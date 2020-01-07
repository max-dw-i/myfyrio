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
from typing import Iterable, Optional

from PyQt5 import QtCore, QtWidgets, uic

from doppelganger import (actionsgroupbox, core, imageviewwidget,
                          pathsgroupbox, processing, processinggroupbox,
                          sensitivitygroupbox, signals)
from doppelganger.aboutwindow import AboutWindow
from doppelganger.preferenceswindow import PreferencesWindow

gui_logger = logging.getLogger('main.mainwindow')


class MainWindow(QtWidgets.QMainWindow, QtCore.QObject):
    '''Main GUI class'''

    def __init__(self) -> None:
        super().__init__()

        UI = pathlib.Path('doppelganger/resources/ui/mainwindow.ui')
        uic.loadUi(str(UI), self)

        self.signals = signals.Signals()
        self.threadpool = QtCore.QThreadPool()

        self._setImageViewWidget()
        self._setPathsGroupBox()
        self._setProcessingGroupBox()

        self.sensitivityActionsWidget = QtWidgets.QWidget(self.bottomWidget)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(
            self.sensitivityActionsWidget
        )
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.addWidget(self.sensitivityActionsWidget)

        self._setSensitivityGroupBox()
        self._setActionsGroupWidget()
        self._setMenubar()

        self.aboutWindow = AboutWindow(self)
        self.preferencesWindow = PreferencesWindow(self)

    def _setImageViewWidget(self) -> None:
        self.imageViewWidget = imageviewwidget.ImageViewWidget(self.scrollArea)
        self.scrollArea.setWidget(self.imageViewWidget)

    def _setPathsGroupBox(self) -> None:
        self.pathsGrp = pathsgroupbox.PathsGroupBox(self.bottomWidget)
        self.horizontalLayout.addWidget(self.pathsGrp)

        self.pathsList = self.pathsGrp.pathsList
        self.addFolderBtn = self.pathsGrp.addFolderBtn
        self.delFolderBtn = self.pathsGrp.delFolderBtn

        self.pathsList.itemSelectionChanged.connect(self.enableDelFolderAction)
        self.addFolderBtn.clicked.connect(self.enableStartBtn)
        self.delFolderBtn.clicked.connect(self.enableStartBtn)

    def _setProcessingGroupBox(self) -> None:
        self.processingGrp = processinggroupbox.ProcessingGroupBox(
            self.bottomWidget
        )
        self.horizontalLayout.addWidget(self.processingGrp)

        self.startBtn = self.processingGrp.startBtn
        self.stopBtn = self.processingGrp.stopBtn

        self.startBtn.clicked.connect(self.startBtnClick)
        self.stopBtn.clicked.connect(self.stopBtnClick)

    def _setSensitivityGroupBox(self) -> None:
        self.sensitivityGrp = sensitivitygroupbox.SensitivityGroupBox(
            self.sensitivityActionsWidget
        )
        self.verticalLayout_2.addWidget(self.sensitivityGrp)

    def _setActionsGroupWidget(self) -> None:
        self.actionsGrp = actionsgroupbox.ActionsGroupBox(
            self.sensitivityActionsWidget
        )
        self.verticalLayout_2.addWidget(self.actionsGrp)

        self.moveBtn = self.actionsGrp.moveBtn
        self.deleteBtn = self.actionsGrp.deleteBtn
        self.autoSelectBtn = self.actionsGrp.autoSelectBtn
        self.unselectBtn = self.actionsGrp.unselectBtn

        self.moveBtn.clicked.connect(self.moveBtnClick)
        self.deleteBtn.clicked.connect(self.deleteBtnClick)
        self.autoSelectBtn.clicked.connect(self.autoSelectBtnClick)
        self.unselectBtn.clicked.connect(self.unselectBtnClick)

    def _setMenubar(self) -> None:
        self.addFolderAction.triggered.connect(self.pathsGrp.addPath)
        self.delFolderAction.triggered.connect(self.pathsGrp.delPath)
        self.preferencesAction.triggered.connect(
            self.openPreferencesWindow
        )
        self.exitAction.triggered.connect(self.close)
        self.moveAction.triggered.connect(self.moveBtnClick)
        self.deleteAction.triggered.connect(self.deleteBtnClick)
        self.autoSelectAction.triggered.connect(self.auto_select)
        self.unselectAction.triggered.connect(self.unselect)
        self.docsAction.triggered.connect(self.openDocs)
        self.homePageAction.triggered.connect(self.openDocs)
        self.aboutAction.triggered.connect(self.openAboutWindow)

    def enableDelFolderAction(self) -> None:
        if self.pathsList.selectedItems():
            self.delFolderAction.setEnabled(True)
        else:
            self.delFolderAction.setEnabled(False)

    def enableStartBtn(self) -> None:
        if self.pathsList.count():
            self.startBtn.setEnabled(True)
        else:
            self.startBtn.setEnabled(False)

    def startBtnClick(self) -> None:
        self.clearMainForm()
        self.autoSelectBtn.setEnabled(False)
        self.autoSelectAction.setEnabled(False)

        self.start_processing(self.pathsGrp.paths())

    def stopBtnClick(self) -> None:
        self.signals.interrupted.emit()

        msgBox = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Information,
            'Interruption request',
            'The image processing has been stopped'
        )
        msgBox.exec()

    def _call_on_selected_widgets(
            self,
            dst: Optional[core.FolderPath] = None
        ) -> None:
        '''Call 'move' or 'delete' on selected widgets

        :param dst: if None, 'delete' is called, otherwise - 'move'
        '''

        groups = self.imageViewWidget.findChildren(
            imageviewwidget.ImageGroupWidget
        )
        for group_widget in groups:
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
        '''Open file dialog and return the full path of a folder

        :return: folder path
        '''

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

        groups = self.findChildren(imageviewwidget.ImageGroupWidget)
        for group_widget in groups:
            group_widget.deleteLater()

    def switchButtons(self):
        if self.imageViewWidget.hasSelectedWidgets():
            self.actionsGrp.setEnabled(True)
            self.moveAction.setEnabled(True)
            self.deleteAction.setEnabled(True)
            self.unselectAction.setEnabled(True)
        else:
            self.actionsGrp.setEnabled(False)
            self.moveAction.setEnabled(False)
            self.deleteAction.setEnabled(False)
            self.unselectAction.setEnabled(False)

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

        group_widgets = self.findChildren(imageviewwidget.ImageGroupWidget)
        for group in group_widgets:
            group.auto_select()

    def unselect(self) -> None:
        '''Unselect all the selected DuplicateWidget's'''

        duplicate_widgets = self.findChildren(imageviewwidget.DuplicateWidget)
        for w in duplicate_widgets:
            if w.selected:
                w.click()

    def render(self, image_groups: Iterable[core.Group]) -> None:
        self.imageViewWidget.render(self.preferencesWindow.conf, image_groups)

        for widget in self.findChildren(imageviewwidget.DuplicateWidget):
            widget.signals.clicked.connect(self.switchButtons)

    def processing_finished(self) -> None:
        '''Called when image processing is finished'''

        self.processingGrp.processProg.setValue(100)
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self.autoSelectBtn.setEnabled(True)
        self.autoSelectAction.setEnabled(True)

    def start_processing(self, folders: Iterable[core.FolderPath]) -> None:
        '''Set up image processing and run it

        :param folders: folders to process,
        '''

        proc = processing.ImageProcessing(
            self.signals,
            folders,
            self.sensitivityGrp.sensitivity,
            self.preferencesWindow.conf
        )

        proc.signals.update_info.connect(self.processingGrp.updateLabel)
        proc.signals.update_progressbar.connect(
            self.processingGrp.processProg.setValue
        )
        proc.signals.result.connect(self.render)
        proc.signals.error.connect(self.showErrMsg)
        proc.signals.finished.connect(self.processing_finished)

        worker = processing.Worker(proc.run)
        self.threadpool.start(worker)

    def moveBtnClick(self) -> None:
        """Function called on 'Move' button click event"""

        self.move_images()

    def deleteBtnClick(self) -> None:
        """Function called on 'Delete' button click event"""

        confirm = QtWidgets.QMessageBox.question(
            self,
            'Deletion confirmation',
            'Do you really want to remove the selected images?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
        )

        if confirm == QtWidgets.QMessageBox.Yes:
            self.delete_images()

    def autoSelectBtnClick(self) -> None:
        """Function called on 'Auto Select' button click event"""

        self.auto_select()

    def unselectBtnClick(self) -> None:
        """Function called on 'Unselect' button click event"""

        self.unselect()
