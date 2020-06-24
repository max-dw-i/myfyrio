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

Module implementing radio buttons setting the sensitivity of duplicate image
search
'''

from PyQt5 import QtCore, QtWidgets


def checkedRadioButton(widget: QtWidgets.QWidget) -> 'SensitivityRadioButton':
    '''Find and return the checked sensitivity radio button

    :param widget: widget to search for the radio button in,
    :return: checked SensitivityRadioButton,
    :raise ValueError: :widget: does not contain any SensitivityRadioButton,
                       does not contain any checked SensitivityRadioButton
                       or contains more than one SensitivityRadioButton
    '''

    buttons = widget.findChildren(SensitivityRadioButton)
    if not buttons:
        err_msg = ('The passed widget does not contain '
                   'any SensitivityRadioButton')
        raise ValueError(err_msg)

    checked = None
    for btn in buttons:
        if btn.isChecked():
            if checked is not None:
                err_msg = ('The passed widget contains more than one '
                           'checked SensitivityRadioButton')
                raise ValueError(err_msg)

            checked = btn

    if checked is None:
        err_msg = ('The passed widget does not contain '
                   'any checked SensitivityRadioButton')
        raise ValueError(err_msg)

    return checked


class SensitivityRadioButton(QtWidgets.QRadioButton):
    '''Widget setting the sensitivity of duplicate image search.
    The sensitivity value is used as the threshold. If the difference
    between two images are greater than the sensitivity, the images
    are not duplicates (similar), and otherwise

    :param parent:              widget's parent (optional),

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
