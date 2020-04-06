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
import pathlib
import pickle
from enum import Enum
from multiprocessing import Pool
from pathlib import Path
from typing import (Collection, Dict, Generator, Iterable, List, Optional,
                    Sequence, Tuple, TypeVar, Union)

import dhash as dhashlib
import pybktree
from PIL import Image as PILImage
from PIL import ImageFile

# Crazy hack not to get error 'IOError: image file is truncated...'
ImageFile.LOAD_TRUNCATED_IMAGES = True

def find_image(folders: Iterable[FolderPath],
               recursive: bool = True) -> Generator[ImagePath, None, None]:
    '''Find next image in :folders: and yield its path

    :param folders: paths of the folders,
    :param recursive: recursive search (include subfolders),
    :yield: full path of the next image,
    :raise FileNotFoundError: any of the folders does not exist
    '''

    IMG_SUFFIXES = {'.png', '.jpg', '.jpeg', '.bmp'}
    pattern = '**/*' if recursive else '*'

    for path in folders:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f'{path} does not exist')

        for filename in p.glob(pattern):
            if filename.is_file() and filename.suffix in IMG_SUFFIXES:
                yield str(filename)

def hamming(image1: Image, image2: Image) -> Distance:
    '''Calculate the Hamming distance between two images

    :param image1: the first image,
    :param image2: the second image,
    :return: Hamming distance
    '''

    return dhashlib.get_num_bits_different(image1.hash, image2.hash)

def image_grouping(images: Collection[Image], sensitivity: Sensitivity) \
    -> Generator[List[Group], None, None]:
    '''Find similar images and group them. Yield an intermediate result
    after checking every image in :images:. The last yielded value is
    the result. If :images: is empty or no duplicate image is found,
    an empty list is returned

    :param images: images to process,
    :param sensitivity: maximal difference between hashes of 2 images
                        when they are considered similar,
    :yield: groups of similar images,
    :raise TypeError: any of the hashes is not integer
    '''

    image_groups: List[Group] = []

    if not images:
        yield image_groups

    try:
        bktree = pybktree.BKTree(hamming, images)
    except TypeError:
        raise TypeError('The hashes must be integers')

    checked: Dict[Image, int] = {} # {Image: index of the group}

    for image in images:
        distance, closest = _closest(bktree, image, sensitivity)
        if closest is None:
            yield image_groups
            continue

        # 'closest' goes to the same group as 'image'
        if image in checked and closest not in checked:
            _add_img_to_existing_group(image, closest, checked, image_groups)
        # and vice versa
        if image not in checked and closest in checked:
            _add_img_to_existing_group(closest, image, checked, image_groups)
        # create a new group with 'image' and 'closest' it it
        if image not in checked and closest not in checked:
            _add_new_group(image, closest, checked, image_groups, distance)

        yield image_groups

def _closest(bktree: pybktree.BKTree, image: Image, sensitivity: Sensitivity) \
    -> Tuple[Optional[Distance], Optional[Image]]:
    closests = bktree.find(image, sensitivity)

    # if len == 1, there's only 'image' itself
    if len(closests) == 1:
        return None, None

    distance, closest = closests[1]
    if image == closest: # again, 'image' itself
        distance, closest = closests[0]

    return distance, closest

def _add_img_to_existing_group(img_in_group: Image, img_not_in_group: Image,
                               checked: Dict[Image, int],
                               image_groups: List[Group]):
    group_num = checked[img_in_group]
    img_not_in_group.difference = hamming(image_groups[group_num][0],
                                          img_not_in_group)
    image_groups[group_num].append(img_not_in_group)
    checked[img_not_in_group] = group_num

def _add_new_group(img1: Image, img2: Image, checked: Dict[Image, int],
                   image_groups: List[Group], distance: Distance):
    img2.difference = distance
    image_groups.append([img1, img2])
    checked[img1] = len(image_groups) - 1
    checked[img2] = len(image_groups) - 1

def load_cache(cache_file: CachePath) -> Cache:
    '''Load the cache with earlier calculated hashes

    :param cache_file: path to the cache file,
    :return: dictionary with pairs "ImagePath: Hash",
    :raise EOFError: the cache file might be corrupted (or empty),
    :raise OSError: if there's some problem while opening cache file
    '''

    try:
        with open(cache_file, 'rb') as f:
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

def save_cache(cache_file: CachePath, cache: Cache) -> None:
    '''Save cache on the disk

    :param cache_file: path to the cache file,
    :param cache: dict with pairs "ImagePath: Hash",
    :raise OSError: if there's some problem while opening cache file
    '''

    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(cache, f)
    except OSError as e:
        raise OSError(e)

def calculate_hashes(paths: Iterable[ImagePath]) \
    -> Generator[Optional[Hash], None, None]:
    '''Calculate and yield hashes of images. Calculating is parallel
    and utilises all CPU cores

    :param paths: paths of images,
    :yield: hash of an image with a path from :paths:
    '''

    with Pool() as p:
        for dhash in p.imap(Image.dhash, paths):
            yield dhash


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
        return image.width * image.height


class SizeFormat(Enum):
    '''Class representing size formats'''

    B = 1           # Bytes
    KB = 1024       # KiloBytes
    MB = 1024**2    # MegaBytes


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
        self._width: Width = None
        self._height: Height = None

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
            image.close()
        return dhash

    def _set_dimensions(self) -> None:
        try:
            image = PILImage.open(self.path)
        except OSError:
            raise OSError(f'Cannot get the dimensions of {self.path}')
        else:
            self._width, self._height = image.size
            image.close()

    @property
    def width(self) -> Width:
        '''Return width of the image

        :return: width,
        :raise OSError: problem with opening the image
        '''

        if self._width is None:
            self._set_dimensions()
        return self._width

    @property
    def height(self) -> Width:
        '''Return height of the image

        :return: height,
        :raise OSError: problem with opening the image
        '''

        if self._height is None:
            self._set_dimensions()
        return self._height

    def _set_filesize(self) -> None:
        try:
            image_size = os.path.getsize(self.path)
        except OSError:
            raise OSError(f'Cannot get the file size of {self.path}')
        else:
            self.size = image_size

    def filesize(self, size_format: SizeFormat = SizeFormat.KB) -> FileSize:
        '''Return the file size of the image

        :param size_format: any of enum 'SizeFormat',
        :return: file size in bytes, kilobytes or megabytes, rounded
                 to the first decimal place,
        :raise OSError: any problem with opening the image,
        '''

        if self.size is None:
            self._set_filesize()

        formatted_size = round(self.size / size_format.value, 1)
        return formatted_size

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


########################## Types ##################################

FilePath = str # Path to a file
CachePath = FilePath # Path to the cache file
FolderPath = FilePath # Path to a folder
ImagePath = FilePath # Path to an image
Hash = int # Perceptual hash of an image
Distance = int # Distance between 2 hashes
Sensitivity = int # Max 'Distance' when images are considered similar
Suffix = str # '.jpg', '.png', etc. (with a dot)
Width = int # Width of a image
Height = int # Height of a image
FileSize = Union[int, float] # Size of a file
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
    msg = ('Type the path of the folder you want to save the cache file in. '
           'Press "Enter" if you want to save it in the working directory\n')
    cache_folder = input(msg)
    if cache_folder:
        cache_file = str(pathlib.Path(cache_folder) / 'cache.p')
    else:
        cache_file = 'cache.p'
    print('------------------------')
    print('Searching images in the folder...')
    paths = set(find_image([folders]))
    print(f'There are {len(paths)} images in the folder')

    cache = load_cache(cache_file)
    not_cached = check_cache(paths, cache)
    print(f'{len(paths)-len(not_cached)} images have been found in the cache')

    print('Starting to calculate hashes...')
    if not_cached:
        hashes = list(calculate_hashes(not_cached))
        cache = extend_cache(cache, not_cached, hashes)
        save_cache(cache_file, cache)
    print('All the hashes have been calculated')

    images = [Image(path, cache[path]) for path in paths if path in cache]

    print('Starting to compare images...')
    image_groups = list(image_grouping(images, int(sensitivity)))[-1]
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
