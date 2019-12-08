'''Copyright 2019 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Doppelgänger.

Doppelgänger is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Doppelgänger is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Doppelgänger. If not, see <https://www.gnu.org/licenses/>.

-------------------------------------------------------------------------------

Module implementing graphical user interface
'''

import logging
import pathlib
from typing import Iterable, Optional, Set

from PyQt5 import QtCore, QtWidgets, uic

from doppelganger import core, processing, signals, widgets

UI = str(pathlib.Path('doppelganger') / 'gui.ui')
ABOUT_UI = str(pathlib.Path('doppelganger') / 'about.ui')

gui_logger = logging.getLogger('main.gui')


class AboutForm(QtWidgets.QMainWindow):
    """'Help' -> 'About' form"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        uic.loadUi(ABOUT_UI, self)

    def closeEvent(self, event) -> None:
        '''Function called on close event'''

        super().closeEvent(event)
        self.deleteLater()


class MainForm(QtWidgets.QMainWindow, QtCore.QObject):
    '''Main GUI class'''

    def __init__(self) -> None:
        super().__init__()
        uic.loadUi(UI, self)
        self.scrollAreaLayout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.signals = signals.Signals()

        self.threadpool = QtCore.QThreadPool()
        self._setWidgetEvents()

        self.sensitivity = 0
        self.highRb.click()

        self._setMenubar()

    def _setWidgetEvents(self) -> None:
        '''Link events and functions called on the events'''

        self.addFolderBtn.clicked.connect(self.addFolderBtn_click)
        self.delFolderBtn.clicked.connect(self.delFolderBtn_click)

        self.startBtn.clicked.connect(self.startBtn_click)
        self.stopBtn.clicked.connect(self.stopBtn_click)
        self.moveBtn.clicked.connect(self.moveBtn_click)
        self.deleteBtn.clicked.connect(self.deleteBtn_click)

        self.highRb.clicked.connect(self.highRb_click)
        self.mediumRb.clicked.connect(self.mediumRb_click)
        self.lowRb.clicked.connect(self.lowRb_click)

    def _setMenubar(self) -> None:
        """Initialise the menus of 'menubar'"""

        fileMenu = self.menubar.addMenu('File')
        fileMenu.setEnabled(False)
        #fileMenu.addAction(self.addFolderAct)
        #fileMenu.addSeparator(self.exitAct)

        editMenu = self.menubar.addMenu('Edit')
        editMenu.setEnabled(False)

        viewMenu = self.menubar.addMenu('View')
        viewMenu.setEnabled(False)
        #viewMenu.addAction(self.showDifference)

        optionsMenu = self.menubar.addMenu('Options')
        optionsMenu.setEnabled(False)
        #optionsMenu.addAction(self.showHiddenFolders)
        #optionsMenu.addAction(self.includeSubfolders)
        #optionsMenu.addAction(self.betweenFoldersOnly)
        #optionsMenu.addAction(self.confirmToClose)

        helpMenu = self.menubar.addMenu('Help')
        helpMenu.setObjectName('helpMenu')
        #helpMenu.addAction(self.help)
        #helpMenu.addAction(self.homePage)

        about = QtWidgets.QAction('About', self)
        about.setObjectName('aboutAction')
        about.triggered.connect(self.openAboutForm)
        helpMenu.addAction(about)

    def _call_on_selected_widgets(self, dst: Optional[core.FolderPath] = None) -> None:
        '''Call 'move' or 'delete' on selected widgets

        :param dst: if None, 'delete' is called, otherwise - 'move'
        '''

        for group_widget in self.scrollAreaWidget.findChildren(widgets.ImageGroupWidget):
            selected_widgets = group_widget.getSelectedWidgets()
            for selected_widget in selected_widgets:
                try:
                    if dst:
                        selected_widget.move(dst)
                    else:
                        selected_widget.delete()
                except OSError as e:
                    gui_logger.error(e)
            # If we select all (or except one) the images in a group,
            if len(group_widget) - len(selected_widgets) <= 1:
                # and all the selected images were processed correctly (so
                # there are no selected images anymore), delete the whole group
                if not group_widget.getSelectedWidgets():
                    group_widget.deleteLater()

    def openAboutForm(self) -> None:
        """Open 'Help' -> 'About' form"""

        about = self.findChildren(AboutForm, options=QtCore.Qt.FindDirectChildrenOnly)
        if about:
            about[0].activateWindow()
        else:
            about = AboutForm(self)
            about.show()

    def openFolderNameDialog(self) -> core.FolderPath:
        '''Open file dialog and return the full path of a folder'''

        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        return folder_path

    def showErrMsg(self):
        '''Show up when there've been some errors while running
        the programme'''

        msg_box = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Warning,
            'Errors',
            ("There've been some errors while running the programme. "
            "For more details, see 'errors.log'")
        )
        msg_box.exec()

    def clearMainForm(self) -> None:
        '''Clear the form from the previous duplicate images and labels'''

        for group_widget in self.findChildren(widgets.ImageGroupWidget):
            group_widget.deleteLater()

        for label in ['thumbnails', 'image_groups', 'remaining_images',
                      'found_in_cache', 'loaded_images', 'duplicates']:
            self.updateLabel(label, str(0))

        self.progressBar.setValue(0)

    def getFolders(self) -> Set[core.FolderPath]:
        '''Get all the folders the user added to 'pathListWidget'

        :returns: folders the user wants to process
        '''

        return {self.pathListWidget.item(i).data(QtCore.Qt.DisplayRole)
                for i in range(self.pathListWidget.count())}

    def render(self, image_groups: Iterable[core.Group]) -> None:
        '''Add 'ImageGroupWidget' to 'scrollArea'

        :param image_groups: groups of similar images
        '''

        if not image_groups:
            msg_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                'No duplicate images found',
                'No duplicate images have been found in the selected folders'
            )
            msg_box.exec()
        else:
            for group in image_groups:
                self.scrollAreaLayout.addWidget(widgets.ImageGroupWidget(group, self.scrollArea))

            for widget in self.findChildren(widgets.DuplicateWidget):
                widget.signals.clicked.connect(self.switchButtons)

    def updateLabel(self, label: str, text: str) -> None:
        '''Update text of :label:

        :param label: one of ('thumbnails', 'image_groups',
                              'remaining_images', 'found_in_cache',
                              'loaded_images', 'duplicates'),
        :param text: new text of :label:
        '''

        labels = {'thumbnails': self.thumbnailsLabel,
                  'image_groups': self.dupGroupLabel,
                  'remaining_images': self.remainingPicLabel,
                  'found_in_cache': self.foundInCacheLabel,
                  'loaded_images': self.loadedPicLabel,
                  'duplicates': self.duplicatesLabel}

        label_to_change = labels[label]
        label_text = label_to_change.text().split(' ')
        label_text[-1] = text
        label_to_change.setText(' '.join(label_text))

    def hasSelectedWidgets(self) -> bool:
        '''Check if there are selected 'DuplicateWidget' on the form

        :return: True if there are any selected ones
        '''

        for group_widget in self.findChildren(widgets.ImageGroupWidget):
            selected_widgets = group_widget.getSelectedWidgets()
            if selected_widgets:
                return True
        return False

    def switchButtons(self):
        if self.hasSelectedWidgets():
            self.moveBtn.setEnabled(True)
            self.deleteBtn.setEnabled(True)
        else:
            self.moveBtn.setEnabled(False)
            self.deleteBtn.setEnabled(False)

    def delete_images(self) -> None:
        """Delete selected images and corresponding 'DuplicateWidget's"""

        self._call_on_selected_widgets()
        self.switchButtons()

    def move_images(self) -> None:
        """Move selected images and delete corresponding 'DuplicateWidget's"""

        new_dst = self.openFolderNameDialog()
        if new_dst:
            self._call_on_selected_widgets(new_dst)
            self.switchButtons()

    def processing_finished(self) -> None:
        '''Called when image processing is finished'''

        self.progressBar.setValue(100)
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)

    def start_processing(self, folders: Iterable[core.FolderPath]) -> None:
        '''Set up image processing and run it

        :param folders: folders to process
        '''

        proc = processing.ImageProcessing(self.signals, folders, self.sensitivity)

        proc.signals.update_info.connect(self.updateLabel)
        proc.signals.update_progressbar.connect(self.progressBar.setValue)
        proc.signals.result.connect(self.render)
        proc.signals.error.connect(self.showErrMsg)
        proc.signals.finished.connect(self.processing_finished)

        worker = processing.Worker(proc.run)
        self.threadpool.start(worker)

    @QtCore.pyqtSlot()
    def highRb_click(self) -> None:
        """Function called on 'High' radio button click event"""

        self.sensitivity = 5

    @QtCore.pyqtSlot()
    def mediumRb_click(self) -> None:
        """Function called on 'Medium' radio button click event"""

        self.sensitivity = 10

    @QtCore.pyqtSlot()
    def lowRb_click(self) -> None:
        """Function called on 'Low' radio button click event"""

        self.sensitivity = 20

    @QtCore.pyqtSlot()
    def addFolderBtn_click(self) -> None:
        """Function called on 'Add Path' button click event"""

        folder_path = self.openFolderNameDialog()
        if folder_path:
            folder_path_item = QtWidgets.QListWidgetItem()
            folder_path_item.setData(QtCore.Qt.DisplayRole, folder_path)
            self.pathListWidget.addItem(folder_path_item)
            self.delFolderBtn.setEnabled(True)
            self.startBtn.setEnabled(True)

    @QtCore.pyqtSlot()
    def delFolderBtn_click(self) -> None:
        """Function called on 'Delete Path' button click event"""

        item_list = self.pathListWidget.selectedItems()
        for item in item_list:
            self.pathListWidget.takeItem(self.pathListWidget.row(item))

        if not self.pathListWidget.count():
            self.delFolderBtn.setEnabled(False)
            self.startBtn.setEnabled(False)

    @QtCore.pyqtSlot()
    def startBtn_click(self) -> None:
        """Function called on 'Start' button click event"""

        self.clearMainForm()
        self.stopBtn.setEnabled(True)
        self.startBtn.setEnabled(False)

        folders = self.getFolders()
        self.start_processing(folders)

    @QtCore.pyqtSlot()
    def stopBtn_click(self) -> None:
        """Function called on 'Stop' button click event"""

        self.signals.interrupted.emit()

        msgBox = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Information,
            'Interruption request',
            'The image processing has been stopped'
        )
        msgBox.exec()

        self.stopBtn.setEnabled(False)

    @QtCore.pyqtSlot()
    def moveBtn_click(self) -> None:
        """Function called on 'Move' button click event"""

        self.move_images()

    @QtCore.pyqtSlot()
    def deleteBtn_click(self) -> None:
        """Function called on 'Delete' button click event"""

        confirm = QtWidgets.QMessageBox.question(
            self,
            'Deletion confirmation',
            'Do you really want to remove the selected images?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
        )

        if confirm == QtWidgets.QMessageBox.Yes:
            self.delete_images()
