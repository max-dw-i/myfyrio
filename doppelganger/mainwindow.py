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
from typing import Iterable

from PyQt5 import QtCore, QtWidgets, uic

from doppelganger import (actionsgroupbox, core, imageviewwidget,
                          pathsgroupbox, processing, processinggroupbox,
                          sensitivitygroupbox, signals)
from doppelganger.aboutwindow import AboutWindow
from doppelganger.preferenceswindow import PreferencesWindow

gui_logger = logging.getLogger('main.mainwindow')


def showErrMsg(msg: str) -> None:
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


class MainWindow(QtWidgets.QMainWindow, QtCore.QObject):
    '''Main GUI class'''

    def __init__(self) -> None:
        super().__init__()

        UI = pathlib.Path('doppelganger/resources/ui/mainwindow.ui')
        uic.loadUi(str(UI), self)

        self.aboutWindow = AboutWindow(self)
        self.preferencesWindow = PreferencesWindow(self)

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

    def _setImageViewWidget(self) -> None:
        self.imageViewWidget = imageviewwidget.ImageViewWidget(self.scrollArea)
        self.scrollArea.setWidget(self.imageViewWidget)

    def _setPathsGroupBox(self) -> None:
        self.pathsGrp = pathsgroupbox.PathsGroupBox(self.bottomWidget)
        self.horizontalLayout.addWidget(self.pathsGrp)

        self.pathsList = self.pathsGrp.pathsList
        self.addFolderBtn = self.pathsGrp.addFolderBtn
        self.delFolderBtn = self.pathsGrp.delFolderBtn

        self.pathsList.itemSelectionChanged.connect(self.setDelFolderActionEnabled)
        self.addFolderBtn.clicked.connect(self.setStartBtnEnabled)
        self.delFolderBtn.clicked.connect(self.setStartBtnEnabled)

    def _setProcessingGroupBox(self) -> None:
        self.processingGrp = processinggroupbox.ProcessingGroupBox(
            self.bottomWidget
        )
        self.horizontalLayout.addWidget(self.processingGrp)

        self.startBtn = self.processingGrp.startBtn
        self.stopBtn = self.processingGrp.stopBtn

        self.startBtn.clicked.connect(self.startProcessing)
        self.stopBtn.clicked.connect(self.stopProcessing)

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

        self.moveBtn.clicked.connect(self.moveImages)
        self.deleteBtn.clicked.connect(self.deleteImages)
        self.autoSelectBtn.clicked.connect(self.imageViewWidget.autoSelect)
        self.unselectBtn.clicked.connect(self.imageViewWidget.unselect)

    def _setMenubar(self) -> None:
        preferencesWindow = QtCore.QVariant(self.preferencesWindow)
        self.preferencesAction.setData(preferencesWindow)

        aboutWindow = QtCore.QVariant(self.aboutWindow)
        self.aboutAction.setData(aboutWindow)

        self.addFolderAction.triggered.connect(self.pathsGrp.addPath)
        self.delFolderAction.triggered.connect(self.pathsGrp.delPath)
        self.preferencesAction.triggered.connect(
            self.openWindow
        )
        self.exitAction.triggered.connect(self.close)
        self.moveAction.triggered.connect(self.moveImages)
        self.deleteAction.triggered.connect(self.deleteImages)
        self.autoSelectAction.triggered.connect(
            self.imageViewWidget.autoSelect
        )
        self.unselectAction.triggered.connect(self.imageViewWidget.unselect)
        self.docsAction.triggered.connect(self.openDocs)
        self.homePageAction.triggered.connect(self.openDocs)
        self.aboutAction.triggered.connect(self.openWindow)

    def setDelFolderActionEnabled(self) -> None:
        if self.pathsList.selectedItems():
            self.delFolderAction.setEnabled(True)
        else:
            self.delFolderAction.setEnabled(False)

    def setStartBtnEnabled(self) -> None:
        if self.pathsList.count():
            self.startBtn.setEnabled(True)
        else:
            self.startBtn.setEnabled(False)

    def _setImageProcessingObj(self) -> processing.ImageProcessing:
        p = processing.ImageProcessing(
            self.signals,
            self.pathsGrp.paths(),
            self.sensitivityGrp.sensitivity,
            self.preferencesWindow.conf
        )

        p.signals.update_info.connect(self.processingGrp.updateLabel)
        p.signals.update_progressbar.connect(
            self.processingGrp.processProg.setValue
        )
        p.signals.result.connect(self.render)
        p.signals.error.connect(showErrMsg)
        p.signals.finished.connect(self.processing_finished)

        return p

    def startProcessing(self) -> None:
        self.imageViewWidget.clear()
        self._setAutoSelectMenuActionNBtnEnabled(False)

        processing_obj = self._setImageProcessingObj()
        worker = processing.Worker(processing_obj.run)
        self.threadpool.start(worker)

    def stopProcessing(self) -> None:
        self.signals.interrupted.emit()

        msgBox = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Information,
            'Interruption request',
            'The image processing has been stopped'
        )
        msgBox.exec()

    def closeEvent(self, event) -> None:
        if self.preferencesWindow.conf['close_confirmation']:
            confirm = QtWidgets.QMessageBox.question(
                self,
                'Closing confirmation',
                'Do you really want to exit?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
            )

            if confirm == QtWidgets.QMessageBox.Cancel:
                event.ignore()

    def openWindow(self) -> None:
        window = self.sender().data()
        if window.isVisible():
            window.activateWindow()
        else:
            window.show()

    def openDocs(self) -> None:
        '''Open URL with the docs'''

        docs_url = 'https://github.com/oratosquilla-oratoria/doppelganger'
        webbrowser.open(docs_url)

    def _setImageMenuBarActionsEnabled(self, enable: bool) -> None:
        self.moveAction.setEnabled(enable)
        self.deleteAction.setEnabled(enable)
        self.unselectAction.setEnabled(enable)

    def _setImageActionsEnabled(self):
        if self.imageViewWidget.hasSelectedWidgets():
            self.actionsGrp.setEnabled(True)
            self._setImageMenuBarActionsEnabled(True)
        else:
            self.actionsGrp.setEnabled(False)
            self._setImageMenuBarActionsEnabled(False)

    def deleteImages(self) -> None:
        """Delete selected images and corresponding 'DuplicateWidget's"""

        confirm = QtWidgets.QMessageBox.question(
            self,
            'Deletion confirmation',
            'Do you really want to remove the selected images?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
        )

        if confirm == QtWidgets.QMessageBox.Yes:
            self.imageViewWidget.call_on_selected_widgets(
                self.preferencesWindow.conf
            )
            self._setImageActionsEnabled()

    def moveImages(self) -> None:
        """Move selected images and delete corresponding 'DuplicateWidget's"""

        new_dst = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if new_dst:
            self.imageViewWidget.call_on_selected_widgets(
                self.preferencesWindow.conf,
                new_dst
            )
            self._setImageActionsEnabled()

    def render(self, image_groups: Iterable[core.Group]) -> None:
        self.imageViewWidget.render(self.preferencesWindow.conf, image_groups)

        for widget in self.findChildren(imageviewwidget.DuplicateWidget):
            widget.signals.clicked.connect(self._setImageActionsEnabled)

    def _setAutoSelectMenuActionNBtnEnabled(self, enable: bool) -> None:
        self.autoSelectBtn.setEnabled(enable)
        self.autoSelectAction.setEnabled(enable)

    def processing_finished(self) -> None:
        '''Called when image processing is finished'''

        self.processingGrp.stopProcessing()
        self._setAutoSelectMenuActionNBtnEnabled(True)
