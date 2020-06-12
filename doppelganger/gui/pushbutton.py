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


class StartButton(PushButton):
    '''Special widget for the button "Start" since the button state depends on
    whether there are any paths in the "pathsList" widget or not

    :param parent: widget's parent (optional)
    '''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent=parent)

        self._run = False
        self._paths = False

    def started(self) -> None:
        '''Run when the "Start" button has been pressed. Disable the button'''

        super().disable()
        self._run = True

    def finished(self) -> None:
        '''Run when the image processing has been finished. Enable the button
        if there are any paths in the "pathsList" widget
        '''

        if self._paths:
            super().enable()

        self._run = False

    def switch(self, paths: bool) -> None:
        '''Connect to the "hasItems" signal of the "pathsList" widget.
        Enable the button if there are any paths in the "pathsList" widget
        and image processing is not in progress, disable - there are no paths
        in the "pathsList" widget and image processing is not in progress.
        If image processing is in progress, do nothing
        '''

        self._paths = paths

        if not self._run:
            if paths:
                super().enable()
            else:
                super().disable()
