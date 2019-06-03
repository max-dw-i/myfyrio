'''Graphical user interface is implemented in here'''

import sys
import traceback

from PyQt5.QtCore import (QFileInfo, QObject, QRunnable, QSize, Qt,
                          QThreadPool, pyqtSignal, pyqtSlot)
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
    :error: tuple, (exctype, value, traceback.format_exc()),
    :result: object, final data returned from processing
    '''

    loaded = pyqtSignal(int)
    found_in_cache = pyqtSignal(int)
    remaining = pyqtSignal(int)
    calculated_hashes = pyqtSignal(int)
    groups = pyqtSignal(int)
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class ImageProcessingWorker(QRunnable):
    '''QRunnable class reimplementation to handle image
    processing threads
    '''

    def __init__(self, folders):
        super().__init__()
        self.folders = folders
        self.signals = ImageProcessingWorkerSignals()

        self.progress_callback = self.signals.calculated_hashes

    @pyqtSlot()
    def run(self):
        try:
            paths = duplicates.get_images_paths(self.folders)
            self.signals.loaded.emit(len(paths))

            cached_hashes = duplicates.load_cached_hashes()
            not_cached_images_paths = duplicates.find_not_cached_images(
                paths,
                cached_hashes
            )
            self.signals.found_in_cache.emit(len(paths)-len(not_cached_images_paths))
            self.signals.remaining.emit(len(not_cached_images_paths))

            if not_cached_images_paths:
                hashes = duplicates.hashes_calculating(
                    not_cached_images_paths,
                    self.progress_callback
                )
                cached_hashes = duplicates.caching_images(
                    not_cached_images_paths,
                    hashes,
                    cached_hashes
                )

            images = duplicates.images_constructor(paths, cached_hashes)
            image_groups = duplicates.images_grouping(images)
            self.signals.groups.emit(len(image_groups))
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(image_groups)


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

    def __init__(self, path):
        super().__init__()
        self.setAlignment(Qt.AlignHCenter)
        # Pixmap can read BMP, GIF, JPG, JPEG, PNG, PBM, PGM, PPM, XBM, XPM
        try:
            scaledImage = self.open_image(path)
        except IOError as e:
            scaledImage = self.open_image(r'resources\image_error.png')
            print(e)
        self.setPixmap(scaledImage)

    def open_image(self, path):
        '''Open an image

        :param path: str, full image's path,
        :return: <class QPixmap> obj,
        :raise IOError: if there's any problem with opening
                        and reading an image
        '''

        reader = QImageReader(path)
        reader.setDecideFormatFromContent(True)
        if not reader.canRead():
            raise IOError('The image cannot be read')
        width, height = self._get_scaling_dimensions(reader)
        reader.setScaledSize(QSize(width, height))
        pixmap = QPixmap.fromImageReader(reader)
        if pixmap.isNull():
            e = pixmap.errorString()
            raise IOError(e)
        return pixmap

    def _get_scaling_dimensions(self, reader):
        '''Returns image thumbnail's dimensions

        :param reader: <class QImageReader> object,
        :returns: tuple, (width: int, height: int)
        '''

        size = reader.size()
        width, height = size.width(), size.height()
        if width >= height:
            width, height = (int(width * self.SIZE / width),
                             int(height * self.SIZE / width))
        else:
            width, height = (int(width * self.SIZE / height),
                             int(height * self.SIZE / height))
        return width, height


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

        imageLabel = ThumbnailWidget(image.path)
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

    def render_image_groups(self, image_groups):
        '''Make all the necessary widgets to render duplicate images

        :param image_groups: list, [[<class Image> obj 1.1,
                                     <class Image> obj 1.2, ...],
                                   [<class Image> obj 2.1,
                                    <class Image> obj 2.2, ...], ...]
        '''

        for image_group in image_groups:
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
        worker.signals.result.connect(self.render_image_groups)
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
