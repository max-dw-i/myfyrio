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

Module implementing menu bar
'''

import webbrowser

from PyQt5 import QtWidgets


class MenuBar(QtWidgets.QMenuBar):
    '''Implement a custom menu bar'''

    def openWindow(self) -> None:
        '''Open the "Preferences" window or "About" windows'''

        window = self.sender().data()
        if window.isVisible():
            window.activateWindow()
        else:
            window.show()

    def openDocs(self) -> None:
        '''Open the website with the docs'''

        docs_url = 'https://github.com/oratosquilla-oratoria/doppelganger'
        webbrowser.open(docs_url)
