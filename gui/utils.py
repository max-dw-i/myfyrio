'''Some functions that are not directly related to the different program modules
 are implemented in here
 '''

import os

from PIL import Image


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

def get_image_dimensions(path):
    '''Return an image dimensions

    :param path: str, full path to an image,
    :returns: tuple, (width: int, height: int)
    '''

    return Image.open(path).size

def get_image_filesize(path, size_format='KB'):
    '''Return an image file size

    :param path: str, full path to an image,
    :param size_format: str, ('B', 'KB', 'MB'),
    :returns: float, file size in bytes, kilobytes or megabytes,
              rounded to the first decimal place,
    :raise ValueError: raise exception if :size_format:
                       not amongst the allowed values
    '''

    image_size = os.path.getsize(path)

    if size_format == 'B':
        return image_size
    if size_format == 'KB':
        return round(image_size / 1024, 1)
    if size_format == 'MB':
        return round(image_size / (1024**2), 1)

    raise ValueError('Wrong size format')

def get_image_size(image_path):
    '''Return info about image dimensions and file size

    :param image_path: str, image full path,
    :returns: str, string with format '{width}x{height}, {file_size} {units}'
    '''

    units = 'KB'
    image_dimensions = get_image_dimensions(image_path)
    file_size = get_image_filesize(image_path, units)
    image_params = {'width': image_dimensions[0], 'height': image_dimensions[1],
                    'file_size': file_size, 'units': units}
    return '{width}x{height}, {file_size} {units}'.format(**image_params)

def delete_image(image):
    '''Delete image from the disk

    :param images: str, full path to an image
    '''

    os.remove(image)
