from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidgetItem, QMainWindow,
    QVBoxLayout, QWidget)
from PyQt5.uic import loadUi

from . import duplicates, utils


class InfoLabelWidget(QLabel):
    def __init__(self, text):
        super().__init__()
        self.setAlignment(Qt.AlignHCenter)
        self.setText(text)


class ImageInfoWidget(QWidget):
    def __init__(self, image_path, similarity):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignBottom)

        image_size = utils.get_image_size(image_path)
        image_weight = utils.get_image_weight(image_path, 'KB')
        image_size = '{}x{}, {} KB'.format(image_size[0], image_size[1], image_weight)

        for text in [str(similarity), image_size, image_path]:
            label = InfoLabelWidget(text)
            layout.addWidget(label)

        label.setWordWrap(True)


class ThumbnailWidget(QLabel):
    SIZE = 200

    def __init__(self, image_path):
        super().__init__()
        self.setAlignment(Qt.AlignHCenter)
        # Pixmap can read BMP, GIF, JPG, JPEG, PNG, PBM, PGM, PPM, XBM, XPM
        image = QPixmap(image_path)
        scaledImage = image.scaled(self.SIZE, self.SIZE, Qt.KeepAspectRatio)
        self.setPixmap(scaledImage)


class DuplicateCandidateWidget(QWidget):
    def __init__(self, image_path, similarity):
        super().__init__()
        layout = QVBoxLayout(self)

        imageLabel = ThumbnailWidget(image_path)
        layout.addWidget(imageLabel)

        imageInfo = ImageInfoWidget(image_path, similarity)
        layout.addWidget(imageInfo)


class ImageGroupWidget(QWidget):
    def __init__(self, image_group, similarities):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignLeft)
        for i, image_path in enumerate(image_group):
            thumbnail = DuplicateCandidateWidget(image_path, similarities[i])
            layout.addWidget(thumbnail)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi(r'gui\gui.ui', self)
        self.setWidgetSlotConnections()
        self.show()

    def setWidgetSlotConnections(self):
        self.addFolderBtn.clicked.connect(self.addFolderBtn_click)
        self.delFolderBtn.clicked.connect(self.delFolderBtn_click)
        self.startBtn.clicked.connect(self.startBtn_click)
        self.stopBtn.clicked.connect(self.stopBtn_click)
        self.pauseBtn.clicked.connect(self.pauseBtn_click)
        self.moveBtn.clicked.connect(self.moveBtn_click)
        self.deleteBtn.clicked.connect(self.deleteBtn_click)

    def openFolderNameDialog(self):
        folder_name = QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QFileDialog.ShowDirsOnly
        )
        return folder_name

    @pyqtSlot()
    def addFolderBtn_click(self):
        folder_path = self.openFolderNameDialog()
        folder_path_item = QListWidgetItem()
        folder_path_item.setData(Qt.DisplayRole, folder_path)
        self.pathLW.addItem(folder_path_item)

    @pyqtSlot()
    def delFolderBtn_click(self):
        item_list = self.pathLW.selectedItems()
        for item in item_list:
            self.pathLW.takeItem(self.pathLW.row(item))

    @pyqtSlot()
    def startBtn_click(self):
        paths = [self.pathLW.item(i).data(0) for i in range(self.pathLW.count())]
        image_groups = duplicates.image_processing(paths)
        for image_group, similarities in image_groups:
            self.scrollAreaLayout.addWidget(ImageGroupWidget(image_group, similarities))

    @pyqtSlot()
    def stopBtn_click(self):
        pass

    @pyqtSlot()
    def pauseBtn_click(self):
        pass

    @pyqtSlot()
    def moveBtn_click(self):
        pass

    @pyqtSlot()
    def deleteBtn_click(self):
        pass
