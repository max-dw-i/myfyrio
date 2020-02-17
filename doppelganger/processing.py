'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

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

import pathlib
import sys
from multiprocessing import Pool
from typing import (Any, Callable, Collection, Iterable, List, Optional, Set,
                    Tuple)

from PyQt5 import QtCore, QtGui

from doppelganger import config, core, signals
from doppelganger.exception import InterruptProcessing, ThumbnailError
from doppelganger.logger import Logger

logger = Logger.getLogger('processing')

def thumbnail(image: core.Image, size: int) -> Optional[QtCore.QByteArray]:
    '''Make thumbnail of :image:

    :param image: image whose thumbnail is returned,
    :param size: the biggest dimension of the image after being scaled,
    :return: "QByteArray" object or None if there's any problem
    '''

    try:
        width, height = _scaling_dimensions(image, size)
        qimg = _scaled_image(image.path, width, height)
        ba_img = _QImage_to_QByteArray(qimg, image.suffix[1:].upper())
    except (OSError, ThumbnailError) as e:
        logger.error(e)
        return None

    return ba_img

def _scaling_dimensions(image: core.Image, size: int) -> Tuple[int, int]:
    width, height = image.dimensions()
    biggest_dim = width if width >= height else height
    new_width, new_height = (width * size // biggest_dim,
                             height * size // biggest_dim)
    return new_width, new_height

def _scaled_image(path: core.ImagePath, width: int,
                  height: int) -> QtGui.QImage:
    reader = QtGui.QImageReader(path)
    reader.setDecideFormatFromContent(True)
    reader.setScaledSize(QtCore.QSize(width, height))

    if not reader.canRead():
        raise ThumbnailError(f'{path} cannot be read')

    img = reader.read()

    if img.isNull():
        e = reader.errorString()
        raise ThumbnailError(e)
    return img

def _QImage_to_QByteArray(image: QtGui.QImage, suffix: str) \
    -> Optional[QtCore.QByteArray]:
    ba = QtCore.QByteArray()
    buf = QtCore.QBuffer(ba)

    if not buf.open(QtCore.QIODevice.WriteOnly):
        raise ThumbnailError('Something went wrong while opening buffer')

    if not image.save(buf, suffix, 100):
        raise ThumbnailError('Something went wrong while saving image '
                             'into buffer')

    buf.close()
    return ba

def similarity_rate(image_groups: List[core.Group]):
    '''To compare images, hamming distance between their
    hashes is found (difference). It is easier for a user
    to compare similarities'''

    for group in image_groups:
        for image in group:
            diff = image.difference
            if diff:
                # hash is a 128-bit vector
                image.difference = int((1 - diff / 128) * 100)
                # if difference == 0, then similarity == 100
            else:
                image.difference = 100


class Worker(QtCore.QRunnable):
    '''QRunnable class reimplementation to handle a separate thread'''

    def __init__(self, func: Callable[..., None], *args: Any,
                 **kwargs: Any) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self) -> None:
        self.func(*self.args, **self.kwargs)


class ImageProcessing:
    '''The whole machinery happens in a separate thread while
    processing images

    :param mw_signals: signals object from the main (GUI) thread,
    :param folders: folders to process,
    :param sensitivity: max difference between the hashes of 2 images
                        when they are considered similar,
    :param conf: dict with programme preferences
    '''

    CACHE_FILE = (pathlib.Path(sys.executable).parent
                  if getattr(sys, 'frozen', False)
                  else pathlib.Path(__file__).parents[1]) / 'cache.p'

    def __init__(self, mw_signals: signals.Signals,
                 folders: Iterable[core.FolderPath],
                 sensitivity: core.Sensitivity,
                 conf: config.Conf) -> None:
        self.folders = folders
        self.sensitivity = sensitivity
        self.conf = conf

        # If a user's clicked button 'Stop' in the main (GUI) thread,
        # 'interrupt' flag is changed to True
        mw_signals.interrupted.connect(self._is_interrupted)
        self.signals = signals.Signals()

        self.interrupt = False
        self.errors = False
        self.progress_bar_value: float = 0.0

    def run(self) -> None:
        '''Main processing function'''

        try:
            paths = self._find_images()
            cache = self._load_cache()
            not_cached = self._check_cache(paths, cache)

            if not_cached:
                hashes = self._imap(core.Image.dhash, not_cached,
                                    'remaining_images')
                cache = self._extend_cache(cache, not_cached, hashes)
                core.save_cache(str(self.CACHE_FILE), cache)

            images = [core.Image(path, cache[path])
                      for path in paths if path in cache]
            image_groups = self._image_grouping(images)

            s = core.Sort(image_groups)
            s.sort(self.conf['sort'])

            similarity_rate(image_groups)

            image_groups = self._make_thumbnails(image_groups)

            self.signals.result.emit(image_groups)
        except InterruptProcessing:
            logger.info('Image processing has been interrupted '
                        'by the user')
        except Exception:
            logger.error('Unknown error: ', exc_info=True)
            self.errors = True
        finally:
            self.signals.finished.emit()
            if self.errors:
                self.signals.error.emit('Something went wrong while '
                                        'processing images')

    def _find_images(self) -> Set[core.ImagePath]:
        try:
            paths = core.find_images(self.folders, self.conf['subfolders'])
        except FileNotFoundError as e:
            raise FileNotFoundError(e)

        self.signals.update_info.emit('loaded_images', str(len(paths)))
        self._update_progress_bar(5)

        return paths

    def _load_cache(self) -> core.Cache:
        try:
            cached_hashes = core.load_cache(str(self.CACHE_FILE))
        except EOFError as e:
            cached_hashes = {}
        except OSError as e:
            raise OSError(e)

        self._update_progress_bar(10)

        return cached_hashes

    def _check_cache(self, paths: Collection[core.ImagePath],
                     cache: core.Cache) -> List[core.ImagePath]:
        not_cached = core.check_cache(paths, cache)

        num_of_cached = len(paths) - len(not_cached)
        self.signals.update_info.emit('found_in_cache', str(num_of_cached))
        if not_cached:
            self._update_progress_bar(15)
        else:
            self._update_progress_bar(55)

        return not_cached

    def _extend_cache(self, cache: core.Cache, paths: Iterable[core.ImagePath],
                      hashes: List[Optional[core.Hash]]) -> core.Cache:
        for i, path in enumerate(paths):
            dhash = hashes[i]
            if dhash is None:
                logger.error(f'Hash of {path} cannot be calculated')
                self.errors = True
            else:
                cache[path] = dhash

        self._update_progress_bar(55)

        return cache

    def _image_grouping(self, images: Collection[core.Image]) \
        -> List[core.Group]:
        image_groups = core.image_grouping(images, self.sensitivity)

        self.signals.update_info.emit('image_groups', str(len(image_groups)))
        self.signals.update_info.emit('duplicates',
                                      str(sum(len(g) for g in image_groups)))
        self._update_progress_bar(65)

        return image_groups

    def _make_thumbnails(self, image_groups: List[core.Group]) \
        -> List[core.Group]:
        # 'Flat' list is processed better in parallel
        flat = [(image, self.conf['size'])
                for group in image_groups for image in group]
        thumbnails = self._imap(self._thumbnail_args_unpacker, flat,
                                'thumbnails')

        # Go through already formed list with groups of duplicate images
        # and assign thumbnails to the corresponding attributes. It's easy
        # because the original image order is preserved in 'flat'
        j = 0
        for group in image_groups:
            for image in group:
                image.thumbnail = thumbnails[j]
                j += 1
        return image_groups

    @staticmethod
    def _thumbnail_args_unpacker(image: Tuple[core.Image, int]) \
        -> Optional[QtCore.QByteArray]:
        return thumbnail(image[0], image[1])

    def _is_interrupted(self) -> None:
        self.interrupt = True

    def _update_progress_bar(self, value: float) -> None:
        self.progress_bar_value = value
        self.signals.update_progressbar.emit(self.progress_bar_value)

    def _imap(self, func: Callable[[Any], core.T], collection: Collection[Any],
              label: str) -> List[core.T]:
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
