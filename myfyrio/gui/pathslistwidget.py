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

Module implementing widget viewing the folders to search for images in
'''

from typing import List

from PyQt5 import QtCore, QtWidgets

from myfyrio import core
from myfyrio.gui import multiselectionfiledialog


class PathsListWidget(QtWidgets.QListWidget):
    '''Widget viewing the folders to search for images in

    :param parent:          widget's parent (optional),

    :signal hasSelection:   True - any path in the widget is selected,
                            False - otherwise, emitted when the selection
                            is changed,
    :signal hasItems:       True - the widget has items (paths),
                            False - otherwise, emitted when an item (path)
                            is added or removed
    '''

    hasSelection = QtCore.pyqtSignal(bool)
    hasItems = QtCore.pyqtSignal(bool)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent=parent)

        self._setSignals()

    def _setSignals(self) -> None:
        model = self.model()
        model.rowsInserted.connect(self._hasItems)
        model.rowsRemoved.connect(self._hasItems)

        self.itemSelectionChanged.connect(self._hasSelectedItems)

    def _hasSelectedItems(self) -> None:
        if self.selectedItems():
            self.hasSelection.emit(True)
        else:
            self.hasSelection.emit(False)

    def _hasItems(self) -> None:
        if self.count():
            self.hasItems.emit(True)
        else:
            self.hasItems.emit(False)

    def paths(self) -> List[core.FolderPath]:
        '''Return all the folders the user added to the widget

        :return: list with the folder paths
        '''

        return [self.item(i).text() for i in range(self.count())]

    def addPath(self) -> None:
        '''Open "MultiSelectionFileDialog" to choose folders
        and add them to the widget
        '''

        dialog = multiselectionfiledialog.MultiSelectionFileDialog(
            self, 'Open Folders', ''
        )
        if dialog.exec():
            for path in dialog.selectedFiles():
                if not self.findItems(path, QtCore.Qt.MatchExactly):
                    self.addItem(path)

    def delPath(self) -> None:
        '''Delete the chosen folders from the widget'''

        for item in self.selectedItems():
            self.takeItem(self.row(item))
