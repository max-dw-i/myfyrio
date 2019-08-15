'''Core functions to process images and find duplicates'''

import os
import pathlib
import pickle
from functools import wraps
from multiprocessing import Pool

import dhash
import pybktree
from PIL import Image as PILImage, ImageFile

# Crazy hack not to get error 'IOError: image file is truncated...'
ImageFile.LOAD_TRUNCATED_IMAGES = True


def get_images_paths(folders):
    '''Returns all the images' full paths from
    the passed 'folders' argument

    :param folders: a collection of folders' paths,
    :returns: list of str, images' full paths
    '''

    IMG_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp'}
    images_paths = []

    for path in folders:
        p = pathlib.Path(path)
        for ext in IMG_EXTENSIONS:
            for filename in p.glob(f'**/*{ext}'):
                if filename.is_file():
                    images_paths.append(str(filename))
    return images_paths

def hamming_dist(image1, image2):
    '''Calculates the Hamming distance between two images

    :param image1: <class Image> object,
    :param image2: <class Image> object,
    :returns: int, Hamming distance
    '''

    return dhash.get_num_bits_different(image1.hash, image2.hash)

def images_grouping(images, sensitivity):
    '''Returns groups of similar images

    :param images: collection of <class Image> objects,
    :param sensitivity: int, min difference between images' hashes
                        when the images are considered similar,
    :returns: list, [[<class Image> obj 1.1, <class Image> obj 1.2, ...],
                     [<class Image> obj 2.1, <class Image> obj 2.2, ...], ...],
              each sublist of which is sorted by image difference in
              ascending order. If there are no duplicate images, an empty list
              is returned
    '''

    if len(images) <= 1:
        return []

    image_groups = []
    checked = {} # {<class Image> obj: index of the image group}
    try:
        bkt = pybktree.BKTree(hamming_dist, images)
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
            closest.difference = hamming_dist(image_groups[group_num][0], closest)
            checked[closest] = group_num
        # and vice versa
        elif image not in checked and closest in checked:
            group_num = checked[closest]
            image_groups[group_num].append(image)
            image.difference = hamming_dist(image_groups[group_num][0], image)
            checked[image] = group_num
        # If neither of these is in groups, add a new group
        elif image not in checked and closest not in checked:
            closest.difference = closests[1][0]
            image_groups.append([image, closest])
            checked[image] = len(image_groups) - 1
            checked[closest] = len(image_groups) - 1

    return [sorted(g, key=lambda x: x.difference) for g in image_groups]

def load_cached_hashes():
    '''Returns cached images' hashes

    :returns: dict, {image_path: str,
                     image_hash: <class ImageHash> obj, ...},
    :raises EOFError: if the cache file cannot be read,
                      for some reason
    '''

    try:
        with open('image_hashes.p', 'rb') as f:
            cached_hashes = pickle.load(f)
    except FileNotFoundError:
        cached_hashes = {}
    except EOFError:
        raise EOFError('The cache file might be corrupted (or empty)')
    return cached_hashes

def check_cache(paths, cached_hashes):
    '''Returns a tuple with 2 lists. The images that are found
    in the cache are in the 1st one, the images that are not
    found in the cache are in the 2nd one

    :param paths: list of str, images' full paths,
    :param cached_hashes: dict, {image_path: str,
                                 image_hash: <class ImageHash> obj},
    :returns: tuple, ([<class Image> obj, ...], [<class Image> obj, ...])
    '''

    cached, not_cached = [], []
    for path in paths:
        suffix = pathlib.Path(path).suffix
        if path in cached_hashes:
            cached.append(Image(path, dhash=cached_hashes[path], suffix=suffix))
        else:
            not_cached.append(Image(path, suffix=suffix))
    return cached, not_cached

def hashes_calculating(images):
    '''Returns a list with the images whose hashes
    are calculated now

    :param images: list of <class Image> objects,
                   images without calculated hashes,
    :returns: list of <class Image> objects
    '''

    with Pool() as p:
        calculated_images = p.map(Image.calc_dhash, images)
    return calculated_images

def caching_images(images, cached_hashes):
    '''Adds new images to the cache, save them on the disk

    :param images: list of <class Image> objects,
    :param cached_hashes: dict, {image_path: str,
                                 image_hash: <class ImageHash> obj}
    '''

    for image in images:
        cached_hashes[image.path] = image.hash

    with open('image_hashes.p', 'wb') as f:
        pickle.dump(cached_hashes, f)

def return_obj(func):
    '''Decorator needed for parallel hashes calculating.
    Multiprocessing lib does not allow to change an object
    in place (because it's a different process). So it's
    passed to the process, changed in there and then
    must be returned
    '''

    @wraps(func)
    def wrapper(obj):
        func(obj)
        return obj
    return wrapper


class Image():
    '''Class that represents images'''

    def __init__(self, path, difference=0, dhash=None,
                 thumbnail=None, suffix=None):
        self.path = path
        # Difference between the image's hash and the 1st
        # image's hash in the group
        self.difference = difference
        self.hash = dhash
        self.thumbnail = thumbnail
        self.suffix = suffix # '.jpg', '.png', etc.

    @return_obj
    def calc_dhash(self):
        '''Calculates an image's difference hash using
        'dhash' function from 'imagehash' lib

        :returns: <class ImageHash> instance or None
                  if there's any problem
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

    def get_dimensions(self):
        '''Returns an image dimensions

        :param path: str, full path to an image,
        :returns: tuple, (width: int, height: int)
                  or (0, 0) if there's any problem,
        :raise OSError: if there's any problem while
                        opening the image
        '''

        try:
            image = PILImage.open(self.path)
        except OSError:
            raise OSError(f'Cannot get the dimensions of {self.path}')
        return image.size

    def get_scaling_dimensions(self, biggest_dim):
        '''Returns the dimensions an image should
        have after having scaled

        :param biggest_dim: int, the biggest dimension of the image after
                            having scaled,
        :returns: tuple, (width: int, height: int) with kept aspect ratio,
        :raise OSError: if there's any problem while getting
                        the image's dimensions,
        :raise ValuError: if the new :biggest_dim: is not positive
        '''

        if biggest_dim <= 0:
            raise ValueError('The new size values must be positive')

        try:
            width, height = self.get_dimensions()
        except OSError:
            raise OSError(f'Cannot get the scaling dimensions of {self.path}')

        if width >= height:
            width, height = (width * biggest_dim // width,
                             height * biggest_dim // width)
        else:
            width, height = (width * biggest_dim // height,
                             height * biggest_dim // height)
        return width, height

    def get_filesize(self, size_format='KB'):
        '''Returns an image file size

        :param size_format: str, ('B', 'KB', 'MB'),
        :returns: float, file size in bytes, kilobytes or megabytes,
                  rounded to the first decimal place or 0 if there's
                  any problem,
        :raise OSError: if there's any problem while opening the image,
        :raise ValueError: if :size_format: not amongst the allowed values
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

    def delete_image(self):
        '''Deletes an image from the disk

        :raise OSError: if the file does not exist,
                        is a folder, is in use, etc.
        '''

        try:
            os.remove(self.path)
        except OSError:
            raise OSError(f'{self.path} cannot be removed')

    def __str__(self):
        return self.path


if __name__ == '__main__':

    print('This is a demonstration of finding duplicate (similar) images')
    print('It might take some time, Be patient')
    print('------------------------')

    folders = input('{} {}\n'.format(
        "Type the folder's path you want",
        'to find duplicate images in',
    ))
    sensitivity = input('{} {}\n'.format(
        'Type the searching sensitivity',
        '(a value between 0 and 100 is recommended)'
    ))
    print('------------------------')

    paths = get_images_paths([folders])
    print('There are {} images in the folder'.format(len(paths)))

    try:
        cached_hashes = load_cached_hashes()
    except EOFError as e:
        print(e)
        print('Delete (back up if needed) the corrupted (or empty) ',
              'cache file and run the script again')

    cached, not_cached = check_cache(paths, cached_hashes)
    print('{} images have been found in the cache'.format(
        len(paths)-len(not_cached)
    ))

    print('Starting to calculate hashes...')
    if not_cached:
        calculated = hashes_calculating(not_cached)
        calculated = [image for image in calculated if image.hash is not None]
        caching_images(calculated, cached_hashes)
        cached.extend(calculated)
    print('All the hashes have been calculated')

    print('Starting to compare images...')
    image_groups = images_grouping(cached, int(sensitivity))
    print('{} duplicate image groups have been found'.format(len(image_groups)))
    print('------------------------')

    for i, group in enumerate(image_groups):
        print('Group {}:'.format(i+1))
        print('------------------------')
        for image in group:
            print(image)
        print('------------------------')

    print('That is it')
    input('Press any key to continue...')
