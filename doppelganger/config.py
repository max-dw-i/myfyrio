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

Module implementing config containing programme's preferences
'''

import os
import pickle
from collections import UserDict

###############################Types##############################

ConfFile = str                  # Path to the cache file

##################################################################


class Config(UserDict):
    '''Represent config containing programme's preferences. The config is a
    dictionary with the keys:

        size:               int - size (width or height) of image thumbnails,
        show_similarity:    bool - show (or not) the similarity rates
                            of duplicate images,
        show_size:          bool - show (or not) the sizes of duplicate images,
        show_path:          bool - show (or not) the paths of duplicate images,
        sort:               int - sorting type (duplicate images in every group
                            can be sorted),
        delete_dirs:        bool - delete (or not) empty directories when
                            duplicate images are moved or deleted,
        size_format:        int - duplicate image size format (bytes,
                            kilobytes...),
        subfolders:         bool - search through the directories recursively
                            (or not),
        close_confirmation: bool - ask the user confirmation when he/she
                            closes the programme,
        filter_img_size:    bool - search for duplicate images only among
                            the images with the specific width and height,
        min_width:          int - if "filter_img_size" is True, the min width
                            of images,
        max_width:          int - if "filter_img_size" is True, the max width
                            of images,
        min_height:         int - if "filter_img_size" is True, the min height
                            of images,
        max_height:         int - if "filter_img_size" is True, the max height
                            of images,
        cores:              int - number of CPU cores to use,
        lazy:               bool - use lazy thumbnail loading (or not),
        sensitivity:        int - threshold used when images are compared to
                            find out whether they are similar or not

    The dictionary is kept in the attribute "data"
    '''

    def _default(self) -> None:
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
            'filter_img_size': False,
            'min_width': 0,
            'max_width': 1000000,
            'min_height': 0,
            'max_height': 1000000,
            'cores': os.cpu_count() or 1,
            'lazy': False,
            'sensitivity': 0
        }

        self.data = DEFAULT_CONFIG.copy() # pylint: disable=attribute-defined-outside-init

    def save(self, file: ConfFile) -> None:
        '''Save data with preferences into the config file

        :param file:    path to the config file,
        :raise OSError: something went wrong during saving attempt
        '''

        try:
            with open(file, 'wb') as f:
                pickle.dump(self.data, f)
        except OSError as e:
            raise OSError(e)

    def load(self, file: ConfFile) -> None:
        '''Load the config file. If the file does not exist yet (or any
        other exception is raised), load the default config

        :param file:    path to the config file,
        :raise OSError: something went wrong during loading attempt
        '''

        try:
            with open(file, 'rb') as f:
                self.data = pickle.load(f) # pylint: disable=attribute-defined-outside-init
        except FileNotFoundError as e:
            self._default()
        except (EOFError, OSError, pickle.UnpicklingError) as e:
            self._default()
            raise OSError(e)
