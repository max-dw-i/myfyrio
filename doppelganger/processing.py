import sys
import traceback
from multiprocessing import Pool

from PyQt5 import QtCore, QtGui

from . import core
from .exception import InterruptProcessing


def thumbnail(image):
    '''Returns an image's thumbnail

    :param image: <class Image> obj,
    :returns: <class QByteArray> obj,
              image's thumbnail
    '''

    reader = QtGui.QImageReader(image.path)
    reader.setDecideFormatFromContent(True)
    if not reader.canRead():
        raise IOError('The image cannot be read')
    width, height = image.get_scaling_dimensions(200)
    reader.setScaledSize(QtCore.QSize(width, height))
    img = reader.read()
    ba = QtCore.QByteArray()
    buf = QtCore.QBuffer(ba)
    buf.open(QtCore.QIODevice.WriteOnly)
    img.save(buf, image.suffix[1:].upper(), 100)
    return ba


class WorkerSignals(QtCore.QObject):
    '''The signals available from running
    ImageProcessingWorker or main (GUI) threads

    Supported signals:
    :interrupt: means the processing should be stopped and
               thread - killed,
    :update_label: label to update: str, text to set: str,
    :error: tuple, (exctype, value, traceback.format_exc()),
    :result: list, group of duplicate images,
    :finished: means the processing is done
    '''

    interrupt = QtCore.pyqtSignal()
    update_label = QtCore.pyqtSignal(str, str)
    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(list)
    finished = QtCore.pyqtSignal()


class ImageProcessingWorker(QtCore.QRunnable):
    '''QRunnable class reimplementation to handle image
    processing thread
    '''

    def __init__(self, main_window, folders):
        super().__init__()
        self.folders = folders

        self.signals = WorkerSignals()
        # If a user's clicked button 'Stop' in the main (GUI) thread,
        # 'interrupt' flag is changed to True
        main_window.signals.interrupt.connect(self._is_interrupted)
        self.interrupt = False

    def _is_interrupted(self):
        self.interrupt = True

    def _paths_processing(self):
        paths = core.get_images_paths(self.folders)
        self.signals.update_label.emit('loaded_images', str(len(paths)))
        return paths

    def _check_cache(self, paths, cached_hashes):
        not_cached_images_paths = core.find_not_cached_images(
            paths,
            cached_hashes
        )
        self.signals.update_label.emit(
            'found_in_cache',
            str(len(paths)-len(not_cached_images_paths))
        )
        self.signals.update_label.emit(
            'remaining_images',
            str(len(not_cached_images_paths))
        )
        return not_cached_images_paths

    def _hashes_calculating(self, not_cached_paths, cached_hashes):
        hashes = []
        with Pool() as p:
            images_num = len(not_cached_paths)
            for i, dhash in enumerate(p.imap(core.Image.calc_dhash, not_cached_paths)):
                if self.interrupt:
                    raise InterruptProcessing
                hashes.append(dhash)
                self.signals.update_label.emit('remaining_images', str(images_num-i-1))
        return hashes

    def _populate_cache(self, paths, hashes, cached_hashes):
        cached_hashes = core.caching_images(
            paths,
            hashes,
            cached_hashes
        )
        return cached_hashes

    def _images_comparing(self, paths, cached_hashes):
        images = core.images_constructor(paths, cached_hashes)
        image_groups = core.images_grouping(images)
        self.signals.update_label.emit('image_groups', str(len(image_groups)))
        return image_groups

    def _making_thumbnails(self, flat):
        thumbnails = []
        thumbnails_left = len(flat)
        with Pool() as p:
            for th in p.imap(thumbnail, flat):
                if self.interrupt:
                    raise InterruptProcessing
                thumbnails.append(th)
                thumbnails_left -= 1
                self.signals.update_label.emit('thumbnails', str(thumbnails_left))
        return thumbnails

    def _thumbnails_processing(self, image_groups):
        flat = [image for group in image_groups for image in group]
        self.signals.update_label.emit('thumbnails', str(len(flat)))

        thumbnails = self._making_thumbnails(flat)

        j = 0
        for group in image_groups:
            for image in group:
                image.thumbnail = thumbnails[j]
                j += 1
            self.signals.result.emit(group)

    @QtCore.pyqtSlot()
    def run(self):
        try:
            paths = self._paths_processing()
            cached_hashes = core.load_cached_hashes()
            not_cached_paths = self._check_cache(paths, cached_hashes)
            if not_cached_paths:
                hashes = self._hashes_calculating(not_cached_paths, cached_hashes)
                cached_hashes = self._populate_cache(not_cached_paths, hashes,
                                                     cached_hashes)
            image_groups = self._images_comparing(paths, cached_hashes)
            self._thumbnails_processing(image_groups)
        except InterruptProcessing:
            self.signals.finished.emit()
            print('Image processing has been interrupted')
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.finished.emit()
