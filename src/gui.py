'''Graphical user interface is implemented in here'''

import os

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidgetItem, QMainWindow,
    QSizePolicy, QVBoxLayout, QWidget)
from PyQt5.uic import loadUi

from . import duplicates


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


class ImagePathLabel(InfoLabelWidget):
    '''Label class to show the path to an image'''

    def __init__(self, text):
        super().__init__(text)
        self.setWordWrap(True)


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
        image = self.open_image(path)
        scaledImage = image.scaled(self.SIZE, self.SIZE, Qt.KeepAspectRatio)
        self.setPixmap(scaledImage)

    def open_image(self, path):
        '''Open an image

        :param path: str, full image's path,
        :returns: <class QPixmap> obj
        '''

        # Sometimes image's format != the one's path extension so when
        # the app try to open it automatically, we get 'Null'. If it's
        # the case, try to open it with the 'specific format' setting
        image = QPixmap(path)
        if not image.isNull():
            return image

        for ext in ('PNG', 'JPG', 'JPEG', 'BMP'):
            image = QPixmap(path, ext)
            if not image.isNull():
                return image

        return QPixmap(os.path.abspath(r'resources\image_error.png'))


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

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)

        imageLabel = ThumbnailWidget(image.path)
        layout.addWidget(imageLabel)

        imageInfo = ImageInfoWidget(image.path, image.difference,
                                    image.dimensions, image.filesize)
        layout.addWidget(imageInfo)

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

        self.image.delete_image()
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
        layout.setAlignment(Qt.AlignLeft)
        for image in image_group:
            thumbnail = DuplicateCandidateWidget(image)
            layout.addWidget(thumbnail)

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

        group_widgets = self.scrollAreaWidget.findChildren(
            ImageGroupWidget,
            options=Qt.FindDirectChildrenOnly
        )
        for group_widget in group_widgets:
            group_widget.deleteLater()

        paths = [self.pathLW.item(i).data(Qt.DisplayRole) for i in range(self.pathLW.count())]
        image_groups = duplicates.image_processing(paths)
        for image_group in image_groups:
            self.scrollAreaLayout.addWidget(ImageGroupWidget(image_group))

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
