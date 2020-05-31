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

Module implementing radio buttons setting the sensitivity of duplicate image
search
'''

from PyQt5 import QtCore, QtWidgets


class SensitivityRadioButton(QtWidgets.QRadioButton):
    '''Widget setting the sensitivity of duplicate image search.
    The sensitivity value is used as the threshold. If the difference
    between two images are greater than the sensitivity, the images
    are not duplicates (similar), and otherwise

    :signal sensitivityChanged: return the new sensitivity value: int,
                                emitted when the widget is activated
                                (clicked)
    '''

    sensitivityChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent=parent)

        self.sensitivity = 0

        self._setSignals()

    def _setSignals(self) -> None:
        self.clicked.connect(self._emitSensitivity)

    def _emitSensitivity(self) -> None:
        self.sensitivityChanged.emit(self.sensitivity)


class VeryHighRadioButton(SensitivityRadioButton):
    '''Very high sensitivity radio button. Sensitivity value is 0'''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent=parent)

        self.sensitivity = 0


class HighRadioButton(SensitivityRadioButton):
    '''High sensitivity radio button. Sensitivity value is 5'''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent=parent)

        self.sensitivity = 5


class MediumRadioButton(SensitivityRadioButton):
    '''Medium sensitivity radio button. Sensitivity value is 10'''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent=parent)

        self.sensitivity = 10


class LowRadioButton(SensitivityRadioButton):
    '''Low sensitivity radio button. Sensitivity value is 15'''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent=parent)

        self.sensitivity = 15


class VeryLowRadioButton(SensitivityRadioButton):
    '''Very low sensitivity radio button. Sensitivity value is 20'''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent=parent)

        self.sensitivity = 20
