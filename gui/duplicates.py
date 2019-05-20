'''Functions to process images and find duplicates'''

import imagehash
from PIL import Image

from . import utils


def phash(image_path):
    '''Calculate an image's perceptual hash using
    'phash' function from 'imagehash' lib

    :param image_path: str, full path to an image,
    :returns: <class ImageHash> instance
    '''

    return imagehash.phash(Image.open(image_path))

def images_phashes(images_paths):
    '''Calculate images' perceptual hashes

    :param images_paths: collection of str, full paths to images,
    :returns: list of tuples,
              (full image path: str,
              image phash: <class ImageHash> instance)
    '''

    return [(path, phash(path)) for path in images_paths]

def phashes_grouping(phashes):
    '''Groups of similar images

    :param phashes: list of tuples,
                    (full image path: str,
                    image phash: <class ImageHash> instance),
    :returns: list, [[(image path 1.1: str, distance between hashes: int),
                      (image path 1.2: str, distance between hashes: int),
                      ...],
                     [(image path 2.1: str, distance between hashes: int),
                      (image path 2.2: str, distance between hashes: int),
                      ...],
                    ...]
    '''

    sensitivity = 10
    phashes_groups = []
    for i in range(len(phashes)-1):
        phashes_groups.append([(phashes[i][0], 0)])
        for j in range(i+1, len(phashes)):
            diff = phashes[i][1] - phashes[j][1]
            if diff <= sensitivity:
                phashes_groups[len(phashes_groups)-1].append((phashes[j][0], diff))
        if len(phashes_groups[len(phashes_groups)-1]) == 1:
            phashes_groups.pop()
        else:
            phashes_groups[len(phashes_groups)-1].sort(key=lambda x: x[1])
    return phashes_groups

def image_processing(folders):
    '''Process images to find the duplicates

    :param folders: collection of str, folders to process,
    :returns: list, [[(image path 1.1: str, distance between hashes: int),
                      (image path 1.2: str, distance between hashes: int),
                      ...],
                     [(image path 2.1: str, distance between hashes: int),
                      (image path 2.2: str, distance between hashes: int),
                      ...],
                    ...]
    '''

    paths = utils.get_images_paths(folders)
    phashes = images_phashes(paths)
    return phashes_grouping(phashes)
