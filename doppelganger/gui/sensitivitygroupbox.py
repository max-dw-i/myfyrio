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

Module implementing widget setting sensitivity of duplicate images search

'''

from PyQt5 import QtWidgets, uic

from doppelganger import manager


class SensitivityGroupBox(QtWidgets.QGroupBox):
    '''Widget setting sensitivity of duplicate images search'''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        sens_ui = manager.UI.SENSITIVITY.abs_path # pylint: disable=no-member
        uic.loadUi(sens_ui, self)

        self.veryHighRbtn.clicked.connect(self.setVeryHighSensitivity)
        self.highRbtn.clicked.connect(self.setHighSensitivity)
        self.mediumRbtn.clicked.connect(self.setMediumSensitivity)
        self.lowRbtn.clicked.connect(self.setLowSensitivity)
        self.veryLowRbtn.clicked.connect(self.setVeryLowSensitivity)

        self.sensitivity = 0

    def setVeryHighSensitivity(self) -> None:
        self.sensitivity = 0

    def setHighSensitivity(self) -> None:
        self.sensitivity = 5

    def setMediumSensitivity(self) -> None:
        self.sensitivity = 10

    def setLowSensitivity(self) -> None:
        self.sensitivity = 15

    def setVeryLowSensitivity(self) -> None:
        self.sensitivity = 20
