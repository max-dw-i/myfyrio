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

        docs_url = 'https://github.com/oratosquilla-oratoria/myfyrio'
        webbrowser.open(docs_url)

    def _autoSelectAction(self) -> QtWidgets.QAction:
        # Since we use Qt Designer to make the GUI and then load .ui file,
        # the menubar actions' parent is the MainWindow and not the menubar.
        # The menubar's parent is also the MainWindow (same reason)
        return self.parent().autoSelectAction

    def enableAutoSelectAction(self) -> None:
        self._autoSelectAction().setEnabled(True)

    def disableAutoSelectAction(self) -> None:
        self._autoSelectAction().setEnabled(False)
