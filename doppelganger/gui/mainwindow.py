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

Module implementing the main window
'''

from typing import List

from PyQt5 import QtCore, QtGui, QtWidgets, uic

from doppelganger import resources, workers
from doppelganger.gui.aboutwindow import AboutWindow
from doppelganger.gui.errornotifier import errorMessage
from doppelganger.gui.preferenceswindow import PreferencesWindow
from doppelganger.gui.sensitivityradiobutton import checkedRadioButton


class MainWindow(QtWidgets.QMainWindow):
    '''Main GUI class'''

    def __init__(self) -> None:
        super().__init__()

        main_ui = resources.UI.MAIN.abs_path # pylint: disable=no-member
        uic.loadUi(main_ui, self)

        icon = resources.Image.ICON.abs_path # pylint: disable=no-member
        app_icon = QtGui.QIcon(icon)
        self.setWindowIcon(app_icon)

        self.aboutWindow = AboutWindow(self)
        self.preferencesWindow = PreferencesWindow(self)

        self._errors: List[str] = []

        self.threadpool = QtCore.QThreadPool.globalInstance()

        # If the "centralWidget" layout margins are set in the .ui file,
        # it does not work for some reason
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)

        self._setImageViewWidget()
        self._setFolderPathsGroupBox()
        self._setImageProcessingGroupBox()
        self._setSensitivityGroupBox()
        self._setActionsGroupBox()
        self._setMenubar()

    def _setImageViewWidget(self) -> None:
        self.imageViewWidget.conf = self.preferencesWindow.conf

        self.imageViewWidget.updateProgressBar.connect(
            self.processProg.setValue
        )

        self.imageViewWidget.finished.connect(self.processProg.setMaxValue)
        self.imageViewWidget.finished.connect(self.stopBtn.disable)
        self.imageViewWidget.finished.connect(self.startBtn.finished)
        self.imageViewWidget.finished.connect(
            lambda: (self.autoSelectBtn.enable()
                     if self.imageViewWidget.widgets
                     else self.autoSelectBtn.disable())
        )
        self.imageViewWidget.finished.connect(
            lambda: (self.menubar.enableAutoSelectAction()
                     if self.imageViewWidget.widgets
                     else self.menubar.disableAutoSelectAction())
        )
        self.imageViewWidget.finished.connect(
            lambda: errorMessage(self._errors)
        )

        self.imageViewWidget.error.connect(self._errors.append)

        self.imageViewWidget.selected.connect(self.moveBtn.setEnabled)
        self.imageViewWidget.selected.connect(self.deleteBtn.setEnabled)
        self.imageViewWidget.selected.connect(self.unselectBtn.setEnabled)
        self.imageViewWidget.selected.connect(self.moveAction.setEnabled)
        self.imageViewWidget.selected.connect(self.deleteAction.setEnabled)
        self.imageViewWidget.selected.connect(self.unselectAction.setEnabled)

    def _setFolderPathsGroupBox(self) -> None:
        self.pathsList.hasSelection.connect(self.delFolderBtn.setEnabled)
        self.pathsList.hasSelection.connect(self.delFolderAction.setEnabled)

        self.pathsList.hasItems.connect(self.startBtn.switch)

        self.addFolderBtn.clicked.connect(self.pathsList.addPath)
        self.delFolderBtn.clicked.connect(self.pathsList.delPath)

    def _setImageProcessingGroupBox(self) -> None:
        self.processProg.setMinimum(workers.ImageProcessing.PROG_MIN)
        self.processProg.setMaximum(workers.ImageProcessing.PROG_MAX)

        self.startBtn.clicked.connect(self._errors.clear)

        self.startBtn.clicked.connect(self.imageViewWidget.clear)

        self.startBtn.clicked.connect(self.processProg.setMinValue)

        self.startBtn.clicked.connect(self.loadedPicLbl.clear)
        self.startBtn.clicked.connect(self.foundInCacheLbl.clear)
        self.startBtn.clicked.connect(self.calculatedLbl.clear)
        self.startBtn.clicked.connect(self.duplicatesLbl.clear)
        self.startBtn.clicked.connect(self.groupsLbl.clear)

        self.startBtn.clicked.connect(self.startBtn.started)
        self.startBtn.clicked.connect(self.stopBtn.enable)

        self.startBtn.clicked.connect(self.autoSelectBtn.disable)
        self.startBtn.clicked.connect(self.menubar.disableAutoSelectAction)

        self.startBtn.clicked.connect(self._startProcessing)

        self.stopBtn.clicked.connect(self.stopBtn.disable)

    def _setSensitivityGroupBox(self) -> None:
        current_sensitivity = checkedRadioButton(self).sensitivity
        self.preferencesWindow.setSensitivity(current_sensitivity)

        self.veryHighRbtn.sensitivityChanged.connect(
            self.preferencesWindow.setSensitivity
        )
        self.highRbtn.sensitivityChanged.connect(
            self.preferencesWindow.setSensitivity
        )
        self.mediumRbtn.sensitivityChanged.connect(
            self.preferencesWindow.setSensitivity
        )
        self.lowRbtn.sensitivityChanged.connect(
            self.preferencesWindow.setSensitivity
        )
        self.veryLowRbtn.sensitivityChanged.connect(
            self.preferencesWindow.setSensitivity
        )

    def _setActionsGroupBox(self) -> None:
        self.moveBtn.clicked.connect(self.imageViewWidget.move)
        self.deleteBtn.clicked.connect(self.imageViewWidget.delete)

        self.autoSelectBtn.clicked.connect(self.imageViewWidget.autoSelect)
        self.unselectBtn.clicked.connect(self.imageViewWidget.unselect)

    def _setMenubar(self) -> None:
        # 'File' menu
        self.addFolderAction.triggered.connect(self.pathsList.addPath)
        self.delFolderAction.triggered.connect(self.pathsList.delPath)

        preferencesWindow = QtCore.QVariant(self.preferencesWindow)
        self.preferencesAction.setData(preferencesWindow)
        self.preferencesAction.triggered.connect(self.menubar.openWindow)

        self.exitAction.triggered.connect(self.close)

        # 'Edit' menu
        self.moveAction.triggered.connect(self.imageViewWidget.move)
        self.deleteAction.triggered.connect(self.imageViewWidget.delete)

        self.autoSelectAction.triggered.connect(
            self.imageViewWidget.autoSelect
        )
        self.unselectAction.triggered.connect(self.imageViewWidget.unselect)

        # 'Help' menu
        self.docsAction.triggered.connect(self.menubar.openDocs)
        self.homePageAction.triggered.connect(self.menubar.openDocs)

        aboutWindow = QtCore.QVariant(self.aboutWindow)
        self.aboutAction.setData(aboutWindow)
        self.aboutAction.triggered.connect(self.menubar.openWindow)

    def _startProcessing(self):
        conf = self.preferencesWindow.conf
        p = workers.ImageProcessing(self.pathsList.paths(), conf)

        p.images_loaded.connect(self.loadedPicLbl.updateNumber)
        p.found_in_cache.connect(self.foundInCacheLbl.updateNumber)
        p.hashes_calculated.connect(self.calculatedLbl.updateNumber)
        p.duplicates_found.connect(self.duplicatesLbl.updateNumber)
        p.groups_found.connect(self.groupsLbl.updateNumber)

        p.update_progressbar.connect(self.processProg.setValue)
        p.image_group.connect(self.imageViewWidget.render,
                              QtCore.Qt.BlockingQueuedConnection)
        p.error.connect(self._errors.append)
        p.interrupted.connect(self.startBtn.finished)
        p.interrupted.connect(self.stopBtn.disable)
        p.interrupted.connect(lambda: errorMessage(self._errors))

        self.imageViewWidget.interrupted.connect(p.interrupt)
        self.stopBtn.clicked.connect(p.interrupt)

        worker = workers.Worker(p.run)
        self.threadpool.start(worker)

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

        if self.stopBtn.isEnabled():
            self.stopBtn.clicked.emit()

        QtCore.QCoreApplication.processEvents()
        self.threadpool.clear()
        self.threadpool.waitForDone()
