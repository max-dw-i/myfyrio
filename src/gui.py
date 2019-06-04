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


class ImageProcessingWorkerSignals(QObject):
    '''The signals available from a running
    ImageProcessingWorker thread

    Supported signals:
    :loaded: int, number of images to process,
    :found_in_cache: int, number of images found in cache,
    :remaining: int, number of images left to process,
    :calculated_hashes: int, number of images whose hashes
                        are calculated at the moment,
    :groups: int, number of groups with duplicate images,
    :thumbnails: int, number of thumbnails to get left,
    :error: tuple, (exctype, value, traceback.format_exc()),
    :result: list, group of duplicate images
    '''

    loaded = pyqtSignal(int)
    found_in_cache = pyqtSignal(int)
    remaining = pyqtSignal(int)
    calculated_hashes = pyqtSignal(int)
    groups = pyqtSignal(int)
    thumbnails = pyqtSignal(int)
    error = pyqtSignal(tuple)
    result = pyqtSignal(list)


class ImageProcessingWorker(QRunnable):
    '''QRunnable class reimplementation to handle image
    processing threads
    '''

    def __init__(self, folders):
        super().__init__()
        self.folders = folders

        self.signals = ImageProcessingWorkerSignals()
        self.progress_callback = self.signals.calculated_hashes

    def _paths_processing(self):
        paths = duplicates.get_images_paths(self.folders)
        self.signals.loaded.emit(len(paths))
        return paths

    def _check_cache(self, paths, cached_hashes):
        not_cached_images_paths = duplicates.find_not_cached_images(
            paths,
            cached_hashes
        )
        self.signals.found_in_cache.emit(len(paths)-len(not_cached_images_paths))
        self.signals.remaining.emit(len(not_cached_images_paths))
        return not_cached_images_paths

    def _hashes_calculating(self, not_cached_images_paths, cached_hashes):
        hashes = duplicates.hashes_calculating(
            not_cached_images_paths,
            self.progress_callback
        )
        cached_hashes = duplicates.caching_images(
            not_cached_images_paths,
            hashes,
            cached_hashes
        )
        return cached_hashes

    def _images_comparing(self, paths, cached_hashes):
        images = duplicates.images_constructor(paths, cached_hashes)
        image_groups = duplicates.images_grouping(images)
        self.signals.groups.emit(len(image_groups))
        return image_groups

    def _thumbnails_processing(self, image_groups):
        flat = [image for group in image_groups for image in group]
        thumbnails_left = len(flat)
        self.signals.thumbnails.emit(thumbnails_left)
        with Pool() as p:
            thumbnails = []
            for th in p.imap(ThumbnailWidget.get_thumbnail, flat):
                thumbnails.append(th)
                thumbnails_left -= 1
                self.signals.thumbnails.emit(thumbnails_left)
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
            not_cached_images_paths = self._check_cache(paths, cached_hashes)
            if not_cached_images_paths:
                self._hashes_calculating(not_cached_images_paths, cached_hashes)
            image_groups = self._images_comparing(paths, cached_hashes)
            self._thumbnails_processing(image_groups)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))


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

        if self.selected:
            self.changeBackgroundColor(self.UNSELECTED_BACKGROUND_COLOR)
            self.selected = False
        else:
            self.changeBackgroundColor(self.SELECTED_BACKGROUND_COLOR)
            self.selected = True


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
        found before doing another search
        '''

        group_widgets = self.scrollAreaWidget.findChildren(
            ImageGroupWidget,
            options=Qt.FindDirectChildrenOnly
        )
        for group_widget in group_widgets:
            group_widget.deleteLater()

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

    def _loaded_images_number(self, num):
        self.loadedPicLabel.setText(
            'Loaded pictures ... {}'.format(num)
        )

    def _found_in_cache_images_number(self, num):
        self.foundInCacheLabel.setText(
            'Found pictures in cache ... {}'.format(num)
        )

    def _remaining_images_number(self, num):
        self.remainingPicLabel.setText(
            'Remaining pictures ... {}'.format(num)
        )

    def _image_groups_number(self, num):
        self.dupGroupLabel.setText(
            'Duplicate groups ... {}'.format(num)
        )

    def _thumbnails_number(self, num):
        self.thumbnailsLabel.setText(
            'Thumbnails left ... {}'.format(num)
        )

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
        folders = self.get_user_folders()

        worker = ImageProcessingWorker(folders)
        worker.signals.loaded.connect(self._loaded_images_number)
        worker.signals.found_in_cache.connect(self._found_in_cache_images_number)
        worker.signals.remaining.connect(self._remaining_images_number)
        worker.signals.calculated_hashes.connect(self._remaining_images_number)
        worker.signals.groups.connect(self._image_groups_number)
        worker.signals.thumbnails.connect(self._thumbnails_number)
        worker.signals.result.connect(self.render_image_group)
        self.threadpool.start(worker)

    @pyqtSlot()
    def stopBtn_click(self):
        '''Function called on 'Stop' button click event'''

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
