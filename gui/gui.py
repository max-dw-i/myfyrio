from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QListWidgetItem
from PyQt5.uic import loadUi


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        loadUi(r'gui\gui.ui', self)
        self.addPathBtn.clicked.connect(self.addPathBtn_click)
        self.delPathBtn.clicked.connect(self.delPathBtn_click)
        self.show()

    def openFolderNameDialog(self):
        folder_name = QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QFileDialog.ShowDirsOnly
        )
        return folder_name

    @pyqtSlot()
    def addPathBtn_click(self):
        folder_path = self.openFolderNameDialog()
        folder_path_item = QListWidgetItem()
        folder_path_item.setData(0, folder_path)
        self.pathLW.addItem(folder_path_item)

    @pyqtSlot()
    def delPathBtn_click(self):
        item_list = self.pathLW.selectedItems()
        if not item_list:
            return None
        for item in item_list:
            self.pathLW.takeItem(self.pathLW.row(item))

    @pyqtSlot()
    def startBtn_click(self):
        pass
