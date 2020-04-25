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

from PyQt5 import QtCore

from doppelganger import config, core, signals
from doppelganger.exception import InterruptProcessing
from doppelganger.logger import Logger
from doppelganger.cache import Cache

logger = Logger.getLogger('processing')


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

        mw_signals.interrupted.connect(self._is_interrupted)
        self.signals = signals.Signals()

        # If a user's clicked button 'Stop' in the main (GUI) thread,
        # 'interrupt' flag is changed to True
        self.interrupt = False
        self.errors = False
        self.progress_bar_value: float = 0.0

    def run(self) -> None:
        '''Main processing function'''

        try:
            images = self._find_images()
            cache = self._load_cache()
            cached, not_cached = self._check_cache(images, cache)

            if not_cached:
                calculated = self._calculate_hashes(not_cached)
                cache = self._update_cache(cache, calculated)
                cache.save(str(self.CACHE_FILE))
                cached.extend(calculated)

            image_groups = self._image_grouping(cached)

            sort_type = self.conf['sort']
            for group in image_groups:
                s = core.Sort(group)
                s.sort(sort_type)

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

    def _find_images(self) -> Set[core.Image]:
        filter_imgs = self.conf['filter_img_size']
        min_w, max_w = self.conf['min_width'], self.conf['max_width']
        min_h, max_h = self.conf['min_height'], self.conf['max_height']

        images = set()
        img_gen = core.find_image(self.folders, self.conf['subfolders'])
        for img in img_gen:
            if self.interrupt:
                raise InterruptProcessing

            if not filter_imgs or (min_w <= img.width <= max_w
                                   and min_h <= img.height <= max_h):
                images.add(img)
                # Slower than showing the result number
                # but show progress (better UX)
                self.signals.update_info.emit('loaded_images',
                                              str(len(images)))

        self._update_progress_bar(5)

        return images

    def _load_cache(self) -> Cache:
        try:
            cache = Cache()
            cache.load(str(self.CACHE_FILE))
        except (EOFError, FileNotFoundError) as e:
            pass
        except OSError as e:
            raise OSError(e)

        self._update_progress_bar(10)

        return cache

    def _check_cache(self, images: Collection[core.Image], cache: Cache) \
        -> Tuple[List[core.Image], List[core.Image]]:
        cached = []
        not_cached = []

        for img in images:
            dhash = cache.get(img.path, None)
            if dhash is None:
                not_cached.append(img)
            else:
                img.dhash = dhash
                cached.append(img)

        self.signals.update_info.emit('found_in_cache', str(len(cached)))
        if not_cached:
            self._update_progress_bar(15)
        else:
            self._update_progress_bar(55)

        return cached, not_cached

    def _update_cache(self, cache: Cache, images: Iterable[core.Image]) \
        -> Cache:
        for img in images:
            dhash = img.dhash
            img_path = img.path
            if dhash == -1:
                logger.error(f'Hash of {img_path} cannot be calculated')
                self.errors = True
            else:
                cache[img_path] = dhash

        self._update_progress_bar(55)

        return cache

    def _calculate_hashes(self, images: Collection[core.Image]) \
        -> List[core.Image]:
        hashed_images: List[core.Image] = []

        if not images:
            return hashed_images

        progress_step = 35 / len(images)

        with Pool() as p:
            img_gen = p.imap(core.Image.dhash_parallel, images)
            for i, img in enumerate(img_gen):
                if self.interrupt:
                    raise InterruptProcessing

                hashed_images.append(img)

                self.signals.update_info.emit('remaining_images', str(i+1))
                self._update_progress_bar(self.progress_bar_value
                                          + progress_step)

        return hashed_images

    def _image_grouping(self, images: Collection[core.Image]) \
        -> List[core.Group]:
        grouping_gen = core.image_grouping(images, self.sensitivity)

        image_groups = []
        for image_groups in grouping_gen:
            if self.interrupt:
                raise InterruptProcessing

            # Slower than showing only the result number of the found
            # duplicate images but show progress
            duplicates_found = str(sum(len(g) for g in image_groups))
            self.signals.update_info.emit('duplicates', duplicates_found)

        self.signals.update_info.emit('image_groups', str(len(image_groups)))
        self._update_progress_bar(65)

        return image_groups

    def _make_thumbnails(self, image_groups: List[core.Group]) \
        -> List[core.Group]:
        thumbnails: List[Optional[QtCore.QByteArray]] = []
        if not image_groups:
            return thumbnails

        # 'Flat' list is processed better in parallel
        flat = [(image, self.conf['size'])
                for group in image_groups for image in group]

        progress_step = 35 / len(flat)

        with Pool() as p:
            thumbnails_gen = p.imap(self._thumbnail_args_unpacker, flat)
            for i, th in enumerate(thumbnails_gen):
                if self.interrupt:
                    raise InterruptProcessing

                thumbnails.append(th)

                self.signals.update_info.emit('thumbnails', str(i + 1))
                self._update_progress_bar(self.progress_bar_value
                                          + progress_step)

        for (image, _), th in zip(flat, thumbnails):
            image.thumb = th

        return image_groups

    @staticmethod
    def _thumbnail_args_unpacker(thumbnail_args: Tuple[core.Image, int]) \
        -> QtCore.QByteArray:
        image, size = thumbnail_args[0], thumbnail_args[1]

        try:
            th = image.thumbnail(size)
        except OSError as e:
            logger.error(e)
            th = None

        return th

    def _is_interrupted(self) -> None:
        self.interrupt = True

    def _update_progress_bar(self, value: float) -> None:
        self.progress_bar_value = value
        self.signals.update_progressbar.emit(self.progress_bar_value)
