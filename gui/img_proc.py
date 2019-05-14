import os

import imagehash
from PIL import Image


def get_images_paths(paths):
    IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'thm'}
    images_paths = []

    for path in paths:
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                full_path = os.path.join(path, dirpath, filename)
                if os.path.isfile(full_path):
                    end = filename.split('.')[-1].lower()
                    if end in IMG_EXTENSIONS:
                        images_paths.append(full_path)
    return images_paths

def phash(image_path):
    return imagehash.phash(Image.open(image_path))

def images_phashes(images_paths):
    return [phash(path) for path in images_paths]

def processing(path_list):
    paths = get_images_paths(path_list)
    phashes = images_phashes(paths)
