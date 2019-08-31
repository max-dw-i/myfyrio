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


This file incorporates work covered by the following copyright and
permission notice:

    MIT License

    Copyright (c) 2019 Maxim Shpak <maxim.shpak@posteo.uk>

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

-------------------------------------------------------------------------------

This module provides core functions for processing images and find duplicates.
'''

from __future__ import annotations

import os
import pathlib
import pickle
from functools import wraps
from multiprocessing import Pool
from typing import Any, Callable, Dict, List, Sequence, Set, Tuple, Union

import dhash
import pybktree
from PIL import Image as PILImage
from PIL import ImageFile

# Crazy hack not to get error 'IOError: image file is truncated...'
ImageFile.LOAD_TRUNCATED_IMAGES = True

def find_images(folders: Sequence[str]) -> Set[str]:
    '''Find all the images in :folders:

    :param folders: paths of the folders,
    :return: full paths of the images
    '''

    IMG_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp'}
    paths = set()

    for path in folders:
        p = pathlib.Path(path)
        for ext in IMG_EXTENSIONS:
            for filename in p.glob(f'**/*{ext}'):
                if filename.is_file():
                    paths.add(str(filename))
    return paths

def hamming(image1: Image, image2: Image) -> int:
    '''Calculate the Hamming distance between two images

    :param image1: the first image,
    :param image2: the second image,
    :return: Hamming distance
    '''

    return dhash.get_num_bits_different(image1.hash, image2.hash)

def image_grouping(images: Sequence[Image], sensitivity: int) -> List[List[Image]]:
    '''Find similar images and group them

    :param images: images to process,
    :param sensitivity: minimal difference between hashes of 2 images
                        when they are considered similar,
    :return: groups of similar images. Each sublist is sorted by image
             difference in ascending order. If there are no duplicate
             images, an empty list is returned,
    :raise TypeError: any of the hashes is not integer
    '''

    if len(images) <= 1:
        return []

    image_groups = []
    checked = {} # {<class Image> obj: index of the image group}
    try:
        bkt = pybktree.BKTree(hamming, images)
    except TypeError:
        raise TypeError('While grouping, image hashes must be integers')

    for image in images:
        # We don't need to get all the images with hash
        # differences <= sensitivity, just the least one (in
        # this algorithm). But it's not possible to do it in
        # 'pybktree' lib, so...
        closests = bkt.find(image, sensitivity)

        # If there's one element in 'closests', it's the 'image' itself,
        # so we need the next one (the 1st)
        if len(closests) == 1:
            continue

        closest = closests[1][1]

        # If 'image' is in a group already, its closest image goes to the same group
        if image in checked and closest not in checked:
            group_num = checked[image]
            image_groups[group_num].append(closest)
            closest.difference = hamming(image_groups[group_num][0], closest)
            checked[closest] = group_num
        # and vice versa
        elif image not in checked and closest in checked:
            group_num = checked[closest]
            image_groups[group_num].append(image)
            image.difference = hamming(image_groups[group_num][0], image)
            checked[image] = group_num
        # If neither of these is in groups, add a new group
        elif image not in checked and closest not in checked:
            closest.difference = closests[1][0]
            image_groups.append([image, closest])
            checked[image] = len(image_groups) - 1
            checked[closest] = len(image_groups) - 1

    return [sorted(g, key=lambda x: x.difference) for g in image_groups]

def load_cache() -> Dict[str, int]:
    '''Load the cache with earlier calculated hashes

    :return: dictionary with pairs 'image path: hash',
    :raise EOFError: the cache file cannot be read
    '''

    try:
        with open('image_hashes.p', 'rb') as f:
            cached_hashes = pickle.load(f)
    except FileNotFoundError:
        cached_hashes = {}
    except EOFError:
        raise EOFError('The cache file might be corrupted (or empty)')
    return cached_hashes

def check_cache(paths: Sequence[str],
                cached_hashes: Dict[str, int]) -> Tuple[List[Image], List[Image]]:
    '''Check which images are cached and which ones are not

    :param paths: full paths of images,
    :param cached_hashes: dictionary with pairs 'image path: hash',
    :return: return a tuple with 2 lists. The images that are found
             in the cache are in the 1st one, the images that are not
             found in the cache are in the 2nd one
    '''

    cached, not_cached = [], []
    for path in paths:
        suffix = pathlib.Path(path).suffix
        if path in cached_hashes:
            cached.append(Image(path, dhash=cached_hashes[path], suffix=suffix))
        else:
            not_cached.append(Image(path, suffix=suffix))
    return cached, not_cached

def hashes_calculating(images: Sequence[Image]) -> List[Image]:
    '''Calculate the hashes of :images:

    :param images: images which hashes are not calculated yet,
    :return: images with calculated hashes
    '''

    with Pool() as p:
        calculated_images = p.map(Image.dhash, images)
    return calculated_images

def caching(images: Sequence[Image], cached_hashes: Dict[str, int]) -> None:
    '''Add new hashes to the cache and save them on the disk

    :param images: images to process,
    :param cached_hashes: dictionary with pairs 'image path: hash'
    '''

    for image in images:
        cached_hashes[image.path] = image.hash

    with open('image_hashes.p', 'wb') as f:
        pickle.dump(cached_hashes, f)

def return_obj(func: Callable[[object], Any]) -> object:
    '''Decorator needed for parallel hashes calculating.
    Multiprocessing lib does not allow to change an object
    in place (because it's a different process). So it's
    passed to the process, changed in there and then
    must be returned

    :param func: function to use in 'multiprocessing.Pool.map',
                 eg. 'Image.dhash',
    :return: object on which :func: is called, eg. 'Image' object
    '''

    @wraps(func)
    def wrapper(obj):
        func(obj)
        return obj
    return wrapper


class Image():
    '''Class that represents images'''

    def __init__(self, path: str, difference: int = 0, dhash: int = None,
                 thumbnail: Any = None, suffix: str = None) -> None:
        self.path = path
        # Difference between the image's hash and the 1st
        # image's hash in the group
        self.difference = difference
        self.hash = dhash
        self.thumbnail = thumbnail
        self.suffix = suffix # '.jpg', '.png', etc.

    @return_obj
    def dhash(self) -> int:
        '''Calculate the perceptual hash of the image
        using 'dhash' library

        :return: the hash of the image
        '''

        try:
            image = PILImage.open(self.path)
        except OSError:
            self.hash = None
        #except UnboundLocalError as e:
            # Sometimes UnboundLocalError in PIL/JpegImagePlugin.py
            # happens with some images. Should be fixed in PIL 6.1.0.
            # Till then these images are not processed
            #print(e, self.path)
            #self.hash = None
        else:
            self.hash = dhash.dhash_int(image)
        return self.hash

    def dimensions(self) -> Tuple[int, int]:
        '''Return the dimensions of the image

        :return: tuple with the image's width and height,
        :raise OSError: any problem while opening the image
        '''

        try:
            image = PILImage.open(self.path)
        except OSError:
            raise OSError(f'Cannot get the dimensions of {self.path}')
        return image.size

    def scaling_dimensions(self, biggest_dim: int) -> Tuple[int, int]:
        '''Find the new dimensions of the image (with aspect ratio kept)
        after being scaled

        :param biggest_dim: the biggest dimension of the image after
                            being scaled,
        :return: tuple with the image's width and height,
        :raise OSError: any problem while getting the image's dimensions,
        :raise ValuError: new :biggest_dim: is not positive
        '''

        if biggest_dim <= 0:
            raise ValueError('The new size values must be positive')

        try:
            width, height = self.dimensions()
        except OSError:
            raise OSError(f'Cannot get the scaling dimensions of {self.path}')

        if width >= height:
            width, height = (width * biggest_dim // width,
                             height * biggest_dim // width)
        else:
            width, height = (width * biggest_dim // height,
                             height * biggest_dim // height)
        return width, height

    def filesize(self, size_format: str = 'KB') -> Union[int, float]:
        '''Return the file size of the image

        :param size_format: bytes - 'B', KiloBytes - 'KB', MegaBytes - 'MB',
        :return: file size in bytes, kilobytes or megabytes, rounded
                 to the first decimal place,
        :raise OSError: any problem while opening the image,
        :raise ValueError: :size_format: is not amongst the allowed values
        '''

        try:
            image_size = os.path.getsize(self.path)
        except OSError:
            raise OSError(f'Cannot get the file size of {self.path}')

        if size_format == 'B':
            return image_size
        if size_format == 'KB':
            return round(image_size / 1024, 1)
        if size_format == 'MB':
            return round(image_size / (1024**2), 1)

        raise ValueError('Wrong size format')

    def delete(self) -> None:
        '''Delete the image from the disk

        :raise OSError: the file does not exist, is a folder, is in use, etc.
        '''

        try:
            os.remove(self.path)
        except OSError:
            raise OSError(f'{self.path} cannot be removed')

    def move(self, dst: str) -> None:
        r'''Move the image to a new directory

        :param dst: new location, eg. '/new/location/' or 'C:\location',
        :raise OSError: the file does not exist, is a folder,
                        :dst: exists, etc.
        '''

        file_name = pathlib.Path(self.path).name
        new_path = str(pathlib.Path(dst) / file_name)

        try:
            os.rename(self.path, new_path)
        except OSError:
            raise OSError(f'{self.path} cannot be moved')

    def __str__(self) -> str:
        return self.path


if __name__ == '__main__':

    print('This is a demonstration of finding duplicate (similar) images')
    print('It might take some time, Be patient')
    print('------------------------')

    msg = "Type the folder's path you want to find duplicate images in\n"
    folders = input(msg)
    msg = 'Type the searching sensitivity (a value between 0 and 50 is recommended)\n'
    sensitivity = input(msg)
    print('------------------------')

    paths = find_images([folders])
    print(f'There are {len(paths)} images in the folder')

    try:
        cached_hashes = load_cache()
    except EOFError as e:
        print(e)
        print('Delete (back up if needed) the corrupted (or empty) ',
              'cache file and run the script again')

    cached, not_cached = check_cache(paths, cached_hashes)
    print(f'{len(paths)-len(not_cached)} images have been found in the cache')

    print('Starting to calculate hashes...')
    if not_cached:
        calculated = hashes_calculating(not_cached)
        calculated = [image for image in calculated if image.hash is not None]
        caching(calculated, cached_hashes)
        cached.extend(calculated)
    print('All the hashes have been calculated')

    print('Starting to compare images...')
    try:
        image_groups = image_grouping(cached, int(sensitivity))
    except TypeError as e:
        print(e)
    print(f'{len(image_groups)} duplicate image groups have been found')
    print('------------------------')

    for i, group in enumerate(image_groups):
        print(f'Group {i+1}:')
        print('------------------------')
        for image in group:
            print(image)
        print('------------------------')

    print('That is it')
    input('Press any key to continue...')
