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

from doppelganger import core, processing
from doppelganger.gui import (actionsgroupbox, imageviewwidget, pathsgroupbox,
                              processinggroupbox, sensitivitygroupbox)
from doppelganger.gui.aboutwindow import AboutWindow
from doppelganger.gui.preferenceswindow import PreferencesWindow
from doppelganger.resources.manager import UI, Image, resource


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

        uic.loadUi(resource(UI.MAIN), self)

        app_icon = QtGui.QIcon(resource(Image.ICON))
        self.setWindowIcon(app_icon)

        self.aboutWindow = AboutWindow(self)
        self.preferencesWindow = PreferencesWindow(self)

        self.threadpool = QtCore.QThreadPool.globalInstance()

        self.image_processing = False
        self.widgets_processing = False

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
        self.imageViewWidget = imageviewwidget.ImageViewWidget(
            self.preferencesWindow.conf,
            self.scrollArea
        )
        self.scrollArea.setWidget(self.imageViewWidget)

        self.imageViewWidget.signals.finished.connect(
            self.widgetsProcessingFinished
        )
        self.imageViewWidget.signals.interrupted.connect(
            self.widgetsProcessingInterrupted
        )

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
        self.processingGrp.stopBtn.clicked.connect(self.disableStopBtn)
        self.processingGrp.stopBtn.clicked.connect(
            self.imageViewWidget.setInterrupted
        )

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
        processing_run = self.image_processing or self.widgets_processing
        if self.pathsGrp.pathsList.count() and not processing_run:
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
            self.pathsGrp.paths(),
            self.sensitivityGrp.sensitivity,
            self.preferencesWindow.conf
        )

        p.signals.update_info.connect(self.processingGrp.updateLabel)
        p.signals.update_progressbar.connect(
            self.processingGrp.processProg.setValue
        )
        p.signals.image_groups.connect(self.render)
        p.signals.error.connect(errorMessage)
        p.signals.interrupted.connect(self.imageProcessingInterrupted)

        self.processingGrp.stopBtn.clicked.connect(p.setInterrupted)

        return p

    def startProcessing(self) -> None:
        self.imageViewWidget.clear()
        self.actionsGrp.autoSelectBtn.setEnabled(False)
        self.autoSelectAction.setEnabled(False)
        self.processingGrp.startProcessing()

        self.imageViewWidget.interrupted = False
        self.image_processing = True

        processing_obj = self._setImageProcessingObj()
        worker = processing.Worker(processing_obj.run)
        self.threadpool.start(worker)

    def disableStopBtn(self) -> None:
        self.processingGrp.stopBtn.setEnabled(False)

    def processingFinished(self) -> None:
        self.switchStartBtn()
        self.processingGrp.stopBtn.setEnabled(False)
        self.processingGrp.processProg.setValue(100)

        if self.imageViewWidget.widgets:
            self.actionsGrp.autoSelectBtn.setEnabled(True)
            self.autoSelectAction.setEnabled(True)

    def imageProcessingInterrupted(self) -> None:
        self._clearThreadpool()
        self.imageProcessingFinished()

    def imageProcessingFinished(self) -> None:
        self.image_processing = False
        if not self.widgets_processing:
            self.processingFinished()

    def widgetsProcessingInterrupted(self) -> None:
        self._clearThreadpool()
        self.widgetsProcessingFinished()

    def widgetsProcessingFinished(self) -> None:
        self.widgets_processing = False
        if not self.image_processing:
            self.processingFinished()

    def _clearThreadpool(self) -> None:
        self.threadpool.clear()
        self.threadpool.waitForDone()

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
                return

        if self.processingGrp.stopBtn.isEnabled():
            self.processingGrp.stopBtn.clicked.emit()

            while self.image_processing:
                QtCore.QCoreApplication.processEvents()

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
            self.widgets_processing = True
            self.imageProcessingFinished()
            self.imageViewWidget.render(image_groups)

            for dup_w in self.imageViewWidget.widgets[-1].widgets:
                dup_w.signals.clicked.connect(self.switchImgActionsAndBtns)
        else:
            msg_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                'No duplicate images found',
                'No duplicate images have been found in the selected folders'
            )
            msg_box.exec()
