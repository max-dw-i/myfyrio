'''Copyright 2019 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Doppelgänger.

Doppelgänger is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Doppelgänger is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Doppelgänger. If not, see <https://www.gnu.org/licenses/>.
'''

import logging
from multiprocessing import Pool
from typing import (Any, Callable, Collection, Dict, Iterable, List, Optional,
                    Set, Tuple)

from PyQt5 import QtCore, QtGui

from doppelganger import core, signals
from doppelganger.exception import InterruptProcessing

SIZE = 200

processing_logger = logging.getLogger('main.processing')

def thumbnail(image: core.Image) -> Optional[QtCore.QByteArray]:
    '''Make thumbnail of :image:

    :param image: image which thumbnail is returned,
    :return: 'QByteArray' object or None if there's any problem
    '''

    try:
        width, height = _scaling_dimensions(image, SIZE)
    except OSError as e:
        processing_logger.error(e)
        return None

    img = _scaled_image(image.path, width, height)

    if img is None:
        return None
    return _QImage_to_QByteArray(img, image.suffix[1:])

def _scaling_dimensions(image: core.Image, biggest_dim: int) -> Tuple[core.Width, core.Height]:
    '''Find the new dimensions of the image (with aspect ratio kept)
    after being scaled

    :param image: image to scale,
    :param biggest_dim: the biggest dimension of the image after
                            being scaled,
    :return: tuple with the image's width and height,
    :raise OSError: any problem while getting the image's dimensions,
    :raise ValuError: new :biggest_dim: is not positive
    '''

    if biggest_dim <= 0:
        raise ValueError('The new size values must be positive')

    try:
        width, height = image.dimensions()
    except OSError:
        raise OSError(f'Cannot get the scaling dimensions of {image.path}')

    if width >= height:
        width, height = (width * biggest_dim // width,
                         height * biggest_dim // width)
    else:
        width, height = (width * biggest_dim // height,
                         height * biggest_dim // height)
    return width, height

def _scaled_image(path: core.ImagePath, width: core.Width,
                  height: core.Height) -> Optional[QtGui.QImage]:
    '''Return the scaled image

    :param path: full path of the image,
    :param width: new width,
    :param height: new height,
    :return: scaled image as 'QImage' object
             or None if something went wrong
    '''

    reader = QtGui.QImageReader(path)
    reader.setDecideFormatFromContent(True)
    reader.setScaledSize(QtCore.QSize(width, height))

    if not reader.canRead():
        processing_logger.error(f'{path} cannot be read')
        return None

    img = reader.read()

    if img.isNull():
        e = reader.errorString()
        processing_logger.error(e)
        return None
    return img

def _QImage_to_QByteArray(image: QtGui.QImage, suffix: str) -> Optional[QtCore.QByteArray]:
    '''Convert 'QImage' object to 'QByteArray' object

    :param image: 'QImage' object,
    :param suffix: suffix of the image (without a dot),
    :return: 'QByteArray' object or None if there's any problem
    '''

    ba = QtCore.QByteArray()
    buf = QtCore.QBuffer(ba)

    if not buf.open(QtCore.QIODevice.WriteOnly):
        processing_logger.error('Something wrong happened while opening buffer')
        return None

    if not image.save(buf, suffix.upper(), 100):
        processing_logger.error('Something wrong happened while saving image into buffer')
        return None

    buf.close()

    return ba


class Worker(QtCore.QRunnable):
    '''QRunnable class reimplementation to handle a separate thread'''

    def __init__(self, func: Callable[..., None], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self) -> None:
        self.func(*self.args, **self.kwargs)


class ImageProcessing:
    '''The whole machinery happenning in a separate thread while
    processing images

    :mw_signals: signals object from the main (GUI) thread,
    :folders: folders to process,
    :sensitivity: maximal difference between hashes of 2 images
                        when they are considered similar;
    '''

    def __init__(self, mw_signals: signals.Signals, folders: Iterable[core.FolderPath],
                 sensitivity: core.Sensitivity) -> None:
        super().__init__()
        self.signals = signals.Signals()
        self.folders = folders
        self.sensitivity = sensitivity

        # If a user's clicked button 'Stop' in the main (GUI) thread,
        # 'interrupt' flag is changed to True
        mw_signals.interrupted.connect(self._is_interrupted)
        self.interrupt = False
        self.errors = False

        self.progress_bar_value: float = 0.0

    def run(self) -> None:
        '''Main processing function'''

        try:
            paths = self.find_images(self.folders)
            cache = self.load_cache()
            cached, not_cached = self.check_cache(paths, cache)

            if not_cached:
                calculated = self.hashes_calculating(not_cached)
                self.caching(calculated, cache)
                cached.extend(calculated)

            image_groups = self.grouping(cached, self.sensitivity)
            image_groups = self.make_thumbnails(image_groups)

            self.signals.result.emit(image_groups)
        except InterruptProcessing:
            processing_logger.info('Image processing has been interrupted by the user')
        except Exception:
            processing_logger.error('Unknown error: ', exc_info=True)
            self.errors = True
        finally:
            self.signals.finished.emit()
            if self.errors:
                self.signals.error.emit('Something went wrong while '
                                        'processing images')

    def find_images(self, folders: Iterable[core.FolderPath]) -> Set[core.ImagePath]:
        try:
            paths = core.find_images(folders)
        except ValueError as e:
            raise ValueError(e)

        self.signals.update_info.emit('loaded_images', str(len(paths)))
        self._update_progress_bar(5)

        return paths

    def load_cache(self) -> Dict[core.ImagePath, core.Hash]:
        try:
            cached_hashes = core.load_cache()
        except EOFError as e:
            processing_logger.error(e)
            cached_hashes = {}

        self._update_progress_bar(10)

        return cached_hashes

    def check_cache(
            self,
            paths: Iterable[core.ImagePath],
            cache: Dict[core.ImagePath, core.Hash]
        ) -> Tuple[List[core.HashedImage], List[core.NoneImage]]:
        cached, not_cached = core.check_cache(paths, cache)

        self.signals.update_info.emit('found_in_cache', str(len(cached)))
        if not_cached:
            self._update_progress_bar(15)
        else:
            self._update_progress_bar(55)

        return cached, not_cached

    def hashes_calculating(self, not_cached: Collection[core.NoneImage]) -> List[core.HashedImage]:
        calculated = self._imap(core.Image.dhash, not_cached, 'remaining_images')

        good = []
        for image in calculated:
            if image.hash is None:
                processing_logger.error(f'Hash of {image.path} cannot be calculated')
                self.errors = True
            else:
                good.append(image)

        return good

    def caching(self, calculated: Iterable[core.HashedImage],
                cache: Dict[core.ImagePath, core.Hash]) -> None:
        core.caching(calculated, cache)

        self._update_progress_bar(55)

    def grouping(self, images: Collection[core.HashedImage],
                 sensitivity: core.Sensitivity) -> List[core.Group]:
        image_groups = core.image_grouping(images, sensitivity)

        self.signals.update_info.emit('image_groups', str(len(image_groups)))
        self.signals.update_info.emit('duplicates', str(sum(len(g) for g in image_groups)))
        self._update_progress_bar(65)

        return image_groups

    def make_thumbnails(self, image_groups: List[core.Group]) -> List[core.Group]:
        '''Make thumbnails of the images

        :param image_groups: groups of duplicate images,
        :return: groups of duplicate images with created thumbnails
        '''

        # 'Flat' list is processed better in parallel
        flat = [image for group in image_groups for image in group]
        thumbnails = self._imap(thumbnail, flat, 'thumbnails')

        # Go through already formed list with groups of duplicate images
        # and assign thumbnails to the corresponding attributes. It's easy
        # because the original image order is preserved in 'flat'
        j = 0
        for group in image_groups:
            for image in group:
                image.thumbnail = thumbnails[j]
                j += 1

        return image_groups

    def _is_interrupted(self) -> None:
        self.interrupt = True

    def _update_progress_bar(self, value: float) -> None:
        '''Emit a new progress bar value

        :param value: new 'progress_bar_value'
        '''

        self.progress_bar_value = value
        self.signals.update_progressbar.emit(self.progress_bar_value)

    def _imap(self, func: Callable[[Any], core.T], collection: Collection[Any],
              label: str) -> List[core.T]:
        '''Reimplementation of 'imap' from multiprocessing lib

        :param func: function to apply to the elements of :collection:,
        :param collection: collection to process in parallel,
        :param label: label to update, one of ('remaining_images', 'thumbnails')
        :return: list of processed elements
        '''

        processed: List[core.T] = []
        num = len(collection)
        self.signals.update_info.emit(label, str(len(collection)))

        try:
            step = 35 / num
        except ZeroDivisionError:
            return processed

        with Pool() as p:
            for i, elem in enumerate(p.imap(func, collection)):
                processed.append(elem)

                self.signals.update_info.emit(label, str(num-i-1))
                self._update_progress_bar(self.progress_bar_value + step)

                if self.interrupt:
                    raise InterruptProcessing
        return processed
