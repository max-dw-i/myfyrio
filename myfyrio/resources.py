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

from myfyrio import metadata as md

################################## Types ######################################
RelativePath = str      # Path relative to the programme's root directory
AbsolutePath = str      # Absolute path in the file system
ByteResource = BytesIO  # Resource as bytes
QtResourcePath = str    # Path to a resource in Qt resource system format
###############################################################################

# Change to True if the app is installed system-widely (in particular, if the
# user does not have permissions to write into the programme's directory) so
# a user-specific directory is used
USER = False


class Resource(Enum):
    '''Enum implementing a convenient way of getting a resource'''

    def nonfrozen(self) -> AbsolutePath:
        '''Return the absolute path to the resource for the non-frozen
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

    ICON = 'myfyrio/static/images/myfyrio.png'

    ERR_IMG = 'myfyrio/static/images/error.png'

    def frozen(self) -> QtResourcePath:
        '''Return the path to the image in Qt resource system format'''

        return ':/' + self.value


class License(Resource):
    '''Represent files with license and copyright information'''

    COPYRIGHT = 'COPYRIGHT'
    LICENSE = 'LICENSE'

    def nonfrozen(self) -> AbsolutePath:
        '''Return the path to the license/copyright file if the executable
        is not frozen
        '''

        site_packages_dir = pathlib.Path(__file__).parents[1]
        dist_info_dir_name = f'{md.NAME.lower()}-{md.VERSION}.dist-info'
        dist_info_dir = site_packages_dir / dist_info_dir_name
        if dist_info_dir.exists(): # installed with 'pip'
            return str(dist_info_dir / self.value)
        return super().nonfrozen()

    def frozen(self) -> AbsolutePath:
        '''Return the path to the license/copyright file if the executable
        is frozen
        '''

        if USER:
            if sys.platform.startswith('linux'):
                license_dir = pathlib.Path(f'/usr/share/doc/{md.NAME.lower()}')
                return str(license_dir / self.value)
        return super().frozen()


class DynamicResource(Resource):
    '''Represent dynamic resources (that are changed at run-time)'''

    def frozen(self) -> AbsolutePath:
        '''Return the user-specific path to the resource if USER == True.
        Otherwise, the usual one (the same directory as the executable's)
        '''

        if USER:
            home_dir = pathlib.Path.home()
            name = md.NAME
            val = self.value
            if sys.platform.startswith('win32'):
                return str(home_dir.joinpath('AppData', 'Local', name, val))
            if sys.platform.startswith('linux'):
                return str(home_dir.joinpath(f'.{name.lower()}', val))
        return super().frozen()


class Config(DynamicResource):
    '''Represent config file'''

    CONFIG = 'config.p'


class Cache(DynamicResource):
    '''Represent cache file'''

    CACHE = 'cache.p'


class Log(DynamicResource):
    '''Represent error log file'''

    ERROR = 'errors.log'
