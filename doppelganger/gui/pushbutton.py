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

Module implementing modified version of QPushButton widget
'''

from PyQt5 import QtWidgets


class PushButton(QtWidgets.QPushButton):
    '''Modified version of QPushButton widget that has methods enabling and
    disabling buttons without passing any arguments (quite useful when signals
    without parameters are used)
    '''

    def enable(self) -> None:
        self.setEnabled(True)

    def disable(self) -> None:
        self.setEnabled(False)
