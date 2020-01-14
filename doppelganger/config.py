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

Module implementing saving/loading programme's preferences to/from
a config file
'''

import pickle
from typing import Any, Dict, Optional

###############################Types##############################

Param = str
Value = Any
Conf = Dict[Param, Value] # preferences

##################################################################


class Config:
    '''Represent "config" containing programme's preferences'''

    def __init__(self, data: Optional[Conf] = None) -> None:
        if data is None:
            self.default()
        else:
            self.data = data

    def default(self) -> None:
        '''Load default preferences'''

        DEFAULT_CONFIG = {
            'size': 200,
            'show_similarity': True,
            'show_size': True,
            'show_path': True,
            'sort': 0,
            'delete_dirs': False,
            'size_format': 1,
            'subfolders': True,
            'close_confirmation': False,
        }

        self.data = DEFAULT_CONFIG.copy()

    def save(self) -> None:
        '''Save data with preferences into file "config.p"

        :raise OSError: if something goes wrong during
                        "config.p" saving attempt
        '''

        try:
            with open('config.p', 'wb') as f:
                pickle.dump(self.data, f)
        except OSError as e:
            raise OSError(e)

    def load(self) -> None:
        '''Load file "config.p". If the file does not
        exist yet, load default config

        :raise OSError: if something goes wrong during
                        "config.p" loading attempt
        '''

        try:
            with open('config.p', 'rb') as f:
                self.data = pickle.load(f)
        except FileNotFoundError as e:
            self.default()
        except (EOFError, OSError, pickle.UnpicklingError) as e:
            raise OSError(e)
