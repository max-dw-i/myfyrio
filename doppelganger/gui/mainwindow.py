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

import webbrowser
from typing import Iterable

from PyQt5 import QtCore, QtGui, QtWidgets, uic

from doppelganger import core, processing, signals
from doppelganger.gui import (actionsgroupbox, imageviewwidget, pathsgroupbox,
                              processinggroupbox, sensitivitygroupbox)
from doppelganger.gui.aboutwindow import AboutWindow
from doppelganger.gui.preferenceswindow import PreferencesWindow
from doppelganger.resources.paths import ICON, MAIN_UI, resource_path


def errorMessage(msg: str) -> None:
    '''Show up when there've been some errors while processing
    images (slot function for signal 'error')

    :param msg: error message
    '''

    msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                    'Errors', msg)
    msg_box.exec()


class MainWindow(QtWidgets.QMainWindow):
    '''Main GUI class'''

    def __init__(self) -> None:
        super().__init__()

        uic.loadUi(resource_path(MAIN_UI), self)

        app_icon = QtGui.QIcon(resource_path(ICON))
        self.setWindowIcon(app_icon)

        self.aboutWindow = AboutWindow(self)
        self.preferencesWindow = PreferencesWindow(self)

        self.signals = signals.Signals()
        self.threadpool = QtCore.QThreadPool()

        self.interrupted = False
        self._setInterruptionMsgBox()

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

    def _setInterruptionMsgBox(self) -> None:
        self.interruptionMsg = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Information,
            'Interruption request',
            'The image processing is being stopped. It may take some time. '
            'Please, do not close this message until you are notified about '
            'the result of your request...'
        )
        self.interruptionMsg.setStandardButtons(QtWidgets.QMessageBox.NoButton)

    def _setImageViewWidget(self) -> None:
        self.imageViewWidget = imageviewwidget.ImageViewWidget(
            self.preferencesWindow.conf,
            self.scrollArea
        )
        self.scrollArea.setWidget(self.imageViewWidget)

    def _setPathsGroupBox(self) -> None:
        self.pathsGrp = pathsgroupbox.PathsGroupBox(self.bottomWidget)
        self.horizontalLayout.addWidget(self.pathsGrp)

        self.pathsGrp.pathsList.itemSelectionChanged.connect(
            self.switchDelFolderAction
        )
        self.pathsGrp.addFolderBtn.clicked.connect(self.switchStartBtn)
        self.pathsGrp.delFolderBtn.clicked.connect(self.switchStartBtn)

    def _setProcessingGroupBox(self) -> None:
        self.processingGrp = processinggroupbox.ProcessingGroupBox(
            self.bottomWidget
        )
        self.horizontalLayout.addWidget(self.processingGrp)

        self.processingGrp.startBtn.clicked.connect(self.startProcessing)
        self.processingGrp.stopBtn.clicked.connect(self.stopProcessing)

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

        self.actionsGrp.moveBtn.clicked.connect(self.moveImages)
        self.actionsGrp.deleteBtn.clicked.connect(self.deleteImages)
        self.actionsGrp.autoSelectBtn.clicked.connect(
            self.imageViewWidget.autoSelect
        )
        self.actionsGrp.unselectBtn.clicked.connect(
            self.imageViewWidget.unselect
        )

    def _setMenubar(self) -> None:
        preferencesWindow = QtCore.QVariant(self.preferencesWindow)
        self.preferencesAction.setData(preferencesWindow)

        aboutWindow = QtCore.QVariant(self.aboutWindow)
        self.aboutAction.setData(aboutWindow)

        self.addFolderAction.triggered.connect(self.pathsGrp.addPath)
        self.addFolderAction.triggered.connect(self.switchStartBtn)
        self.delFolderAction.triggered.connect(self.pathsGrp.delPath)
        self.delFolderAction.triggered.connect(self.switchStartBtn)
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

    def switchDelFolderAction(self) -> None:
        if self.pathsGrp.pathsList.selectedItems():
            self.delFolderAction.setEnabled(True)
        else:
            self.delFolderAction.setEnabled(False)

    def switchStartBtn(self) -> None:
        if self.pathsGrp.pathsList.count():
            self.processingGrp.startBtn.setEnabled(True)
        else:
            self.processingGrp.startBtn.setEnabled(False)

    def switchImgActionsAndBtns(self):
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
        p.signals.error.connect(errorMessage)
        p.signals.finished.connect(self.processingFinished)

        return p

    def startProcessing(self) -> None:
        self.imageViewWidget.clear()
        self.actionsGrp.autoSelectBtn.setEnabled(False)
        self.autoSelectAction.setEnabled(False)
        self.processingGrp.startProcessing()

        processing_obj = self._setImageProcessingObj()
        worker = processing.Worker(processing_obj.run)
        self.threadpool.start(worker)

    def stopProcessing(self) -> None:
        self.signals.interrupted.emit()
        self.interrupted = True
        self.processingGrp.stopBtn.setEnabled(False)
        self.interruptionMsg.exec()

    def processingFinished(self) -> None:
        self.processingGrp.stopProcessing()
        if self.imageViewWidget.widgets:
            self.actionsGrp.autoSelectBtn.setEnabled(True)
            self.autoSelectAction.setEnabled(True)

        if self.interrupted:
            self.interrupted = False
            self.interruptionMsg.setText(
                'The image processing has been stopped. '
                'You can close this message...'
            )
            self.interruptionMsg.setStandardButtons(QtWidgets.QMessageBox.Ok)

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
        docs_url = 'https://github.com/oratosquilla-oratoria/doppelganger'
        webbrowser.open(docs_url)

    def deleteImages(self) -> None:
        confirm = QtWidgets.QMessageBox.question(
            self,
            'Deletion confirmation',
            'Do you really want to remove the selected images?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
        )

        if confirm == QtWidgets.QMessageBox.Yes:
            self.imageViewWidget.delete()
            self.switchImgActionsAndBtns()

    def moveImages(self) -> None:
        new_dst = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if new_dst:
            self.imageViewWidget.move(new_dst)
            self.switchImgActionsAndBtns()

    def render(self, image_groups: Iterable[core.Group]) -> None:
        if image_groups:
            self.imageViewWidget.render(image_groups)

            for group_w in self.imageViewWidget.widgets:
                for dup_w in group_w.widgets:
                    dup_w.signals.clicked.connect(self.switchImgActionsAndBtns)
        else:
            msg_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                'No duplicate images found',
                'No duplicate images have been found in the selected folders'
            )
            msg_box.exec()
