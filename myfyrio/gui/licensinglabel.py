'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

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

Module implementing widget that represents the 'Licensing information' label
'''


import pathlib
import subprocess
import sys
from typing import TYPE_CHECKING

from PyQt5 import QtWidgets

from myfyrio import resources
from myfyrio.gui import errornotifier, utils
from myfyrio.logger import Logger

if TYPE_CHECKING:
    from PyQt5 import QtGui


logger = Logger.getLogger('licensinglabel')


class LicensingLabel(QtWidgets.QLabel):
    '''Widget viewing a duplicate image and all info about it (its similarity
    rate, size and path)
    '''

    @staticmethod
    def _openLicensesDir() -> None:
        license_file = resources.License.LICENSE.get() # pylint:disable=no-member
        license_dir = pathlib.Path(license_file).parent

        try:
            utils.openFile(license_dir)

        except subprocess.CalledProcessError:
            err_msg = f"Something went wrong while opening '{license_dir}'"
            logger.exception(err_msg)
            # Crazy hack: on Windows, for some reason, 'explorer's exit code
            # is 1, even though the directory is opened in the file manager, so
            # we do not show the error message to the user
            if not sys.platform.startswith('win'):
                errornotifier.errorMessage([err_msg])

    def mouseReleaseEvent(self, event: 'QtGui.QMouseEvent') -> None:
        self._openLicensesDir()

        event.ignore()
