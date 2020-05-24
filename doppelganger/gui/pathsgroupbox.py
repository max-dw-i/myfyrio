'''Copyright 2020 Maxim Shpak <maxim.shpak@posteo.uk>

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

Module implementing widget allowing to add and remove folder paths
to/from QListWidget
'''

from __future__ import annotations

from typing import List

from PyQt5 import QtCore, QtWidgets, uic

from doppelganger import core
from doppelganger.resources.manager import UI, resource


class MousePressFilter(QtCore.QObject):
    '''Do not allow to choose multiple folders in a MultiSelectionFileDialog
    if "Ctrl" is not pressed and hold
    '''

    def __init__(self, dialog: MultiSelectionFileDialog) -> None:
        super().__init__(parent=dialog)

        self.dialog = dialog

    def eventFilter(self, obj, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                if not self.dialog.ctrl_pressed:
                    # listView and treeView modes point to the same
                    # abstractView so clearing any of them is ok
                    self.dialog.listView.clearSelection()
                    return False
        return False


class CtrlPressFilter(QtCore.QObject):
    '''Assign True to the MultiSelectionFileDialog attribute "ctrl_pressed"
    if "Ctrl" is pressed, False - if "Ctrl" is released
    '''

    def __init__(self, dialog: MultiSelectionFileDialog) -> None:
        super().__init__(parent=dialog)

        self.dialog = dialog

    def eventFilter(self, obj, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Control:
                self.dialog.ctrl_pressed = True
                return True

        elif event.type() == QtCore.QEvent.KeyRelease:
            if event.key() == QtCore.Qt.Key_Control:
                self.dialog.ctrl_pressed = False
                return True

        return False


class MultiSelectionFileDialog(QtWidgets.QFileDialog):
    '''Implement a file dialog with multiple selection. Only folders
    can be chosen. Press and hold "Ctrl" to select more than one folder
    '''

    def __init__(self, parent: QtWidgets.QWidget = None, caption: str = '',
                 directory: str = '') -> None:
        super().__init__(parent=parent, caption=caption, directory=directory)

        self.ctrl_pressed = False

        self.setFileMode(QtWidgets.QFileDialog.Directory)
        self.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog
                        | QtWidgets.QFileDialog.ReadOnly)

        self._setViewModes()

    def _setViewModes(self) -> None:
        self.listView = self.findChild(QtWidgets.QListView, 'listView')
        self.treeView = self.findChild(QtWidgets.QTreeView)

        for mode in [self.listView, self.treeView]:
            mode.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

            viewport = mode.viewport()
            mouseFilter = MousePressFilter(self)
            viewport.installEventFilter(mouseFilter)

            ctrlFilter = CtrlPressFilter(self)
            mode.installEventFilter(ctrlFilter)

class PathsGroupBox(QtWidgets.QGroupBox):
    '''Widget implementing adding and removing folder
    paths to/from QListWidget
    '''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        uic.loadUi(resource(UI.PATHS), self)

        self.addFolderBtn.clicked.connect(self.addPath)
        self.delFolderBtn.clicked.connect(self.delPath)
        self.pathsList.itemSelectionChanged.connect(self._enableDelFolderBtn)

    def paths(self) -> List[core.FolderPath]:
        '''Return all the folders the user added to "pathsList"

        :return: list with folder paths
        '''

        return [self.pathsList.item(i).text()
                for i in range(self.pathsList.count())]

    def _enableDelFolderBtn(self) -> None:
        if self.pathsList.selectedItems():
            self.delFolderBtn.setEnabled(True)
        else:
            self.delFolderBtn.setEnabled(False)

    def addPath(self) -> None:
        '''Open "QFileDialog" to choose folders and add them to the widget'''

        dialog = MultiSelectionFileDialog(self, 'Open Folders', '')
        if dialog.exec():
            for path in dialog.selectedFiles():
                if not self.pathsList.findItems(path, QtCore.Qt.MatchExactly):
                    self.pathsList.addItem(path)

    def delPath(self) -> None:
        '''Delete the chosen folders from the widget'''

        for item in self.pathsList.selectedItems():
            self.pathsList.takeItem(self.pathsList.row(item))
