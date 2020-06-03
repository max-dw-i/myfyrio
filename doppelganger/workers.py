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

-------------------------------------------------------------------------------

Module implementing working with worker threads
'''

from __future__ import annotations

import os
from multiprocessing import Pool
from typing import Any, Callable, Collection, Iterable, List, Set, Tuple, Union

from PyQt5 import QtCore, QtGui

from doppelganger import core, resources
from doppelganger.cache import Cache
from doppelganger.config import Config
from doppelganger.gui import imageviewwidget
from doppelganger.logger import Logger

logger = Logger.getLogger('workers')


class Worker(QtCore.QRunnable):
    '''QRunnable class reimplementation to handle a worker thread.
    Pass any function you want to run in a worker thread with
    an arbitrary number of arguments to the constructor

    E.g. "Worker(print, 'Run', 'thread', sep='WORKER')" runs
    the function "print" with the arguments "Run", "thread",
    "sep='WORKER'" which prints the string "RunWORKERthread"
    '''

    def __init__(self, func: Callable[..., None], *args: Any,
                 **kwargs: Any) -> None:
        super().__init__()

        self._func = func
        self._args = args
        self._kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self) -> None:
        self._func(*self._args, **self._kwargs)


class ImageProcessing(QtCore.QObject):
    '''Function "run" implements all the stages of image processing:
    finds images in the :folders:, loads the cache file, checks the cache
    and finds the images with no calculated hashes, runs hash calculation
    for these images and groups all the similar images

    :param folders:             folders to search for images in,
    :param sensitivity:         images are considered similar if the difference
                                between their hashes is at most this value,
    :param conf:                "Config" object with the programme's settings,

    :signal images_loaded:      number of the found in the :folders:
                                images: int, emitted when a new image is found,
    :signal found_in_cache:     number of the found in the cache images: int,
                                emitted when the whole cache is checked,
    :signal hashes_calculated:  number of new calculatedhashes: int,
                                emitted when a new hash is calculated,
    :signal duplicates_found:   number of found duplicate images: int,
                                emitted when a new image is found,
    :signal groups_found:       number of found duplicate image groups: int,
                                emitted when a new group is found,
    :signal update_progressbar: new progress bar value: int,
    :signal finished:           list of duplicate image groups: List[Group],
    :signal interrupted:        image processing has been interrupted
                                by the user,
    :signal error:              error text: str
    '''

    images_loaded = QtCore.pyqtSignal(int)
    found_in_cache = QtCore.pyqtSignal(int)
    hashes_calculated = QtCore.pyqtSignal(int)
    duplicates_found = QtCore.pyqtSignal(int)
    groups_found = QtCore.pyqtSignal(int)

    update_progressbar = QtCore.pyqtSignal(float)
    finished = QtCore.pyqtSignal(list)
    interrupted = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, folders: Iterable[core.FolderPath],
                 conf: Config) -> None:
        super().__init__(parent=None)

        self._folders = folders
        self._conf = conf

        self._interrupted = False
        self._error = False
        self._progressbar_value: float = 0.0

    def run(self) -> None:
        try:
            images = self._find_images()
            if not images:
                return

            cache = self._load_cache()
            cached, not_cached = self._check_cache(images, cache)

            if not_cached:
                calculated = self._calculate_hashes(not_cached)
                self._update_cache(cache, calculated)
                if self._interrupted:
                    self.interrupted.emit()
                    return
                cached.extend(calculated)

            self._image_grouping(cached)

        except Exception:
            logger.error('Unknown error: ', exc_info=True)
            self._error = True

        finally:
            if self._error:
                self.error.emit('Something went wrong while processing images')

    def interrupt(self) -> None:
        self._interrupted = True

    def _find_images(self) -> Set[core.Image]:
        filter_size = self._conf['filter_img_size']
        min_w, max_w = self._conf['min_width'], self._conf['max_width']
        min_h, max_h = self._conf['min_height'], self._conf['max_height']

        images = set()
        gen = core.find_image(self._folders, self._conf['subfolders'])
        for img in gen:
            if self._interrupted:
                self.interrupted.emit()
                return set()

            if not filter_size or (min_w <= img.width <= max_w
                                   and min_h <= img.height <= max_h):
                images.add(img)
                # Slower than showing the result number
                self.images_loaded.emit(len(images))

        if not images:
            self.finished.emit([])

        return images

    def _load_cache(self) -> Cache:
        try:
            c = Cache()
            c.load(resources.Cache.CACHE.abs_path) # pylint: disable=no-member
        except FileNotFoundError:
            # Make an empty cache (it's empty by default) since there's no one
            pass
        except EOFError:
            logger.error('Cache file is corrupted and will be rewritten')
            self._error = True

        return c

    def _check_cache(self, images: Collection[core.Image], cache: Cache) \
        -> Tuple[List[core.Image], List[core.Image]]:
        cached, not_cached = [], []

        for img in images:
            dhash = cache.get(img.path, None)
            if dhash is None:
                not_cached.append(img)
            else:
                img.dhash = dhash
                cached.append(img)

        self.found_in_cache.emit(len(cached))
        if not_cached:
            self._update_progressbar(5)
        else:
            self._update_progressbar(35)

        return cached, not_cached

    def _calculate_hashes(self, images: Collection[core.Image]) \
        -> List[core.Image]:
        calculated: List[core.Image] = []
        progress_step = 30 / len(images)

        with Pool(processes=self._available_cores()) as p:
            gen = p.imap(core.Image.dhash_parallel, images)
            for i, img in enumerate(gen):
                if self._interrupted:
                    return calculated

                calculated.append(img)

                self.hashes_calculated.emit(i+1)
                new_val = self._progressbar_value + progress_step
                self._update_progressbar(new_val)

        self._update_progressbar(35)

        return calculated

    def _update_cache(self, cache: Cache, images: Iterable[core.Image]) \
        -> None:
        for img in images:
            dhash = img.dhash
            path = img.path
            if dhash == -1:
                logger.error(f'Hash of {path} cannot be calculated')
                self._error = True
            else:
                cache[path] = dhash

        try:
            cache.save(resources.Cache.CACHE.abs_path) # pylint: disable=no-member
        except OSError:
            logger.error('Cache cannot be saved on the disk')
            self._error = True

        self._update_progressbar(40)

    def _image_grouping(self, images: Collection[core.Image]) -> None:
        image_groups = []
        progress_step = 30 / len(images)

        gen = core.image_grouping(images, self._conf['sensitivity'])
        for image_groups in gen:
            if self._interrupted:
                self.interrupted.emit()
                return

            # Slower than showing the result number
            duplicates_found = sum(len(g) for g in image_groups)
            self.duplicates_found.emit(duplicates_found)
            self.groups_found.emit(len(image_groups))
            new_val = self._progressbar_value + progress_step
            self._update_progressbar(new_val)

        self._update_progressbar(70)

        self.finished.emit(image_groups)

    def _available_cores(self) -> int:
        cores = self._conf['cores']
        available_cores = len(os.sched_getaffinity(0))
        if cores > available_cores:
            cores = available_cores
        return cores

    def _update_progressbar(self, value: float) -> None:
        old_val = self._progressbar_value
        self._progressbar_value = value
        emit_val = int(value)
        if emit_val > old_val:
            self.update_progressbar.emit(emit_val)


class ThumbnailProcessing(QtCore.QObject):
    '''Function "run" implements thumbnail making

    :param image:       "Image" object to make a thumbnail for,
    :param size:        the biggest dimension (width or height) of
                        the image after having been scaled,
    :param widget:      "ThumbnailWidget" object (optional) is used
                        in "lazy" mode (when the thumbnails are not
                        made all at once),

    :signal finished:   image thumbnail is made and assigned to
                        the attribute "thumb" of the "Image" object
    '''

    finished = QtCore.pyqtSignal()

    def __init__(self, image: core.Image, size: Union[core.Width, core.Height],
                 widget: imageviewwidget.ThumbnailWidget = None) -> None:
        super().__init__(parent=None)

        self._image = image
        self._size = size
        self._widget = widget

    def run(self) -> None:
        # If 'lazy' mode and the widget is not visible,
        # there's no point in making the thumbnail
        if self._widget is None or self._widget.isVisible():
            try:
                self._image.thumbnail(self._size)
            except OSError as e:
                logger.error(e)
                self._image.thumb = QtGui.QImage()

            self.finished.emit()
