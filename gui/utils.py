import os

from PIL import Image


def get_image_size(path):
    return Image.open(path).size

def get_image_weight(path, size_format='KB'):
    image_size = os.path.getsize(path)

    if size_format == 'B':
        return image_size
    if size_format == 'KB':
        return round(image_size / 1024)
    if size_format == 'MB':
        return round(image_size / (1024**2))

    raise ValueError('Wrong size format')
