'''Graphical user interface is implemented in here'''

import sys
import traceback
from multiprocessing import Pool

from PyQt5.QtCore import (QBuffer, QByteArray, QFileInfo, QIODevice, QObject,
                          QRunnable, QSize, Qt, QThreadPool, pyqtSignal,
                          pyqtSlot)
from PyQt5.QtGui import QColor, QImageReader, QPalette, QPixmap
from PyQt5.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
                             QListWidgetItem, QMainWindow, QTextEdit,
                             QVBoxLayout, QWidget)
from PyQt5.uic import loadUi

from . import duplicates
from .exceptions import InterruptProcessing


class WorkerSignals(QObject):
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

    interrupt = pyqtSignal()
    update_label = pyqtSignal(str, str)
    error = pyqtSignal(tuple)
    result = pyqtSignal(list)
    finished = pyqtSignal()


class ImageProcessingWorker(QRunnable):
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
        paths = duplicates.get_images_paths(self.folders)
        self.signals.update_label.emit('loaded_images', str(len(paths)))
        return paths

    def _check_cache(self, paths, cached_hashes):
        not_cached_images_paths = duplicates.find_not_cached_images(
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
            for i, dhash in enumerate(p.imap(duplicates.Image.calc_dhash, not_cached_paths)):
                if self.interrupt:
                    raise InterruptProcessing
                hashes.append(dhash)
                self.signals.update_label.emit('remaining_images', str(images_num-i-1))
        return hashes

    def _populate_cache(self, paths, hashes, cached_hashes):
        cached_hashes = duplicates.caching_images(
            paths,
            hashes,
            cached_hashes
        )
        return cached_hashes

    def _images_comparing(self, paths, cached_hashes):
        images = duplicates.images_constructor(paths, cached_hashes)
        image_groups = duplicates.images_grouping(images)
        self.signals.update_label.emit('image_groups', str(len(image_groups)))
        return image_groups

    def _making_thumbnails(self, flat):
        thumbnails = []
        thumbnails_left = len(flat)
        with Pool() as p:
            for th in p.imap(ThumbnailWidget.get_thumbnail, flat):
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

    @pyqtSlot()
    def run(self):
        try:
            paths = self._paths_processing()
            cached_hashes = duplicates.load_cached_hashes()
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


class InfoLabelWidget(QLabel):
    '''Abstract Label class'''

    def __init__(self, text):
        super().__init__()
        self.setAlignment(Qt.AlignHCenter)
        self.setText(text)


class SimilarityLabel(InfoLabelWidget):
    '''Label class to show info about images similarity'''


class ImageSizeLabel(InfoLabelWidget):
    '''Label class to show info about the image size'''


class ImagePathLabel(QTextEdit):
    '''TextEdit class to show the path to an image'''

    def __init__(self, text):
        super().__init__()
        self.setReadOnly(True)
        self.setFrameStyle(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pal = QPalette()
        pal.setColor(QPalette.Base, Qt.transparent)
        self.setPalette(pal)

        self.setText(QFileInfo(text).canonicalFilePath())
        self.setAlignment(Qt.AlignCenter)


class ImageInfoWidget(QWidget):
    '''Label class to show info about an image (its similarity
    rate, size and path)'''

    def __init__(self, path, difference, dimensions, filesize):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignBottom)

        widgets = (
            SimilarityLabel(str(difference)),
            ImageSizeLabel(self.get_image_size(dimensions, filesize)),
            ImagePathLabel(path)
        )
        for widget in widgets:
            layout.addWidget(widget)
        self.setLayout(layout)

    def get_image_size(self, dimensions, filesize):
        '''Return info about image dimensions and file size

        :param dimensions: tuple, (width: int, height: int),
        :param filesize: float, file size in bytes, kilobytes or megabytes,
                                rounded to the first decimal place,
        :returns: str, string with format '{width}x{height}, {file_size} {units}'
        '''

        units = 'KB'
        image_params = {'width': dimensions[0], 'height': dimensions[1],
                        'filesize': filesize, 'units': units}
        return '{width}x{height}, {filesize} {units}'.format(**image_params)


class ThumbnailWidget(QLabel):
    '''Label class to render image thumbnail'''

    SIZE = 200

    def __init__(self, image):
        super().__init__()
        self.setAlignment(Qt.AlignHCenter)
        # Pixmap can read BMP, GIF, JPG, JPEG, PNG, PBM, PGM, PPM, XBM, XPM
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(image.thumbnail)
            if pixmap.isNull():
                e = pixmap.errorString()
                raise IOError(e)
        except IOError as e:
            pixmap = QPixmap(r'resources\image_error.png')
            print(e)
        self.setPixmap(pixmap)

    @staticmethod
    def get_thumbnail(image):
        '''Returns an image's thumbnail

        :param image: <class Image> obj,
        :returns: <class QByteArray> obj,
                  image's thumbnail
        '''

        reader = QImageReader(image.path)
        reader.setDecideFormatFromContent(True)
        if not reader.canRead():
            raise IOError('The image cannot be read')
        width, height = image.get_scaling_dimensions(200)
        reader.setScaledSize(QSize(width, height))
        img = reader.read()
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.WriteOnly)
        img.save(buf, image.suffix[1:].upper(), 100)
        return ba


class DuplicateCandidateWidget(QWidget):
    '''Widget class to render a duplicate candidate image and
    all the info about it (its similarityrate, size and path)
    '''

    def __init__(self, image):
        super().__init__()
        self.image = image
        self.UNSELECTED_BACKGROUND_COLOR = self.getBackgroundColor()
        self.SELECTED_BACKGROUND_COLOR = '#d3d3d3'
        self.selected = False

        self.setFixedWidth(200)
        layout = QVBoxLayout(self)

        imageLabel = ThumbnailWidget(image)
        layout.addWidget(imageLabel)

        try:
            dimensions = image.get_dimensions()
            filesize = image.get_filesize()
        except OSError:
            dimensions = (-1, -1)
            filesize = 0
        except ValueError:
            filesize = image.get_filesize()
        imageInfo = ImageInfoWidget(image.path, image.difference,
                                    dimensions, filesize)
        layout.addWidget(imageInfo)
        self.setLayout(layout)

        self.setAutoFillBackground(True)
        self.setWidgetEvents()

    def setWidgetEvents(self):
        '''Link events and functions called on the events'''

        self.mouseReleaseEvent = self.mouseRelease

    def changeBackgroundColor(self, color):
        '''Change DuplicateCandidateWidget background color

        :color: str, hex format '#ffffff'
        '''

        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(color))
        self.setPalette(palette)

    def getBackgroundColor(self):
        '''Return DuplicateCandidateWidget background color

        :returns: str, hex format '#ffffff'
        '''

        return self.palette().color(QPalette.Background).name()

    def delete(self):
        '''Delete an image from disk and its DuplicateCandidateWidget
        instance
        '''

        try:
            self.image.delete_image()
        except OSError:
            pass # Add pop-up or something else
        else:
            self.deleteLater()

    def mouseRelease(self, event):
        '''Function called on mouse release event'''

        window = self.window()

        if self.selected:
            self.changeBackgroundColor(self.UNSELECTED_BACKGROUND_COLOR)
            self.selected = False
            if not window.has_selected_widgets():
                window.deleteBtn.setEnabled(False)
        else:
            self.changeBackgroundColor(self.SELECTED_BACKGROUND_COLOR)
            self.selected = True
            window.deleteBtn.setEnabled(True)


class ImageGroupWidget(QWidget):
    '''Widget class to keep similar images together'''

    def __init__(self, image_group):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        for image in image_group:
            thumbnail = DuplicateCandidateWidget(image)
            layout.addWidget(thumbnail)
        self.setLayout(layout)

    def getSelectedWidgets(self):
        '''Return list of the selected DuplicateCandidateWidget instances'''

        widgets = self.findChildren(
            DuplicateCandidateWidget,
            options=Qt.FindDirectChildrenOnly
        )
        return [widget for widget in widgets if widget.selected]


class App(QMainWindow):
    '''Main GUI class'''

    def __init__(self):
        super().__init__()
        loadUi(r'src\gui.ui', self)
        self.signals = WorkerSignals()
        self.setWidgetEvents()
        self.show()

        self.threadpool = QThreadPool()

    def setWidgetEvents(self):
        '''Link events and functions called on the events'''

        self.addFolderBtn.clicked.connect(self.addFolderBtn_click)
        self.delFolderBtn.clicked.connect(self.delFolderBtn_click)
        self.startBtn.clicked.connect(self.startBtn_click)
        self.stopBtn.clicked.connect(self.stopBtn_click)
        self.pauseBtn.clicked.connect(self.pauseBtn_click)
        self.moveBtn.clicked.connect(self.moveBtn_click)
        self.deleteBtn.clicked.connect(self.deleteBtn_click)

    def openFolderNameDialog(self):
        '''Open file dialog and return the folder full path'''

        folder_path = QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QFileDialog.ShowDirsOnly
        )
        return folder_path

    def clear_form_before_start(self):
        '''Clear the form from the previous duplicate images
        found and labels before doing another search
        '''

        group_widgets = self.scrollAreaWidget.findChildren(
            ImageGroupWidget,
            options=Qt.FindDirectChildrenOnly
        )
        for group_widget in group_widgets:
            group_widget.deleteLater()

        for label in ['thumbnails', 'image_groups', 'remaining_images',
                      'found_in_cache', 'loaded_images']:
            self._update_label_info(label, str(0))

    def get_user_folders(self):
        '''Get all the folders a user added to the 'pathLW'

        :returns: list of str, the folders the user wants to
                  process
        '''

        return [self.pathLW.item(i).data(Qt.DisplayRole)
                for i in range(self.pathLW.count())]

    def render_image_group(self, image_group):
        '''Render ImageGroupWidget with duplicate images

        :param image_groups: list, [<class Image> obj 1.1, ...]
        '''

        self.scrollAreaLayout.addWidget(ImageGroupWidget(image_group))

    def _update_label_info(self, label, text):
        '''Update a label's info

        :param label: str, one of ('thumbnails', 'image_groups',
                           'remaining_images', 'found_in_cache',
                           'loaded_images'),
        :param text: str, text to add to a label
        '''

        labels = {'thumbnails': self.thumbnailsLabel,
                  'image_groups': self.dupGroupLabel,
                  'remaining_images': self.remainingPicLabel,
                  'found_in_cache': self.foundInCacheLabel,
                  'loaded_images': self.loadedPicLabel}

        label_to_change = labels[label]
        label_text = label_to_change.text().split(' ')
        label_text[-1] = text
        label_to_change.setText(' '.join(label_text))

    def has_selected_widgets(self):
        '''Checks if there are selected DuplicateCandidateWidget
        in the form

        :returns: bool, True if there are any
        '''

        group_widgets = self.scrollAreaWidget.findChildren(
            ImageGroupWidget,
            options=Qt.FindDirectChildrenOnly
        )
        for group_widget in group_widgets:
            selected_widgets = group_widget.getSelectedWidgets()
            if selected_widgets:
                self.deleteBtn.setEnabled(True)
                return True
        return False

    def image_processing_finished(self):
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)

    @pyqtSlot()
    def addFolderBtn_click(self):
        '''Function called on 'Add Path' button click event'''

        folder_path = self.openFolderNameDialog()
        folder_path_item = QListWidgetItem()
        folder_path_item.setData(Qt.DisplayRole, folder_path)
        self.pathLW.addItem(folder_path_item)
        self.delFolderBtn.setEnabled(True)

    @pyqtSlot()
    def delFolderBtn_click(self):
        '''Function called on 'Delete Path' button click event'''

        item_list = self.pathLW.selectedItems()
        for item in item_list:
            self.pathLW.takeItem(self.pathLW.row(item))

        if not self.pathLW.count():
            self.delFolderBtn.setEnabled(False)

    @pyqtSlot()
    def startBtn_click(self):
        '''Function called on 'Start' button click event'''

        self.clear_form_before_start()
        self.stopBtn.setEnabled(True)
        self.startBtn.setEnabled(False)
        folders = self.get_user_folders()

        worker = ImageProcessingWorker(self, folders)
        worker.signals.update_label.connect(self._update_label_info)
        worker.signals.result.connect(self.render_image_group)
        worker.signals.finished.connect(self.image_processing_finished)
        self.threadpool.start(worker)

    @pyqtSlot()
    def stopBtn_click(self):
        '''Function called on 'Stop' button click event'''

        self.signals.interrupt.emit()
        self.stopBtn.setEnabled(False)
        # TODO Add popup or something about stopping the program

    @pyqtSlot()
    def pauseBtn_click(self):
        '''Function called on 'Pause' button click event'''

    @pyqtSlot()
    def moveBtn_click(self):
        '''Function called on 'Move' button click event'''

    @pyqtSlot()
    def deleteBtn_click(self):
        '''Function called on 'Delete' button click event'''

        group_widgets = self.scrollAreaWidget.findChildren(
            ImageGroupWidget,
            options=Qt.FindDirectChildrenOnly
        )
        for group_widget in group_widgets:
            duplicate_candidate_widgets_num = len(group_widget.findChildren(
                DuplicateCandidateWidget,
                options=Qt.FindDirectChildrenOnly
            ))
            selected_widgets = group_widget.getSelectedWidgets()
            for selected_widget in selected_widgets:
                selected_widget.delete()
            if len(selected_widgets) == duplicate_candidate_widgets_num:
                group_widget.deleteLater()

        self.deleteBtn.setEnabled(False)
