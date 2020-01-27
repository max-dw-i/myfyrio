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

from typing import List

from PyQt5 import QtWidgets, uic

from doppelganger import core
from doppelganger.resources.paths import PATHS_UI, resource_path


class PathsGroupBox(QtWidgets.QGroupBox):
    '''Widget implementing adding and removing folder
    paths to/from QListWidget
    '''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        uic.loadUi(resource_path(PATHS_UI), self)

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
        '''Open "QFileDialog" to choose a folder and add it to the widget'''

        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if folder_path:
            self.pathsList.addItem(folder_path)

    def delPath(self) -> None:
        '''Delete the chosen folders from the widget'''

        for item in self.pathsList.selectedItems():
            self.pathsList.takeItem(self.pathsList.row(item))
