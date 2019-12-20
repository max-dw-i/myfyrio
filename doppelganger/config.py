'''Copyright 2019 Maxim Shpak <maxim.shpak@posteo.uk>

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

import logging
import pickle
from typing import Any, Dict, Optional


config_logger = logging.getLogger('main.config')

###############################Types##############################

Param = str
Value = Any
ConfigData = Dict[Param, Value] # preferences

##################################################################


class Config:
    '''Represent 'config' containing programme's preferences'''

    DEFAULT_CONFIG_DATA = {
        'size': 200,
        'show_similarity': True,
        'show_size': True,
        'show_path': True,
        'sort': 0,
        'delete_dirs': False,
        'size_format': 'KB',
        'subfolders': True,
    }

    def __init__(self, data: Optional[ConfigData] = None) -> None:
        if data is None:
            self.data = self.DEFAULT_CONFIG_DATA.copy()
        else:
            self.data = data

    def save(self) -> None:
        """Save data with preferences into file 'config.p'

        :raise OSError: if something goes wrong during
                        'config.p' saving attempt
        """

        try:
            with open('config.p', 'wb') as f:
                pickle.dump(self.data, f)
        except OSError as e:
            config_logger.error(e)
            raise OSError(e)

    def load(self) -> None:
        """Load file 'config.p'. If something went wrong
        while loading 'config.p', the default data is loaded

        :raise OSError: if something goes wrong during
                        'config.p' loading attempt
        """

        try:
            with open('config.p', 'rb') as f:
                self.data = pickle.load(f)
        except FileNotFoundError as e:
            self.data = self.DEFAULT_CONFIG_DATA.copy()
        except (EOFError, OSError, pickle.UnpicklingError) as e:
            config_logger.error(e)
            self.data = self.DEFAULT_CONFIG_DATA.copy()
            raise OSError(e)
