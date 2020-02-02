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

Module implementing resources managing
'''

from __future__ import annotations

import pathlib
import sys
from enum import Enum
from io import BytesIO
from typing import Union

from PyQt5 import QtCore


def resource(resource: Union[UI, Image]) -> Union[ResourcePath, BytesIO]:
    '''Return absolute path to :resource: or file-like object
    with :resource:

    :param resource: enum object representing resource,
    :return: absolute path or file-like object
    '''

    abs_path = str(pathlib.Path(__file__).parent / resource.value)
    if getattr(sys, 'frozen', False):
        if isinstance(resource, UI):
            # Qt functions understand 'Qt resource' paths, which
            # are used if the programme is bundled, eg. ':/images/icon.png'.
            # Since function 'loadUi' is not a wrapper for the corresponding
            # Qt function, it does not comprehend this kind of path. So we
            # use a Qt function to read the path and convert it to something
            # 'loadUi' can read (in this case, 'BytesIO' object)
            return _ui_file_obj(abs_path)
    return abs_path

def _ui_file_obj(abs_path: ResourcePath) -> BytesIO:
    ui_file = QtCore.QFile(abs_path)
    ui_file.open(QtCore.QIODevice.ReadOnly)
    data = ui_file.readAll()
    ui_file.close()
    return BytesIO(bytes(data))

class UI(Enum):
    '''Enum class representing .ui files and paths to them'''

    ABOUT = 'ui/aboutwindow.ui'
    ACTIONS = 'ui/actionsgroupbox.ui'
    MAIN = 'ui/mainwindow.ui'
    PATHS = 'ui/pathsgroupbox.ui'
    PREFERENCES = 'ui/preferenceswindow.ui'
    PROCESSING = 'ui/processinggroupbox.ui'
    SENSITIVITY = 'ui/sensitivitygroupbox.ui'


class Image(Enum):
    '''Enum class representing images and paths to them'''

    ICON = 'images/icon.png'
    ERR_IMG = 'images/image_error.png'


#################################TYPES##################################
ResourcePath = str # absolute path to the resource
########################################################################
