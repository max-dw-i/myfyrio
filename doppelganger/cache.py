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

Module implementing cache for keeping image hashes
'''

import pickle
from collections import UserDict

########################## Types ##################################
CacheFile = str # Path to the cache file
###################################################################


class Cache(UserDict):
    '''Represent cache containing image hashes. The cache is a dictionary with
    pairs "ImagePath: Hash". The cache is empty when a new instance is created.
    The dictionary is kept in the attribute "data"
    '''

    def load(self, file: CacheFile) -> None:
        '''Load the cache with the earlier calculated hashes

        :param file:                path to the cache file,
        :raise FileNotFoundError:   cache file does not exist,
        :raise EOFError:            cache file might be corrupted (or empty),
        :raise OSError:             some problem while opening cache file
        '''

        try:
            with open(file, 'rb') as f:
                cache = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f'Cache file does not exist')
        except EOFError:
            raise EOFError('Cache file might be corrupted (or empty)')
        except OSError as e:
            raise OSError(e)
        else:
            self.data = cache # pylint: disable=attribute-defined-outside-init

    def save(self, file: CacheFile) -> None:
        '''Save cache on the disk

        :param file:    path to the cache file,
        :raise OSError: some problem while saving cache file
        '''

        try:
            with open(file, 'wb') as f:
                pickle.dump(self.data, f)
        except OSError as e:
            raise OSError(e)
