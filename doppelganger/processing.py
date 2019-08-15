import logging
import sys
import traceback
from multiprocessing import Pool

from PyQt5 import QtCore, QtGui

from doppelganger import core
from doppelganger.exception import InterruptProcessing

SIZE = 200

processing_logger = logging.getLogger('main.processing')

def thumbnail(image):
    '''Returns an image's thumbnail

    :param image: <class Image> object,
    :returns: <class QByteArray> object or None
              if there's any problem
    '''

    try:
        width, height = image.get_scaling_dimensions(SIZE)
    except OSError as e:
        processing_logger.error(e)
        return None

    img = _scaled_image(image.path, width, height)

    if img is None:
        return None
    return _QImage_to_QByteArray(img, image.suffix[1:])

def _scaled_image(path, width, height):
    '''Returns a scaled image

    :param path: str, full path of an image,
    :param width: int, its new width,
    :param height: int, its new height,
    :returns: <class QImage> object or None if
              something went wrong
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

def _QImage_to_QByteArray(image, suffix):
    '''Converts a <class QImage> object to
    a <class QByteArray> object

    :param image: <class QImage> object,
    :param suffix: str, suffix of the image (without a dot),
    :returns: <class QByteArray> object or None
              if there's any problem
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

    def __init__(self, main_window, folders, sensitivity):
        super().__init__()
        self.folders = folders
        self.sensitivity = sensitivity

        self.signals = Signals()
        # If a user's clicked button 'Stop' in the main (GUI) thread,
        # 'interrupt' flag is changed to True
        main_window.signals.interrupt.connect(self._is_interrupted)
        self.interrupt = False

        self.progress_bar_value = 0

    def run(self):
        '''Main processing function'''

        try:
            paths = self.paths(self.folders)
            cache = self.load_cache()
            cached, not_cached = self.check_cache(paths, cache)

            if not_cached:
                calculated = self.calculating(not_cached)
                self.caching(calculated, cache)
                cached.extend(calculated)

            image_groups = self.grouping(cached, self.sensitivity)
            image_groups = self.thumbnails_generating(image_groups)

            self.signals.result.emit(image_groups)
        except InterruptProcessing:
            processing_logger.info('Image processing has been interrupted by the user')
        except Exception:
            processing_logger.error('Unknown error: ', exc_info=True)
        finally:
            self.signals.finished.emit()

    def paths(self, folders):
        paths = core.get_images_paths(folders)

        self.signals.update_info.emit('loaded_images', str(len(paths)))
        self._update_progress_bar(5)

        return paths

    def load_cache(self):
        try:
            cached_hashes = core.load_cached_hashes()
        except EOFError as e:
            print(e)
            cached_hashes = {}

        self._update_progress_bar(10)

        return cached_hashes

    def check_cache(self, paths, cache):
        cached, not_cached = core.check_cache(paths, cache)

        self.signals.update_info.emit('found_in_cache', str(len(cached)))
        if not_cached:
            self._update_progress_bar(15)
        else:
            self._update_progress_bar(55)

        return cached, not_cached

    def calculating(self, not_cached):
        calculated = self._imap(core.Image.calc_dhash, not_cached, 'remaining_images')

        good = []
        for image in calculated:
            if image.hash is None:
                processing_logger.error(f'Hash of {image.path} cannot be calculated')
            else:
                good.append(image)

        return good

    def caching(self, calculated, cache):
        core.caching_images(calculated, cache)

        self._update_progress_bar(55)

    def grouping(self, cached, sensitivity):
        image_groups = core.images_grouping(cached, sensitivity)

        self.signals.update_info.emit('image_groups', str(len(image_groups)))
        self._update_progress_bar(65)

        return image_groups

    def thumbnails_generating(self, image_groups):
        '''Makes thumbnails for the duplicate images

        :param image_groups: list, [[<class Image> obj 1.1,
                                     <class Image> obj 1.2, ...],
                                    [<class Image> obj 2.1,
                                     <class Image> obj 2.2, ...], ...]
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

    def _is_interrupted(self):
        self.interrupt = True

    def _update_progress_bar(self, value):
        '''Emit a new progress bar value

        :param value: int, new 'progress_bar_value'
        '''

        self.progress_bar_value = value
        self.signals.update_progressbar.emit(self.progress_bar_value)

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
