'''Functions to process images and find duplicates'''

import os

import imagehash
from PIL import Image as pilimage


def get_images_paths(folders):
    '''Return all the images' full paths from
    the passed 'folders' argument

    :param folders: a collection of folders' paths,
    :returns: list, images' full paths
    '''

    IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
    images_paths = []

    for path in folders:
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                full_path = os.path.join(path, dirpath, filename)
                if os.path.isfile(full_path):
                    end = filename.split('.')[-1].lower()
                    if end in IMG_EXTENSIONS:
                        images_paths.append(full_path)
    return images_paths

def images_grouping(images):
    '''Return groups of similar images

    :param images: collection of <class Image> objects,
    :returns: list, [[<class Image> obj 1.1, <class Image> obj 1.2, ...],
                     [<class Image> obj 2.1, <class Image> obj 2.2, ...], ...]
    '''

    SENSITIVITY = 10

    image_groups = []
    for i in range(len(images)-1):
        image_groups.append([images[i]])
        for j in range(i+1, len(images)):
            diff = images[i].phash - images[j].phash
            if diff <= SENSITIVITY:
                images[j].difference = diff
                image_groups[-1].append(images[j])
        if len(image_groups[-1]) == 1:
            image_groups.pop()
        else:
            image_groups[-1].sort(key=lambda x: x.difference)
    return image_groups

def image_processing(folders):
    '''Process images to find the duplicates

    :param folders: collection of str, folders to process,
    :returns: list, [[<class Image> obj 1.1, <class Image> obj 1.2, ...],
                     [<class Image> obj 2.1, <class Image> obj 2.2, ...], ...]
    '''

    paths = get_images_paths(folders)
    images = [Image(path) for path in paths]
    return images_grouping(images)


class Image():
    '''Class that represents images'''

    def __init__(self, path, difference=0):
        self.path = path
        self.difference = difference
        self.phash = self.calc_phash()
        self.dimensions = self.get_dimensions()
        self.filesize = self.get_filesize()

    def calc_phash(self):
        '''Calculate an image's perceptual hash using
        'phash' function from 'imagehash' lib

        :returns: <class ImageHash> instance
        '''

        return imagehash.phash(pilimage.open(self.path))

    def get_dimensions(self):
        '''Return an image dimensions

        :param path: str, full path to an image,
        :returns: tuple, (width: int, height: int)
        '''

        return pilimage.open(self.path).size

    def get_filesize(self, size_format='KB'):
        '''Return an image file size

        :param size_format: str, ('B', 'KB', 'MB'),
        :returns: float, file size in bytes, kilobytes or megabytes,
                  rounded to the first decimal place,
        :raise ValueError: raise exception if :size_format:
                           not amongst the allowed values
        '''

        image_size = os.path.getsize(self.path)

        if size_format == 'B':
            return image_size
        if size_format == 'KB':
            return round(image_size / 1024, 1)
        if size_format == 'MB':
            return round(image_size / (1024**2), 1)

        raise ValueError('Wrong size format')

    def delete_image(self):
        '''Delete an image from the disk'''

        os.remove(self.path)
