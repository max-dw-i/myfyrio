import sys
import traceback
from multiprocessing import Pool

from PyQt5 import QtCore, QtGui

from . import core
from .exception import InterruptProcessing, ProcessingDone


def thumbnail(image):
    '''Returns an image's thumbnail

    :param image: <class Image> object,
    :returns: <class QByteArray> object or None
              if there's any problem
    '''

    reader = QtGui.QImageReader(image.path)
    reader.setDecideFormatFromContent(True)
    if not reader.canRead():
        print('The image cannot be read')
        return None
    width, height = image.get_scaling_dimensions(200)
    reader.setScaledSize(QtCore.QSize(width, height))

    img = reader.read()
    if img.isNull():
        e = reader.errorString()
        print(e)
        return None
    return _QImage_to_QByteArray(img, image.suffix[1:].upper())

def _QImage_to_QByteArray(image, suffix):
    '''Converts a <class QImage> object to
    a <class QByteArray> object

    :param image: <class QImage> object,
    :returns: <class QByteArray> object
    '''

    ba = QtCore.QByteArray()
    buf = QtCore.QBuffer(ba)
    if not buf.open(QtCore.QIODevice.WriteOnly):
        print('Something wrong happened while opening buffer')
        return None
    if not image.save(buf, suffix, 100):
        print('Something wrong happened while saving image into buffer')
        return None
    buf.close()
    return ba


class Signals(QtCore.QObject):
    '''Supported signals:

    :interrupt: the processing should be stopped and
               the thread - killed,
    :update_info: label to update: str, text to set: str,
    :update_progressbar: int, new progress bar's value,
    :error: tuple, (exctype, value, traceback.format_exc()),
    :result: list, group of duplicate images,
    :finished: the processing is done
    '''

    interrupt = QtCore.pyqtSignal()
    update_info = QtCore.pyqtSignal(str, str)
    update_progressbar = QtCore.pyqtSignal(int)
    error = QtCore.pyqtSignal(tuple)
    result = QtCore.pyqtSignal(list)
    finished = QtCore.pyqtSignal()


class Worker(QtCore.QRunnable):
    '''QRunnable class reimplementation to handle a separate thread
    '''

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self):
        self.func(*self.args, **self.kwargs)


class ImageProcessing:
    '''All the machinery happenning in a separate thread while
    processing images including reporting about the progress

    :param main_window: <class QMainWindow> instance
                        from the main (GUI) thread,
    :param folders: list of str, folders to process
    '''

    def __init__(self, main_window, folders):
        super().__init__()
        self.folders = folders

        self.signals = Signals()
        # If a user's clicked button 'Stop' in the main (GUI) thread,
        # 'interrupt' flag is changed to True
        main_window.signals.interrupt.connect(self._is_interrupted)
        self.interrupt = False

        self.progress_bar_value = 0

    def run(self):
        '''Main processing function'''

        try:
            paths = self._paths_processing()
            cached_hashes = self._load_cached()
            cached, not_cached = self._check_cache(paths, cached_hashes)

            if not_cached:
                calculated = self._imap(core.Image.calc_dhash, not_cached,
                                        'remaining_images')
                self._populate_cache(calculated, cached_hashes)
                cached.extend(calculated)

            image_groups = self._images_comparing(cached, 10)
            self._thumbnails_processing(image_groups)
        except InterruptProcessing:
            print('Image processing has been interrupted by the user')
        except ProcessingDone:
            self.signals.result.emit([])
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()

    def _is_interrupted(self):
        self.interrupt = True

    def _increase_progress_bar_value(self, value):
        self.signals.update_progressbar.emit(self.progress_bar_value + value)
        self.progress_bar_value += value

    def _paths_processing(self):
        paths = core.get_images_paths(self.folders)
        self.signals.update_info.emit('loaded_images', str(len(paths)))
        if len(paths) in (0, 1):
            raise ProcessingDone
        self._increase_progress_bar_value(5)
        return paths

    def _load_cached(self):
        cached_hashes = core.load_cached_hashes()
        self._increase_progress_bar_value(5)
        return cached_hashes

    def _check_cache(self, paths, cached_hashes):
        cached, not_cached = core.check_cache(paths, cached_hashes)
        self.signals.update_info.emit('found_in_cache', str(len(paths)-len(not_cached)))
        self.signals.update_info.emit('remaining_images', str(len(not_cached)))
        self._increase_progress_bar_value(5)
        if not not_cached:
            self._increase_progress_bar_value(40)
        return cached, not_cached

    def _populate_cache(self, hashes, cached_hashes):
        core.caching_images(hashes, cached_hashes)
        self._increase_progress_bar_value(5)

    def _images_comparing(self, paths, sensitivity):
        image_groups = core.images_grouping(paths, sensitivity)
        self.signals.update_info.emit('image_groups', str(len(image_groups)))
        if not image_groups:
            raise ProcessingDone
        self._increase_progress_bar_value(10)
        return image_groups

    def _imap(self, func, collection, label):
        '''Reimplementation of 'imap' from multiprocessing lib

        :param func: function to apply to :collection:,
        :param collection: collection for processing,
        :param label: label to update, one of
                      ('remaining_images', 'thumbnails')
        :returns: list of processed elements
        '''

        processed = []
        num = len(collection)
        step = 35 / num
        with Pool() as p:
            for i, elem in enumerate(p.imap(func, collection)):
                if self.interrupt:
                    raise InterruptProcessing
                processed.append(elem)
                self.signals.update_info.emit(label, str(num-i-1))
                self._increase_progress_bar_value(step)
        return processed

    def _thumbnails_processing(self, image_groups):
        '''Makes thumbnails for the duplicate images

        :param image_groups: list, [[<class Image> obj 1.1,
                                     <class Image> obj 1.2, ...],
                                    [<class Image> obj 2.1,
                                     <class Image> obj 2.2, ...], ...]
        '''

        # 'Flat' list is processed better in parallel
        flat = [image for group in image_groups for image in group]
        self.signals.update_info.emit('thumbnails', str(len(flat)))

        thumbnails = self._imap(thumbnail, flat, 'thumbnails')

        # Go through already formed list with groups
        # of duplicate images and assign thumbnails to
        # the corresponding attributes. It's easy cause
        # the original image order is preserved in 'flat'
        j = 0
        for group in image_groups:
            for image in group:
                image.thumbnail = thumbnails[j]
                j += 1

        self.signals.result.emit(image_groups)
