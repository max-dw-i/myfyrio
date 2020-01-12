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


This file incorporates work covered by the following copyright and
permission notice:

    MIT License

    Copyright (c) 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files
    (the "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to permit
    persons to whom the Software is furnished to do so, subject to
    the following conditions:

        The above copyright notice and this permission notice shall be
        included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

-------------------------------------------------------------------------------

This module provides core functions for processing images and find duplicates
'''

from __future__ import annotations

import os
import pickle
from multiprocessing import Pool
from pathlib import Path
from typing import (Collection, Dict, Iterable, List, Optional, Sequence, Set,
                    Tuple, TypeVar, Union)

import dhash as dhashlib
import pybktree
from PIL import Image as PILImage
from PIL import ImageFile

# Crazy hack not to get error 'IOError: image file is truncated...'
ImageFile.LOAD_TRUNCATED_IMAGES = True

def find_images(folders: Iterable[FolderPath],
                recursive: bool = True) -> Set[ImagePath]:
    '''Find all the images in :folders:

    :param folders: paths of the folders,
    :param recursive: recursive search (include subfolders),
    :return: full paths of the images,
    :raise FileNotFoundError: any of the folders does not exist
    '''

    paths = set()
    for path in folders:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f'{path} does not exist')
        paths.update(_search(p, recursive))
    return paths

def _search(path: Path, recursive: bool) -> Set[ImagePath]:
    paths = set()
    if recursive:
        patterns = ['**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.bmp']
    else:
        patterns = ['*.png', '*.jpg', '*.jpeg', '*.bmp']

    for pattern in patterns:
        for filename in path.glob(pattern):
            if filename.is_file():
                paths.add(str(filename))
    return paths

def hamming(image1: Image, image2: Image) -> Distance:
    '''Calculate the Hamming distance between two images

    :param image1: the first image,
    :param image2: the second image,
    :return: Hamming distance
    '''

    return dhashlib.get_num_bits_different(image1.hash, image2.hash)

def image_grouping(images: Collection[Image],
                   sensitivity: Sensitivity) -> List[Group]:
    '''Find similar images and group them

    :param images: images to process,
    :param sensitivity: maximal difference between hashes of 2 images
                        when they are considered similar,
    :return: groups of similar images. If there are no duplicate
             images, an empty list is returned,
    :raise TypeError: any of the hashes is not integer
    '''

    if len(images) <= 1:
        return []

    image_groups = []
    checked: Set[Image] = set()
    try:
        bkt = pybktree.BKTree(hamming, images)
    except TypeError:
        raise TypeError('While grouping, image hashes must be integers')

    for image in images:
        if image in checked:
            continue

        closests = bkt.find(image, sensitivity)

        # If there's one element in 'closests', it's the 'image' itself
        if len(closests) == 1:
            continue

        image_groups.append(_new_group(closests, checked))

    return image_groups

def _new_group(closests: List[Tuple[Distance, Image]],
               checked: Set[Image]) -> Group:
    image_group = []
    for dist, img in closests:
        if img not in checked:
            img.difference = dist
            image_group.append(img)
            checked.add(img)
    return image_group

def load_cache() -> Cache:
    '''Load the cache with earlier calculated hashes

    :return: dictionary with pairs "ImagePath: Hash",
    :raise EOFError: the cache file might be corrupted (or empty),
    :raise OSError: if there's some problem while opening cache file
    '''

    try:
        with open('cache.p', 'rb') as f:
            cache = pickle.load(f)
    except FileNotFoundError:
        cache = {}
    except EOFError:
        raise EOFError('The cache file might be corrupted (or empty)')
    except OSError as e:
        raise OSError(e)
    return cache

def check_cache(paths: Iterable[ImagePath], cache: Cache) -> List[ImagePath]:
    '''Check which images are not cached

    :param paths: full paths of images,
    :param cache: dict with pairs "ImagePath: Hash",
    :return: list with the paths of not cached images
    '''

    not_cached = []
    for path in paths:
        if path not in cache:
            not_cached.append(path)
    return not_cached

def extend_cache(cache: Cache, paths: Iterable[ImagePath],
                 hashes: Sequence[Optional[Hash]]) -> Cache:
    '''Populate cache with new hashes

    :param cache: dict with pairs "ImagePath: Hash",
    :param paths: paths of new images,
    :param hashes: new hashes,
    :return: dict with pairs "ImagePath: Hash" (updated cache)
    '''

    for i, path in enumerate(paths):
        dhash = hashes[i]
        if dhash is not None:
            cache[path] = dhash
    return cache

def save_cache(cache: Cache) -> None:
    '''Save cache on the disk

    :param cache: dict with pairs "ImagePath: Hash",
    :raise OSError: if there's some problem while opening cache file
    '''

    try:
        with open('cache.p', 'wb') as f:
            pickle.dump(cache, f)
    except OSError as e:
        raise OSError(e)

def calculating(paths: Iterable[ImagePath]) -> List[Optional[Hash]]:
    '''Calculate the hashes of images with :paths:

    :param paths: paths of the images which hashes are not calculated yet,
    :return: list with calculated hashes, Hash can be "None"
    '''

    with Pool() as p:
        hashes = p.map(Image.dhash, paths)
    return hashes


class Image:
    '''Class representing images'''

    def __init__(self, path: ImagePath, dhash: Hash) -> None:
        self.path = path
        self.hash = dhash
        # Difference between the hash of the image
        # and the hash of the 1st image in the group
        self.difference = 0
        self.thumbnail = None
        self.suffix: Suffix = Path(path).suffix # '.jpg', '.png', etc.
        self.size: FileSize = None
        self.width: Width = None
        self.height: Height = None

    @staticmethod
    def dhash(path: ImagePath) -> Optional[Hash]:
        '''Calculate the perceptual hash of the image using lib "dhash"

        :param path: path of an image,
        :return: the hash of the image or None if there's any problem
        '''

        try:
            image = PILImage.open(path)
        except OSError:
            dhash = None
        else:
            dhash = dhashlib.dhash_int(image)
        return dhash

    def dimensions(self) -> Tuple[Width, Height]:
        '''Return the dimensions of the image

        :return: tuple with width and height of the image,
        :raise OSError: any problem while opening the image
        '''

        if self.width is None or self.height is None:
            try:
                image = PILImage.open(self.path)
            except OSError:
                raise OSError(f'Cannot get the dimensions of {self.path}')
            else:
                self.width, self.height = image.size
        return self.width, self.height

    def filesize(self, size_format: SizeFormat = 1) -> FileSize:
        '''Return the file size of the image

        :param size_format: bytes - 0, KiloBytes - 1, MegaBytes - 2,
        :return: file size in bytes, kilobytes or megabytes, rounded
                 to the first decimal place,
        :raise OSError: any problem while opening the image,
        :raise ValueError: :size_format: is not amongst the allowed values
        '''

        if size_format not in (0, 1, 2):
            raise ValueError('Wrong size format')

        if self.size is None:
            try:
                image_size = os.path.getsize(self.path)
            except OSError:
                raise OSError(f'Cannot get the file size of {self.path}')
            else:
                self.size = image_size

        if size_format == 0:
            filesize = self.size
        if size_format == 1:
            filesize = round(self.size / 1024, 1)
        if size_format == 2:
            filesize = round(self.size / (1024**2), 1)

        return filesize

    def delete(self) -> None:
        '''Delete the image from the disk

        :raise OSError: the file does not exist, is a folder, is in use, etc.
        '''

        try:
            os.remove(self.path)
        except OSError:
            raise OSError(f'{self.path} cannot be removed')

    def move(self, dst: FolderPath) -> None:
        r'''Move the image to a new directory

        :param dst: new location, eg. "/new/location/" or "C:\location",
        :raise OSError: the file does not exist, is a folder,
                        :dst: exists, etc.
        '''

        file_name = Path(self.path).name
        new_path = str(Path(dst) / file_name)

        try:
            os.rename(self.path, new_path)
        except OSError:
            raise OSError(f'{self.path} cannot be moved')

    def rename(self, name: str) -> None:
        '''Rename the image

        :param name: new name of the image,
        :raise FileExistsError: if a file with name :new_name:
                                already exists (on Unix replaces
                                the old file silently)
        '''

        path = Path(self.path)
        new_name = path.parent / name
        try:
            path.rename(new_name)
        except FileExistsError as e:
            raise FileExistsError(f'File with name "{name}" already exists')
        else:
            self.path = str(new_name)

    def del_parent_dir(self) -> None:
        '''Delete the parent directory if it is empty'''

        parent_dir = Path(self.path).parent
        if not list(parent_dir.glob('*')):
            parent_dir.rmdir()

    def __str__(self) -> str:
        return self.path


class Sort:
    '''Custom sort for duplicate images (already grouped)'''

    def __init__(self, image_groups: Iterable[Group]) -> None:
        self.image_groups = image_groups

    def sort(self, sort_type: int = 0) -> None:
        '''Sort duplicate image groups

        :param sort_type: 0 - sort by similarity rate
                              in descending order,
                          1 - sort by size of an image file
                              in descending order,
                          2 - sort by width and height of an image
                              in descending order,
                          3 - sort by path of an image file
                              in ascending order
        '''

        if sort_type == 0:
            self._similarity_sort()
        if sort_type == 1:
            self._filesize_sort()
        if sort_type == 2:
            self._dimensions_sort()
        if sort_type == 3:
            self._path_sort()

    def _similarity_sort(self) -> None:
        for group in self.image_groups:
            group.sort(key=lambda x: x.difference)

    def _filesize_sort(self) -> None:
        for group in self.image_groups:
            group.sort(key=Image.filesize, reverse=True)

    def _dimensions_sort(self) -> None:
        for group in self.image_groups:
            group.sort(key=self._dimensions_product, reverse=True)

    def _path_sort(self) -> None:
        for group in self.image_groups:
            group.sort(key=lambda img: img.path)

    @staticmethod
    def _dimensions_product(image: Image) -> int:
        width, height = image.dimensions()
        return width * height


########################## Types ##################################

FolderPath = str # Path to a folder
ImagePath = str # Path to an image
Hash = int # Perceptual hash of an image
Distance = int # Distance between 2 hashes
Sensitivity = int # Max 'Distance' when images are considered similar
Suffix = str # '.jpg', '.png', etc. (with a dot)
Width = int # Width of a image
Height = int # Height of a image
FileSize = Union[int, float] # Size of a file
SizeFormat = int # Units of file size (one of {0, 1, 2})
Cache = Dict[ImagePath, Hash] # Cache containing image hashes
Group = List[Image] # Group of similar images

T = TypeVar('T')

###################################################################


if __name__ == '__main__':

    print('This is a demonstration of finding duplicate (similar) images')
    print('It might take some time, Be patient')
    print('------------------------')

    msg = 'Type the path of the folder you want to find duplicate images in\n'
    folders = input(msg)
    msg = ('Type the searching sensitivity (a value '
           'between 0 and 20 is recommended)\n')
    sensitivity = input(msg)
    print('------------------------')

    paths = find_images([folders])
    print(f'There are {len(paths)} images in the folder')

    cache = load_cache()
    not_cached = check_cache(paths, cache)
    print(f'{len(paths)-len(not_cached)} images have been found in the cache')

    print('Starting to calculate hashes...')
    if not_cached:
        hashes = calculating(not_cached)
        cache = extend_cache(cache, not_cached, hashes)
        save_cache(cache)
    print('All the hashes have been calculated')

    images = [Image(path, cache[path]) for path in paths if path in cache]

    print('Starting to compare images...')
    image_groups = image_grouping(images, int(sensitivity))
    print(f'{len(image_groups)} duplicate image groups have been found')

    print('Sorting the images by similarity rate in descending order...')
    s = Sort(image_groups)
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
