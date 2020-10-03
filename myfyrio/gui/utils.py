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

Module implementing functions-helpers used by different parts of the GUI
subsystem
'''

import subprocess
import sys
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    import pathlib

################################## Types ######################################
FilePath = Union['pathlib.Path', str] # Path to a file/directory
###############################################################################


def openFile(path: FilePath) -> None:
    '''Open :path: in the OS default viewer (image viewer, file manager,
    etc.)

    :param path:                            path to a file/directory,
    :raise subprocess.CalledProcessError:   something went wrong while opening
                                            a file/directory
    '''

    if sys.platform.startswith('linux'):
        command = 'xdg-open'
    elif sys.platform.startswith('win32'):
        command = 'explorer'
    elif sys.platform.startswith('darwin'):
        command = 'open'
    else:
        command = 'Unknown platform'

    subprocess.run([command, str(path)], check=True)
