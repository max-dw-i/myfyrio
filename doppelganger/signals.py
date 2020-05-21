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


class ImageProcessingSignals(QtCore.QObject):
    '''Supported signals:
    ------------------
    :signal update_info:        label to update: str, text to set: str,
    :signal update_progressbar: new value of progress bar: float,
    :signal image_groups:       list of image groups: List[Group],
    :signal error:              error: str,
    :signal interrupted:        image processing has been interrupted by user
    '''

    update_info = QtCore.pyqtSignal(str, str)
    update_progressbar = QtCore.pyqtSignal(float)
    image_groups = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)
    interrupted = QtCore.pyqtSignal()


class ThumbnailsProcessingSignals(QtCore.QObject):
    '''Supported signals:
    ------------------
    :signal finished:          image thumbnail is made and assigned to
                               attribute "thumb" of the "Image" object
    '''

    finished = QtCore.pyqtSignal()


class WidgetsRenderingSignals(QtCore.QObject):
    '''Supported signals:
    ------------------
    :signal update_progressbar: new value of progress bar: float,
    :signal finished:           widgets rendering has been finished,
    :signal interrupted:        widgets rendering has been interrupted by user
    '''

    update_progressbar = QtCore.pyqtSignal(float)
    finished = QtCore.pyqtSignal()
    interrupted = QtCore.pyqtSignal()


class DuplicateWidgetSignals(QtCore.QObject):
    '''Supported signals:
    ------------------
    :signal clicked:            "DuplicateWidget" has been clicked
    '''

    clicked = QtCore.pyqtSignal()
