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
from enum import Enum

################################## Types ######################################
RelativePath = str  # Path relative to the programme's root directory
AbsolutePath = str  # Absolute path
###############################################################################


class Resource(Enum):
    '''Enum implementing a convenient way of getting the resource path'''

    def __init__(self, rel_path: RelativePath) -> None:
        self._rel_path = rel_path

    @property
    def abs_path(self) -> AbsolutePath:
        return str(pathlib.Path(__file__).parents[1] / self._rel_path)


class UI(Resource):
    '''Enum class representing .ui files and the paths to them'''

    ABOUT = 'myfyrio/static/ui/aboutwindow.ui'
    MAIN = 'myfyrio/static/ui/mainwindow.ui'
    PREFERENCES = 'myfyrio/static/ui/preferenceswindow.ui'


class Image(Resource):
    '''Enum class representing images and the paths to them'''

    ICON = 'myfyrio/static/images/icon.png'
    ERR_IMG = 'myfyrio/static/images/error.png'


class Config(Resource):
    '''Enum class representing config file and the path to it'''

    CONFIG = 'config.p'


class Cache(Resource):
    '''Enum class representing cache file and the path to it'''

    CACHE = 'cache.p'


class Log(Resource):
    '''Enum class representing error log file and the path to it'''

    ERROR = 'errors.log'
