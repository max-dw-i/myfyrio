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

This module provides an example of using the 'Doppelgänger' core features
'''

import pathlib

from doppelganger import core

print('This is a demonstration of finding duplicate (similar) images')
print('It might take some time, Be patient')
print('------------------------')

msg = 'Type the path of the folder you want to find duplicate images in\n'
folders = input(msg)
msg = ('Type the searching sensitivity (a value '
       'between 0 and 20 is recommended)\n')
sensitivity = input(msg)
msg = ('Type the path of the folder you want to save the cache file in. '
       'Press "Enter" if you want to save it in the working directory\n')
cache_folder = input(msg)
if cache_folder:
    cache_file = str(pathlib.Path(cache_folder) / 'cache.p')
else:
    cache_file = 'cache.p'
print('------------------------')
print('Searching images in the folder...')
paths = set(core.find_image([folders]))
print(f'There are {len(paths)} images in the folder')

cache = core.load_cache(cache_file)
not_cached = core.check_cache(paths, cache)
print(f'{len(paths)-len(not_cached)} images have been found in the cache')

print('Starting to calculate hashes...')
if not_cached:
    hashes = list(core.calculate_hashes(not_cached))
    cache = core.extend_cache(cache, not_cached, hashes)
    core.save_cache(cache_file, cache)
print('All the hashes have been calculated')

images = [core.Image(path, cache[path]) for path in paths if path in cache]

print('Starting to compare images...')
image_groups = list(core.image_grouping(images, int(sensitivity)))[-1]
print(f'{len(image_groups)} duplicate image groups have been found')

print('Sorting the images by similarity rate in descending order...')
s = core.Sort(image_groups)
s.sort()
print('Done')
print('------------------------')

for i, group in enumerate(image_groups):
    print(f'Group {i+1}:')
    print('------------------------')
    for image in group:
        print(image)
    print('------------------------')

print('That is it')
input('Press any key to continue...')
