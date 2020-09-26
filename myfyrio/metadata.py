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

Module storing the programme's metadata
'''

import pathlib

NAME = 'Myfyrio'
VERSION = '0.4.1'
DESCRIPTION = 'Application searching for similar/duplicate images'
KEYWORDS = ['image', 'picture', 'photo', 'identical', 'similar', 'duplicate']
AUTHOR = 'Maxim Shpak'
AUTHOR_EMAIL = 'maxim.shpak@posteo.uk'
LICENSE = 'GPLv3'
URL_ABOUT = 'https://github.com/oratosquilla-oratoria/myfyrio/'
URL_BUG_REPORTS = URL_ABOUT + 'issues/'
URL_SOURCE = URL_ABOUT


def long_description():
    readme_file = pathlib.Path(__file__).parents[1] / 'README.md'
    with open(readme_file, 'r') as f:
        return f.read()
