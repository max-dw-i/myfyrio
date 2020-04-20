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
from typing import Dict

from doppelganger.core import Hash, ImagePath

########################## Types ##################################

CacheFile = str # Path to the cache file

###################################################################


class Cache:
    '''Represent "cache" containing image hashes. Cache is a dictionary with
    pairs "ImagePath: Hash". Cache is empty when a new instance is created
    '''

    def __init__(self) -> None:
        self._data: Dict[ImagePath, Hash] = {}

    def load(self, file: CacheFile):
        '''Load the cache with earlier calculated hashes

        :param file: path to the cache file,
        :raise FileNotFoundError: cache file does not exist,
        :raise EOFError: cache file might be corrupted (or empty),
        :raise OSError: some problem while opening cache file
        '''

        try:
            with open(file, 'rb') as f:
                cache = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f'Cache file at {file} does not exist')
        except EOFError:
            raise EOFError('The cache file might be corrupted (or empty)')
        except OSError as e:
            raise OSError(e)
        else:
            self._data = cache

    def save(self, file: CacheFile) -> None:
        '''Save cache on the disk

        :param file: path to the cache file,
        :raise OSError: some problem while saving cache file
        '''

        try:
            with open(file, 'wb') as f:
                pickle.dump(self._data, f)
        except OSError as e:
            raise OSError(e)

    def update(self, new_hashes: Dict[ImagePath, Hash]):
        '''Update the cache with new hashes

        :param new_hashes: dict with pairs "ImagePath: Hash"
        '''

        self._data.update(new_hashes)

    def __contains__(self, path: ImagePath) -> bool:
        if path in self._data:
            return True
        return False

    def __getitem__(self, path: ImagePath) -> Hash:
        if path not in self._data:
            raise KeyError(f'Path "{path}" is not in cache')
        return self._data[path]

    def __setitem__(self, path: ImagePath, image_hash: Hash) -> None:
        self._data[path] = image_hash
