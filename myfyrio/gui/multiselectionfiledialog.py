'''Copyright 2020 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Myfyrio.

Myfyrio is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Myfyrio is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Myfyrio. If not, see <https://www.gnu.org/licenses/>.

-------------------------------------------------------------------------------

Module implementing multiple selection file dialog
'''

from PyQt5 import QtCore, QtWidgets


class MousePressFilter(QtCore.QObject):
    '''Do not allow to choose multiple folders in a MultiSelectionFileDialog
    if "Ctrl" is not pressed and hold
    '''

    def __init__(self, dialog: 'MultiSelectionFileDialog') -> None:
        super().__init__(parent=dialog)

        self._dialog = dialog

    def eventFilter(self, obj, event: QtCore.QEvent) -> bool: # pylint: disable=unused-argument
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                if not self._dialog._ctrl_pressed:
                    # listView and treeView modes point to the same
                    # abstractView so clearing any of them is ok
                    self._dialog.listView.clearSelection()
                    return False
        return False


class CtrlPressFilter(QtCore.QObject):
    '''Assign True to the MultiSelectionFileDialog attribute "_ctrl_pressed"
    if "Ctrl" is pressed, False - if "Ctrl" is released
    '''

    def __init__(self, dialog: 'MultiSelectionFileDialog') -> None:
        super().__init__(parent=dialog)

        self._dialog = dialog

    def eventFilter(self, obj, event: QtCore.QEvent) -> bool: # pylint: disable=unused-argument
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Control:
                self._dialog._ctrl_pressed = True
                return True

        elif event.type() == QtCore.QEvent.KeyRelease:
            if event.key() == QtCore.Qt.Key_Control:
                self._dialog._ctrl_pressed = False
                return True

        return False


class MultiSelectionFileDialog(QtWidgets.QFileDialog):
    '''Implement a file dialog with multiple selection. Only folders
    can be chosen. Press and hold "Ctrl" to select more than one folder

    :param parent:      widget's parent (optional),
    :param caption:     dialog's caption (optional),
    :param directory:   directory opened by default (optional)
    '''

    def __init__(self, parent: QtWidgets.QWidget = None, caption: str = '',
                 directory: str = '') -> None:
        super().__init__(parent=parent, caption=caption, directory=directory)

        self._ctrl_pressed = False

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
