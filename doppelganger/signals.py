'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

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

Module implementing custom signals
'''

from PyQt5 import QtCore


class Signals(QtCore.QObject):
    '''Supported signals:
    ------------------
    :signal update_info:        label to update: str, text to set: str,
    :signal update_progressbar: new value of progress bar: float,
    :signal error:              error: str,
    :signal result:             groups of duplicate images: List[core.Group],
    :signal finished:           processing is done,
    :signal interrupted:        image processing must be stopped,
    :signal clicked:            DuplicateWidget is clicked
    '''

    update_info = QtCore.pyqtSignal(str, str)
    update_progressbar = QtCore.pyqtSignal(float)
    error = QtCore.pyqtSignal(str)
    result = QtCore.pyqtSignal(list)
    finished = QtCore.pyqtSignal()
    interrupted = QtCore.pyqtSignal()
    clicked = QtCore.pyqtSignal()
