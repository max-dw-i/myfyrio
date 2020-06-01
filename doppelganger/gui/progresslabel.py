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

Module implementing label viewing the progress of duplicate image finding
'''

from PyQt5 import QtWidgets


class ProgressLabel(QtWidgets.QLabel):
    '''Label viewing the progress of duplicate image finding'''

    def clear(self) -> None:
        '''Clear the label (set 0 as the number)'''

        self.updateNumber(0)

    def updateNumber(self, number: int) -> None:
        '''Update the number in the text of the label

        :param number: number to set
        '''

        text = self.text().split(' ')
        text[-1] = str(number)
        self.setText(' '.join(text))
