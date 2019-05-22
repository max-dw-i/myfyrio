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

    SENSITIVITY = 100

    # Here all the hashes are compared to each other and the nearest (most
    # similar images) are added to list 'closest_images'.
    closest_images = []
    final_groups = {}
    for i, image1 in enumerate(images):
        closest_images.append((None, float('inf')))
        for j, image2 in enumerate(images):
            diff = image1.phash - image2.phash
            # If the difference less/equal than SENSITIVITY and this image (image2)
            # is closer to image1, we add a tuple (image2 index, hash difference)
            # to an image to the list. So the list looks like this: [(1, 7), (3, 4), ...].
            # 0th image is the closest to 1th image and they have hash difference 7, etc.
            if diff <= SENSITIVITY and i != j and closest_images[i][1] > diff:
                closest_images[i] = (j, diff)

        j = closest_images[i][0] # the closest image to the ith image (its index)
        diff = closest_images[i][1] # hash difference between the ith and jth images
        # If ith image has the closest one...
        if j is not None:
            # ...if jth image has been added already to 'final_groups'...
            if j in final_groups:
                # ...and ith image is not amongst the added to some group, add it,
                if i not in final_groups[j]:
                    images[i].difference = diff
                    final_groups[j].add(i)
            else:
                # else add a new group to 'final_groups'
                images[j].difference = diff
                final_groups[i] = {j}

        # So 'final_groups' dictionary looks like this: {0: {1, 2, 3}, 4: {5}...},
        # when 0, 1, 2, 3 images are in one group, 4 and 5 are in another group, etc.

    image_groups_to_render = []
    key = lambda x: x.difference # sort images using hash differences
    for group in final_groups:
        image_groups_to_render.append(
            [images[group]] + sorted([images[j] for j in final_groups[group]], key=key)
        )

    return image_groups_to_render

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
