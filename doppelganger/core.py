'''Core functions to process images and find duplicates'''

import os
import pathlib
import pickle
from collections import defaultdict
from multiprocessing import Pool

from functools import wraps

import imagehash
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
            for filename in p.glob('**/*{}'.format(ext)):
                if filename.is_file():
                    images_paths.append(str(filename))
    return images_paths

def _closest_images_populating(closest_images, images, i, j):
    '''Populates :closest_images:

    :param closest_images: dict of :images: indices,
                           eg. {0: 0, 1: 0, 5: 0}. The 1st
                           and 5th's closest image is 0th,
    :param images: collection of <class Image> objects,
    :param i: int, :images: index,
    :param j: int, :images: index
    '''

    # Do nothing if ith and jth images have been added already
    if i in closest_images and j in closest_images:
        return
    # ...if the ith's closest image was added already, then the closest
    # image of this already added (ith closest) image become the ith's
    # closest image. Eg. we have :closest_images: = {0: 0, 1: 0} and
    # the 5th's closest image is the 1st one; 1 is in :closest_images: and its
    # closest image is the 0th one, so 0 becomes the 5th's closest image and
    # now we have :closest_images: = {0: 0, 1: 0, 5: 0}...
    if j in closest_images:
        images[i].difference = images[i].hash - images[closest_images[j]].hash
        closest_images[i] = closest_images[j]
    # ...and vice versa
    elif i in closest_images:
        images[j].difference = images[j].hash - images[closest_images[i]].hash
        closest_images[j] = closest_images[i]
    else:
        # else we add a new pair of images and the ith image pointing
        # to itself. Eg. :closest_images: = {0: 0, 1: 0, 5: 0} and
        # the 7th's closest image is the 2nd, then now we have
        # :closest_images: = {0: 0, 1: 0, 5: 0, 2: 7, 7: 7}
        images[j].difference = images[j].hash - images[i].hash
        closest_images[j] = i
        closest_images[i] = i

def _closest_images_search(images, sensitivity):
    '''Searches every image's closest one

    :param sensitivity: int, min difference between images' hashes
                        when the images are considered similar,
    :param images: collection of <class Image> objects,
    :returns: dict of :images:' indices, eg. {0: 0, 1: 0, 5: 0}.
              The 1st and 5th's closest image is 0th
    '''

    # Here all the hashes are compared to each other and the closest (most
    # similar image) are added to dict 'closest_images'
    closest_images = {}
    for i, image1 in enumerate(images):
        # If a hash is None there were some problem with
        # calculating it so we don't process the image
        if image1.hash is not None:
            closest_image = None
            min_diff = float('inf')
            for j, image2 in enumerate(images):
                if image2.hash is not None:
                    diff = image1.hash - image2.hash
                    # If the difference less/equal than 'sensitivity' and this
                    # image (image2) is closer to image1 (diff is less),
                    # we remember image2 index
                    if diff <= sensitivity and i != j and min_diff > diff:
                        closest_image = j
                        min_diff = diff
            # If ith image has the closest one...
            if closest_image is not None:
                _closest_images_populating(closest_images, images, i, closest_image)
    return closest_images

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

    closest_images = _closest_images_search(images, sensitivity)

    final_groups = defaultdict(list)
    for i in closest_images:
        final_groups[closest_images[i]].append(images[i])

    return [sorted(final_groups[g], key=lambda x: x.difference) for g in final_groups]

def load_cached_hashes():
    '''Returns cached images' hashes

    :returns: dict, {image_path: str,
                     image_hash: <class ImageHash> obj, ...}
    '''

    try:
        with open('image_hashes.p', 'rb') as f:
            cached_hashes = pickle.load(f)
    except FileNotFoundError:
        cached_hashes = {}
    return cached_hashes

def save_cached_hashes(cached_hashes):
    '''Saves cached images' hashes on the disk

    :param cached_hashes: dict, {image_path: str,
                                 image_hash: <class ImageHash> obj}
    '''

    with open('image_hashes.p', 'wb') as f:
        pickle.dump(cached_hashes, f)

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

    save_cached_hashes(cached_hashes)

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
        except OSError as e:
            print(e, self.path)
            self.hash = None
        except UnboundLocalError as e:
            # Sometimes UnboundLocalError in PIL/JpegImagePlugin.py
            # happens with some images. Should be fixed in PIL 6.1.0.
            # Till then these images are not processed
            print(e, self.path)
            self.hash = None
        else:
            self.hash = imagehash.dhash(image)
        return self.hash

    def get_dimensions(self):
        '''Returns an image dimensions

        :param path: str, full path to an image,
        :returns: tuple, (width: int, height: int)
                  or (0, 0) if there's any problem
        '''

        try:
            image = PILImage.open(self.path)
        except OSError as e:
            print(e)
            return (0, 0)
        return image.size

    def get_scaling_dimensions(self, size):
        '''Returns the dimensions an image should
        have after having scaled

        :param size: tuple, (width: int, height: int),
        :returns: tuple, (width: int, height: int) with
                  kept aspect ratio
        '''

        width, height = self.get_dimensions()
        if width >= height:
            width, height = (width * size // width,
                             height * size // width)
        else:
            width, height = (width * size // height,
                             height * size // height)
        return width, height

    def get_filesize(self, size_format='KB'):
        '''Returns an image file size

        :param size_format: str, ('B', 'KB', 'MB'),
        :returns: float, file size in bytes, kilobytes or megabytes,
                  rounded to the first decimal place or 0 if there's
                  any problem
        :raise ValueError: if :size_format: not amongst
                           the allowed values
        '''

        try:
            image_size = os.path.getsize(self.path)
        except OSError as e:
            print(e)
            return 0

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
        except OSError as e:
            print(e)
            raise OSError(e)

    def __str__(self):
        return self.path


if __name__ == '__main__':

    print('This is a demonstration of finding duplicate (similar) images')
    print('It might take some time, Be patient')
    print('------------------------')

    folders = input("""Type the folder's path you want to find duplicate images in\n""")
    message = '''Type the searching sensitivity (a value between 0 and 100 is recommended)\n'''
    sensitivity = input(message)
    print('------------------------')

    paths = get_images_paths([folders])
    print('There are {} images in the folder'.format(len(paths)))

    cached_hashes = load_cached_hashes()
    cached, not_cached = check_cache(paths, cached_hashes)
    print('{} images have been found in the cache'.format(
        len(paths)-len(not_cached)
    ))

    print('Starting to calculate hashes...')
    if not_cached:
        calculated = hashes_calculating(not_cached)
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
