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

Module implementing window "About"
'''

from PyQt5 import QtCore, QtWidgets, uic

from doppelganger import resources


class AboutWindow(QtWidgets.QMainWindow):
    '''Class implementing window "About"'''

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        about_ui = resources.UI.ABOUT.abs_path # pylint: disable=no-member
        uic.loadUi(about_ui, self)

        sizeHint = self.sizeHint()
        self.setMaximumSize(sizeHint)
        self.resize(sizeHint)

        self.setWindowModality(QtCore.Qt.ApplicationModal)
