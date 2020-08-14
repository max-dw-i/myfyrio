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

Module implementing resources managing
'''

import pathlib
import sys
from enum import Enum
from io import BytesIO
from typing import Any

from PyQt5 import QtCore

################################## Types ######################################
RelativePath = str      # Path relative to the programme's root directory
AbsolutePath = str      # Absolute path in the file system
ByteResource = BytesIO  # Resource as bytes
QtResourcePath = str    # Path to a resource in Qt resource system format
###############################################################################


class Resource(Enum):
    '''Enum implementing a convenient way of getting a resource'''

    def nonfrozen(self) -> AbsolutePath:
        '''Return the absolute path of the resource for the non-frozen
        application
        '''

        return str(pathlib.Path(__file__).parents[1] / self.value)

    def frozen(self) -> Any:
        '''Return the resource (as the absolute path, bytes, ...) for
        the frozen application (this, default, implementation returns
        the absolute path of the resource)
        '''

        return str(pathlib.Path(sys.executable).parent / self.value)

    def get(self) -> Any:
        '''Return the resource (for frozen or non-frozen application)'''

        if getattr(sys, 'frozen', False):
            return self.frozen()
        return self.nonfrozen()


class UI(Resource):
    '''Represent '.ui' resources'''

    ABOUT = 'myfyrio/static/ui/aboutwindow.ui'
    MAIN = 'myfyrio/static/ui/mainwindow.ui'
    PREFERENCES = 'myfyrio/static/ui/preferenceswindow.ui'

    def frozen(self) -> ByteResource:
        '''Return the '.ui' file as BytesIO object'''

        ui_file = QtCore.QFile(':/' + self.value)
        ui_file.open(QtCore.QIODevice.ReadOnly)
        data = ui_file.readAll()
        ui_file.close()
        return BytesIO(bytes(data))


class Image(Resource):
    '''Represent image resources'''

    ICON = 'myfyrio/static/images/icon.png'

    ERR_IMG = 'myfyrio/static/images/error.png'

    def frozen(self) -> QtResourcePath:
        '''Return the path of the image in Qt resource system format'''

        return ':/' + self.value


class Config(Resource):
    '''Represent config file'''

    CONFIG = 'config.p'


class Cache(Resource):
    '''Represent cache file'''

    CACHE = 'cache.p'


class Log(Resource):
    '''Represent error log file'''

    ERROR = 'errors.log'
