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

    Copyright (c) 2016 Jetsetter

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom
    the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

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
from enum import Enum
from pathlib import Path
from typing import (Collection, Dict, Generator, Iterable, List, Optional,
                    Tuple, Union)

import pybktree
from PyQt5 import QtCore, QtGui


def find_image(folders: Iterable[FolderPath],
               recursive: bool = True) -> Generator[Image, None, None]:
    '''Find next image in :folders: and yield its representation
    as "Image" object

    :param folders:             paths to the folders,
    :param recursive:           recursive search - include subfolders
                                (optional, "True" by default),
    :yield:                     next image as "Image" object,
    :raise FileNotFoundError:   any of the folders does not exist
    '''

    IMG_SUFFIXES = {'.png', '.jpg', '.jpeg', '.bmp', '.pbm', '.pgm', '.ppm',
                    '.xbm', '.xpm'}
    pattern = '**/*' if recursive else '*'

    for path in folders:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f'{path} does not exist')

        for filename in p.glob(pattern):
            if filename.is_file() and filename.suffix in IMG_SUFFIXES:
                yield Image(str(filename))

def image_grouping(images: Collection[Image], sensitivity: Sensitivity) \
    -> Generator[List[Group], None, None]:
    '''Find similar images and group them. Yield an intermediate result
    after checking every image in :images:. The last yielded value is
    the result. If :images: is empty or no duplicate images are found,
    an empty list is returned

    :param images:      images to process,
    :param sensitivity: maximal difference between hashes of 2 images
                        when they are considered similar,
    :yield:             groups of similar images,
    :raise TypeError:   any of the hashes is not integer
    '''

    image_groups: List[Group] = []

    if not images:
        yield image_groups

    try:
        bktree = pybktree.BKTree(Image.hamming, images)
    except TypeError:
        raise TypeError('Hashes must be integers')

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
    first_img = image_groups[group_num][0]
    img_not_in_group.difference = first_img.hamming(img_not_in_group)
    image_groups[group_num].append(img_not_in_group)
    checked[img_not_in_group] = group_num

def _add_new_group(img1: Image, img2: Image, checked: Dict[Image, int],
                   image_groups: List[Group], distance: Distance):
    img2.difference = distance
    image_groups.append([img1, img2])
    checked[img1] = len(image_groups) - 1
    checked[img2] = len(image_groups) - 1


class Sort:
    '''Custom sort for duplicate images (already grouped if the sort
    by similarity will be used)

    :param images: duplicate images to sort
    '''

    def __init__(self, images: Group) -> None:
        self.images = images

    def sort(self, sort_type: int = 0) -> None:
        '''Sort duplicate image group

        :param sort_type: 0 - sort by similarity rate
                              in descending order (default),
                          1 - sort by size of an image file
                              in descending order,
                          2 - sort by width and height of an image
                              in descending order,
                          3 - sort by path of an image file
                              in ascending order
        '''

        sort_funcs = {
            0: self._similarity_sort,
            1: self._filesize_sort,
            2: self._dimensions_sort,
            3: self._path_sort
        }

        sort_funcs[sort_type]()

    def _similarity_sort(self) -> None:
        self.images.sort(key=lambda x: x.difference)

    def _filesize_sort(self) -> None:
        self.images.sort(key=Image.filesize, reverse=True)

    def _dimensions_sort(self) -> None:
        self.images.sort(key=self._dimensions_product, reverse=True)

    def _path_sort(self) -> None:
        self.images.sort(key=lambda img: img.path)

    @staticmethod
    def _dimensions_product(image: Image) -> int:
        return image.width * image.height


class SizeFormat(Enum):
    '''Class representing size formats. Bytes (B), kilobytes (KB),
    megabytes (MB) are implemented

    :param int_index: an instance can be constructed by passing an integer
                      index to the SizeFormat constructor
                      (e.g. "SizeFormat(2)" returns "SizeFormat.MB" object)
    '''

    B = 0     # Bytes
    KB = 1    # KiloBytes
    MB = 2    # MegaBytes

    def __init__(self, int_index: int) -> None:
        self._int_index = int_index

    @property
    def coefficient(self) -> int:
        '''Return size format coefficient. Bytes - 1, KiloBytes - 1024,
        MegaBytes = 1024**2
        '''

        return 1024**self._int_index


class Image:
    '''Class representing images

    :param path: image path
    '''

    def __init__(self, path: ImagePath) -> None:
        self.path = path
        self.dhash: Hash = None
        # Difference between the hash of the image
        # and the hash of the 1st image in the group
        self.difference = 0
        self.thumb: QtGui.QImage = None
        self.size: FileSize = None
        self._width: Width = None
        self._height: Height = None

    def calculate_dhash(self) -> Hash:
        '''Return perceptual hash of the image and assign it
        to the attribute "dhash"

        :return: perceptual hash or -1 if the hash cannot be calculated
        '''

        SIZE = 8 # Hash-vector size is 2 * (SIZE ** 2)

        try:
            qimg = self.scaled(SIZE+1, SIZE+1)
        except OSError:
            self.dhash = -1
        else:
            grey = qimg.convertToFormat(QtGui.QImage.Format_Grayscale8)
            self.dhash = self._form_hash(grey, SIZE)

        return self.dhash

    @staticmethod
    def _form_hash(image: QtGui.QImage, size: int) -> Hash:
        # Code is taken from library "dhash" except the "PyQt" parts
        row_hash, col_hash = 0, 0
        for y in range(size):
            for x in range(size):
                current_pixel = QtGui.qGray(image.pixel(x, y))
                right_pixel = QtGui.qGray(image.pixel(x+1, y))
                down_pixel = QtGui.qGray(image.pixel(x, y+1))

                row_bit = current_pixel < right_pixel
                row_hash = row_hash << 1 | row_bit

                col_bit = current_pixel < down_pixel
                col_hash = col_hash << 1 | col_bit

        return row_hash << (size * size) | col_hash

    def dhash_parallel(self) -> Image:
        '''Calculate hash and return "Image" object itself with
        the hash assigned to attribute "dhash". It is used with
        library "multiprocessing"

        :return: "Image" object (self)
        '''

        self.calculate_dhash()
        return self

    def hamming(self, image: Image) -> Distance:
        '''Calculate the Hamming distance between two images

        :param image:   the second image,
        :return:        Hamming distance
        '''

        return bin(self.dhash ^ image.dhash).count('1')

    def similarity(self) -> int:
        '''To compare images, hamming distance between their
        hashes is found (difference). It is easier for a user
        to see how similar the images are

        :return: similarity rate (in %)
        '''

        diff = self.difference

        if diff == 0:
            # if difference == 0, then similarity == 100
            return 100
        # hash is a 128-bit vector
        return int((1 - diff / 128) * 100)

    def thumbnail(self, size: int) -> QtGui.QImage:
        '''Make image thumbnail, assign it to attribute "thumb"
        and return it

        :param size:    the biggest dimension (width or height) of
                        the image after having been scaled,
        :return:        thumbnail as "QImage" object,
        :raise OSError: something went wrong while making thumbnail
        '''

        width, height = self.scaling_dimensions(size)
        self.thumb = self.scaled(width, height)

        return self.thumb

    def scaling_dimensions(self, size: int) -> Tuple[Width, Height]:
        '''Return width and height of the scaled image with the aspect ratio
        kept where the biggest size is :size:. E.g. for 200x400 image and
        :size: == 200, (100, 200) will be returned

        :param size:    the biggest size of the scaled image (px),
        :return:        width and height of the scaled image,
        :raise OSError: image size cannot be read for some reason
        '''

        width, height = self.width, self.height
        biggest_dim = width if width >= height else height
        new_width, new_height = (width * size // biggest_dim,
                                 height * size // biggest_dim)
        return new_width, new_height

    def scaled(self, width: Width, height: Height) -> QtGui.QImage:
        '''Scale image and return it

        :param width:   width of the scaled image,
        :param height:  height of the scaled image,
        :return:        scaled image as "QImage" object,
        :raise OSError: image cannot be read for some reason
        '''

        path = self.path
        reader = QtGui.QImageReader(path)
        reader.setScaledSize(QtCore.QSize(width, height))

        if not reader.canRead():
            raise OSError(f'{path} cannot be read')

        img = reader.read()

        if img.isNull():
            e = reader.errorString()
            raise OSError(e)
        return img

    def _set_dimensions(self) -> None:
        image = QtGui.QImageReader(self.path)
        size = image.size()
        if not size.isValid():
            raise OSError('Image size cannot be read')

        self._width, self._height = size.width(), size.height()

    @property
    def width(self) -> Width:
        '''Return width of the image

        :return:        width,
        :raise OSError: image size cannot be read for some reason
        '''

        if self._width is None:
            self._set_dimensions()
        return self._width

    @property
    def height(self) -> Width:
        '''Return height of the image

        :return:        height,
        :raise OSError: image size cannot be read for some reason
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

    def filesize(self, size_format: SizeFormat = SizeFormat.B) -> FileSize:
        '''Return the file size of the image

        :param size_format: any of enum 'SizeFormat',
        :return:            file size in bytes, kilobytes or megabytes, rounded
                            to the first decimal place,
        :raise OSError:     any problem with opening the image,
        '''

        if self.size is None:
            self._set_filesize()

        formatted_size = round(self.size / size_format.coefficient, 1)
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

        :param dst:     new location, eg. "/new/location/" or "C:\location",
        :raise OSError: the file does not exist, is a folder, :dst: exists, etc
        '''

        file_name = Path(self.path).name
        new_path = str(Path(dst) / file_name)

        try:
            os.rename(self.path, new_path)
        except OSError:
            raise OSError(f'{self.path} cannot be moved')

    def rename(self, name: str) -> None:
        '''Rename the image

        :param name:                new name of the image,
        :raise FileExistsError:     the file with name :new_name: already
                                    exists (on Unix replaces the old file
                                    silently),
        :raise FileNotFoundError:   the file has been removed
        '''

        path = Path(self.path)
        new_name = path.parent / name
        try:
            path.rename(new_name)
        except FileExistsError:
            err_msg = f'File with the name "{name}" already exists'
            raise FileExistsError(err_msg)
        except FileNotFoundError:
            err_msg = f'File with the name "{path}" does not exist'
            raise FileNotFoundError(err_msg)
        else:
            self.path = str(new_name)

    def del_parent_dir(self) -> None:
        '''Delete the parent directory if it is empty'''

        parent_dir = Path(self.path).parent
        if not list(parent_dir.glob('*')):
            parent_dir.rmdir()

    def __str__(self) -> str:
        return self.path

    def __eq__(self, image: object) -> bool:
        if not isinstance(image, Image):
            return NotImplemented
        return self.path == image.path

    def __hash__(self) -> int:
        return hash(self.path)


########################## Types ##################################
FilePath = str # Path to a file
FolderPath = FilePath # Path to a folder
ImagePath = FilePath # Path to an image
Hash = int # Perceptual hash of an image
Distance = int # Distance between 2 hashes
Sensitivity = int # Max 'Distance' when images are considered similar
Suffix = str # 'jpg', 'png', etc.
Width = int # Width of a image
Height = int # Height of a image
FileSize = Union[int, float] # Size of a file
Group = List[Image] # Group of similar images
###################################################################
