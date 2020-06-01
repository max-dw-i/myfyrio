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

Module implementing modified version of QProgressBar widget
'''

from PyQt5 import QtWidgets


class ProgressBar(QtWidgets.QProgressBar):
    '''Modified version of QProgressBar widget that has methods for setting
    minimum and maximum values without passing any arguments (quite useful
    when signals without parameters are used)
    '''

    def setMinValue(self) -> None:
        self.setValue(self.minimum())


    def setMaxValue(self) -> None:
        self.setValue(self.maximum())
