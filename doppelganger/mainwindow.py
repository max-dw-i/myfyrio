'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

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

Module implementing window "Main"
'''

import logging
import pathlib
import webbrowser
from typing import Iterable, Optional, Set

from PyQt5 import QtCore, QtWidgets, uic

from doppelganger import core, processing, signals, widgets
from doppelganger.aboutwindow import AboutWindow
from doppelganger.preferenceswindow import PreferencesWindow

gui_logger = logging.getLogger('main.mainwindow')


class MainWindow(QtWidgets.QMainWindow, QtCore.QObject):
    '''Main GUI class'''

    def __init__(self) -> None:
        super().__init__()
        MAIN_UI = pathlib.Path('doppelganger/resources/ui/mainwindow.ui')
        uic.loadUi(str(MAIN_UI), self)
        self.scrollAreaLayout.setAlignment(QtCore.Qt.AlignTop
                                           | QtCore.Qt.AlignLeft)

        self.signals = signals.Signals()

        self.threadpool = QtCore.QThreadPool()
        self._setWidgetEvents()
        self.sensitivity = 0
        self.veryHighRbtn.click()

        self._setMenubar()

        self.aboutWindow = AboutWindow(self)
        self.preferencesWindow = PreferencesWindow(self)

    def _setWidgetEvents(self) -> None:
        '''Link events and functions called on the events'''

        self.addFolderBtn.clicked.connect(self.addFolderBtn_click)
        self.delFolderBtn.clicked.connect(self.delFolderBtn_click)

        self.startBtn.clicked.connect(self.startBtn_click)
        self.stopBtn.clicked.connect(self.stopBtn_click)
        self.moveBtn.clicked.connect(self.moveBtn_click)
        self.deleteBtn.clicked.connect(self.deleteBtn_click)
        self.autoSelectBtn.clicked.connect(self.autoSelectBtn_click)
        self.unselectBtn.clicked.connect(self.unselectBtn_click)

        self.veryHighRbtn.clicked.connect(self.veryHighRb_click)
        self.highRbtn.clicked.connect(self.highRb_click)
        self.mediumRbtn.clicked.connect(self.mediumRb_click)
        self.lowRbtn.clicked.connect(self.lowRb_click)
        self.veryLowRbtn.clicked.connect(self.veryLowRb_click)

    def _setMenubar(self) -> None:
        """Initialise the menus of 'menubar'"""

        self.addFolderAction.triggered.connect(self.add_folder)
        self.removeFolderAction.triggered.connect(self.del_folder)
        self.preferencesAction.triggered.connect(self.openPreferencesWindow)
        self.exitAction.triggered.connect(self.close)
        self.moveAction.triggered.connect(self.moveBtn_click)
        self.deleteAction.triggered.connect(self.deleteBtn_click)
        self.autoSelectAction.triggered.connect(self.auto_select)
        self.unselectAction.triggered.connect(self.unselect)
        self.docsAction.triggered.connect(self.openDocs)
        self.homePageAction.triggered.connect(self.openDocs)
        self.aboutAction.triggered.connect(self.openAboutWindow)

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
                    msgBox = QtWidgets.QMessageBox(
                        QtWidgets.QMessageBox.Warning,
                        'Removing/Moving image',
                        ('Error occured while removing/moving '
                         f'image {selected_widget.image.path}')
                    )
                    msgBox.exec()
                else:
                    if self.preferencesWindow.conf['delete_dirs']:
                        selected_widget.image.del_parent_dir()
            # If we select all (or except one) the images in a group,
            if len(group_widget) - len(selected_widgets) <= 1:
                # and all the selected images were processed correctly (so
                # there are no selected images anymore), delete the whole group
                if not group_widget.getSelectedWidgets():
                    group_widget.deleteLater()

    def closeEvent(self, event) -> None:
        '''Called on programme close event'''

        if self.preferencesWindow.conf['close_confirmation']:
            confirm = QtWidgets.QMessageBox.question(
                self,
                'Closing confirmation',
                'Do you really want to exit?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
            )

            if confirm == QtWidgets.QMessageBox.Cancel:
                event.ignore()

    def openAboutWindow(self) -> None:
        if self.aboutWindow.isVisible():
            self.aboutWindow.activateWindow()
        else:
            self.aboutWindow.show()

    def openPreferencesWindow(self) -> None:
        if self.preferencesWindow.isVisible():
            self.preferencesWindow.activateWindow()
        else:
            self.preferencesWindow.show()

    def openFolderNameDialog(self) -> core.FolderPath:
        '''Open file dialog and return the full path of a folder'''

        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        return folder_path

    def openDocs(self) -> None:
        '''Open URL with the docs'''

        docs_url = 'https://github.com/oratosquilla-oratoria/doppelganger'
        webbrowser.open(docs_url)

    def showErrMsg(self, msg: str) -> None:
        '''Show up when there've been some errors while running
        the programme

        :param msg: error message
        '''

        msg_box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            'Errors',
            (f"{msg}. For more details, see 'errors.log'")
        )
        msg_box.exec()

    def clearMainForm(self) -> None:
        '''Clear the form from the previous duplicate images and labels'''

        for group_widget in self.findChildren(widgets.ImageGroupWidget):
            group_widget.deleteLater()

        for label in ['thumbnails', 'image_groups', 'remaining_images',
                      'found_in_cache', 'loaded_images', 'duplicates']:
            self.updateLabel(label, str(0))

        self.processProg.setValue(0)

    def getFolders(self) -> Set[core.FolderPath]:
        '''Get all the folders the user added to 'pathsList'

        :returns: folders the user wants to process
        '''

        return {self.pathsList.item(i).data(QtCore.Qt.DisplayRole)
                for i in range(self.pathsList.count())}

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
                self.scrollAreaLayout.addWidget(
                    widgets.ImageGroupWidget(group, self.preferencesWindow.conf, self.scrollArea)
                )

            for widget in self.findChildren(widgets.DuplicateWidget):
                widget.signals.clicked.connect(self.switchButtons)

    def updateLabel(self, label: str, text: str) -> None:
        '''Update text of :label:

        :param label: one of ('thumbnails', 'image_groups',
                              'remaining_images', 'found_in_cache',
                              'loaded_images', 'duplicates'),
        :param text: new text of :label:
        '''

        labels = {'thumbnails': self.thumbnailsLbl,
                  'image_groups': self.dupGroupLbl,
                  'remaining_images': self.remainingPicLbl,
                  'found_in_cache': self.foundInCacheLbl,
                  'loaded_images': self.loadedPicLbl,
                  'duplicates': self.duplicatesLbl}

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
            self.unselectBtn.setEnabled(True)

            self.moveAction.setEnabled(True)
            self.deleteAction.setEnabled(True)
            self.unselectAction.setEnabled(True)
        else:
            self.moveBtn.setEnabled(False)
            self.deleteBtn.setEnabled(False)
            self.unselectBtn.setEnabled(False)

            self.moveAction.setEnabled(False)
            self.deleteAction.setEnabled(False)
            self.unselectAction.setEnabled(False)

    def add_folder(self):
        '''Add folder for searching duplicate images'''

        folder_path = self.openFolderNameDialog()
        if folder_path:
            folder_path_item = QtWidgets.QListWidgetItem()
            folder_path_item.setData(QtCore.Qt.DisplayRole, folder_path)
            self.pathsList.addItem(folder_path_item)
            self.delFolderBtn.setEnabled(True)
            self.startBtn.setEnabled(True)
            self.removeFolderAction.setEnabled(True)

    def del_folder(self):
        '''Delete folder from searching duplicate images'''

        item_list = self.pathsList.selectedItems()
        for item in item_list:
            self.pathsList.takeItem(self.pathsList.row(item))

        if not self.pathsList.count():
            self.delFolderBtn.setEnabled(False)
            self.startBtn.setEnabled(False)
            self.removeFolderAction.setEnabled(False)

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

    def auto_select(self) -> None:
        '''Automatic selection of DuplicateWidget's'''

        group_widgets = self.findChildren(widgets.ImageGroupWidget)
        for group in group_widgets:
            group.auto_select()

    def unselect(self) -> None:
        '''Unselect all the selected DuplicateWidget's'''

        duplicate_widgets = self.findChildren(widgets.DuplicateWidget)
        for w in duplicate_widgets:
            if w.selected:
                w.click()

    def processing_finished(self) -> None:
        '''Called when image processing is finished'''

        self.processProg.setValue(100)
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self.autoSelectBtn.setEnabled(True)
        self.autoSelectAction.setEnabled(True)

    def start_processing(self, folders: Iterable[core.FolderPath]) -> None:
        '''Set up image processing and run it

        :param folders: folders to process,
        '''

        proc = processing.ImageProcessing(self.signals, folders,
                                          self.sensitivity, self.preferencesWindow.conf)

        proc.signals.update_info.connect(self.updateLabel)
        proc.signals.update_progressbar.connect(self.processProg.setValue)
        proc.signals.result.connect(self.render)
        proc.signals.error.connect(self.showErrMsg)
        proc.signals.finished.connect(self.processing_finished)

        worker = processing.Worker(proc.run)
        self.threadpool.start(worker)

    def veryHighRb_click(self) -> None:
        """Function called on 'High' radio button click event"""

        self.sensitivity = 0

    def highRb_click(self) -> None:
        """Function called on 'High' radio button click event"""

        self.sensitivity = 5

    def mediumRb_click(self) -> None:
        """Function called on 'Medium' radio button click event"""

        self.sensitivity = 10

    def lowRb_click(self) -> None:
        """Function called on 'Low' radio button click event"""

        self.sensitivity = 15

    def veryLowRb_click(self) -> None:
        """Function called on 'High' radio button click event"""

        self.sensitivity = 20

    def addFolderBtn_click(self) -> None:
        """Function called on 'Add Path' button click event"""

        self.add_folder()

    def delFolderBtn_click(self) -> None:
        """Function called on 'Delete Path' button click event"""

        self.del_folder()

    def startBtn_click(self) -> None:
        """Function called on 'Start' button click event"""

        self.clearMainForm()
        self.stopBtn.setEnabled(True)
        self.startBtn.setEnabled(False)
        self.autoSelectBtn.setEnabled(False)
        self.autoSelectAction.setEnabled(False)

        folders = self.getFolders()
        self.start_processing(folders)

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

    def moveBtn_click(self) -> None:
        """Function called on 'Move' button click event"""

        self.move_images()

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

    def autoSelectBtn_click(self) -> None:
        """Function called on 'Auto Select' button click event"""

        self.auto_select()

    def unselectBtn_click(self) -> None:
        """Function called on 'Unselect' button click event"""

        self.unselect()
