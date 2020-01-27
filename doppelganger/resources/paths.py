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

Module containing paths of the resources
'''

import pathlib

ABOUT_UI = 'ui/aboutwindow.ui'
ACTIONS_UI = 'ui/actionsgroupbox.ui'
MAIN_UI = 'ui/mainwindow.ui'
PATHS_UI = 'ui/pathsgroupbox.ui'
PREFERENCES_UI = 'ui/preferenceswindow.ui'
PROCESSING_UI = 'ui/processinggroupbox.ui'
SENSITIVITY_UI = 'ui/sensitivitygroupbox.ui'

ICON = 'images/icon.png'
ERR_IMG = 'images/image_error.png'

def resource_path(relative_path: str) -> str:
    '''Return absolute path to resource

    :param relative_path: relative path
    :return: absolute path
    '''

    return str(pathlib.Path(__file__).parent / relative_path)
