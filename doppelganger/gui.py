'''Graphical user interface is implemented in here'''

from PyQt5.QtCore import QFileInfo, Qt, QThreadPool, pyqtSlot
from PyQt5.QtGui import QColor, QPalette, QPixmap
from PyQt5.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
                             QListWidgetItem, QMainWindow, QTextEdit,
                             QVBoxLayout, QWidget)
from PyQt5.uic import loadUi

from . import processing


UI = r'doppelganger\gui.ui'
IMAGE_ERROR = r'doppelganger\resources\image_error.png'


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
            pixmap = QPixmap(IMAGE_ERROR)
            print(e)
        self.setPixmap(pixmap)


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
        loadUi(UI, self)
        self.signals = processing.WorkerSignals()
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

        worker = processing.ImageProcessingWorker(self, folders)
        worker.signals.update_label.connect(self._update_label_info)
        worker.signals.result.connect(self.render_image_group)
        worker.signals.finished.connect(self.image_processing_finished)
        self.threadpool.start(worker)

    @pyqtSlot()
    def stopBtn_click(self):
        '''Function called on 'Stop' button click event'''

        self.signals.interrupt.emit()
        self.stopBtn.setEnabled(False)
        # Add popup or something about stopping the program

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
