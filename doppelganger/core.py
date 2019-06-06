'''Core functions to process images and find duplicates'''

import os
import pathlib
import pickle
from collections import defaultdict
from multiprocessing import Pool

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
        closest_image = None
        min_diff = float('inf')
        for j, image2 in enumerate(images):
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
              ascending order
    '''

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

def find_not_cached_images(paths, cached_hashes):
    '''Returns a list with not cached images' paths

    :param paths: list of str, images' full paths,
    :param cached_hashes: dict, {image_path: str,
                                 image_hash: <class ImageHash> obj},
    :returns: list, [not_cached_image_path: str, ...]
    '''

    return [path for path in paths if path not in cached_hashes]

def hashes_calculating(images_paths):
    '''Returns a list with new calculated hashes

    :param images_paths: list of str, images' full paths,
    :returns: list, [<class ImageHash> obj, ...]
    '''

    with Pool() as p:
        new_hashes = p.map(Image.calc_dhash, images_paths)
    return new_hashes

def images_constructor(image_paths, image_hashes):
    '''Returns a list of <class Image> objects ready
    for comparing

    :param image_paths: list of str, images' full paths,
    :param image_hashes: dict, {image_path: str,
                                image_hash: <class ImageHash> obj, ...},
    :returns: list of <class Image> objs
    '''

    return [Image(path, dhash=image_hashes[path], suffix=pathlib.Path(path).suffix)
            for path in image_paths]

def caching_images(paths, hashes, cached_hashes):
    '''Adds new images to the cache, save them on the disk
    and returns an updated dictionary with hashes

    :param paths: list of str, images' full paths,
    :param hashes: list of <class ImageHash> objs,
    :param cached_hashes: dict, {image_path: str,
                                 image_hash: <class ImageHash> obj}
    '''

    for i, path in enumerate(paths):
        cached_hashes[path] = hashes[i]

    save_cached_hashes(cached_hashes)

    return cached_hashes


class Image():
    '''Class that represents images'''

    def __init__(self, path, difference=0, dhash=None,
                 thumbnail=None, suffix=None):
        self.path = path
        self.difference = difference
        self.hash = dhash
        self.thumbnail = thumbnail
        self.suffix = suffix

    @staticmethod
    def calc_dhash(path):
        '''Calculates an image's difference hash using
        'dhash' function from 'imagehash' lib

        :param path: str, an image's path,
        :returns: <class ImageHash> instance,
        :raise OSError: if there's any problem with
                        opening or reading an image
        '''

        try:
            image = PILImage.open(path)
        except OSError as e:
            print(e)
            raise OSError(e)
        return imagehash.dhash(image)

    def get_dimensions(self):
        '''Returns an image dimensions

        :param path: str, full path to an image,
        :returns: tuple, (width: int, height: int),
        :raise OSError: if there's any problem with
                        opening or reading an image
        '''

        try:
            image = PILImage.open(self.path)
        except OSError as e:
            print(e)
            raise OSError(e)
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
                  rounded to the first decimal place,
        :raise ValueError: if :size_format: not amongst
                           the allowed values,
        :raise OSError: if the file does not exist or is
                        inaccessible
        '''

        try:
            image_size = os.path.getsize(self.path)
        except OSError as e:
            print(e)
            raise OSError(e)

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
    not_cached_paths = find_not_cached_images(paths, cached_hashes)
    print('{} images have been found in the cache'.format(
        len(paths)-len(not_cached_paths)
    ))

    if not_cached_paths:
        hashes = hashes_calculating(not_cached_paths)
        cached_hashes = caching_images(not_cached_paths, hashes, cached_hashes)
    images = images_constructor(paths, cached_hashes)

    image_groups = images_grouping(images, int(sensitivity))
    print('{} duplicate image groups have been found'.format(len(image_groups)))
    print('------------------------')
    print('Here are your duplicate images')
    for i, group in enumerate(image_groups):
        print('Group {}:'.format(i+1))
        print('------------------------')
        for image in group:
            print(image)
        print('------------------------')

    print('That is it')
    input('Press any key to continue...')
