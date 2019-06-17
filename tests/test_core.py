import os
import pathlib
import pickle
import shutil
import tempfile
import unittest

import imagehash

from tests import utils
from doppelganger import core


class TestImageClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a temporary directory
        cls.test_dir = pathlib.Path(tempfile.mkdtemp())

        # Create an image
        suffix = 'jpg'
        cls.img = str(cls.test_dir / 'image.{}'.format(suffix))
        cls.w, cls.h = 1, 1
        utils.make_image(cls.img, cls.w, cls.h, suffix)

        # Create not an image
        cls.txt = str(cls.test_dir / 'text.txt')
        with open(cls.txt, 'w') as f:
            f.write('Not an image')

    @classmethod
    def tearDownClass(cls):
        # Remove the directory after the test
        shutil.rmtree(cls.test_dir)

    #############################TESTS##################################

    def test_calc_dhash_returns_OSError(self):
        image = core.Image(self.txt)
        image.calc_dhash()
        self.assertIsNone(image.hash)

    def test_calc_dhash_returns_no_error(self):
        image = core.Image(self.img)
        image.calc_dhash()
        self.assertIsInstance(image.hash, imagehash.ImageHash)

    def test_get_dimensions_returns_OSError(self):
        image = core.Image(self.txt)
        with self.assertRaises(OSError):
            image.get_dimensions()

    def test_get_dimensions_returns_no_error(self):
        image = core.Image(self.img)
        size = image.get_dimensions()
        self.assertEqual(size[0], self.w)
        self.assertEqual(size[1], self.h)

    def test_get_scaling_dimensions_ValueError(self):
        image = core.Image(self.img)
        for size in (-1, 0):
            with self.assertRaises(ValueError):
                image.get_scaling_dimensions(size)

    def test_get_scaling_dimensions_OSError(self):
        image = core.Image(self.txt)
        with self.assertRaises(OSError):
            image.get_scaling_dimensions(1)

    def test_get_scaling_dimensions_square_image(self):
        image = core.Image(self.img)
        new_size = image.get_scaling_dimensions(self.w*2)
        self.assertEqual(new_size[0], self.w*2)
        self.assertEqual(new_size[1], self.h*2)

    def test_get_scaling_dimensions_portrait_image(self):
        suffix = 'jpg'
        img = str(self.test_dir / 'portrait.{}'.format(suffix))
        w, h = 1, 5
        utils.make_image(img, w, h, suffix)
        image = core.Image(img)
        new_size = image.get_scaling_dimensions(h*2)
        self.assertEqual(new_size[0], w*2)
        self.assertEqual(new_size[1], h*2)

    def test_get_scaling_dimensions_landscape_image(self):
        suffix = 'jpg'
        img = str(self.test_dir / 'landscape.{}'.format(suffix))
        w, h = 5, 1
        utils.make_image(img, w, h, suffix)
        image = core.Image(img)
        new_size = image.get_scaling_dimensions(w*2)
        self.assertEqual(new_size[0], w*2)
        self.assertEqual(new_size[1], h*2)

    def test_get_filesize_OSError(self):
        not_existing = str(self.test_dir / 'not_existing.txt')
        image = core.Image(not_existing)
        with self.assertRaises(OSError):
            image.get_filesize()

    def test_get_filesize_ValueError(self):
        image = core.Image(self.img)
        with self.assertRaises(ValueError):
            image.get_filesize(size_format='Kg')

    def test_get_filesize_Bytes(self):
        image = core.Image(self.img)
        size = os.path.getsize(self.img)
        filesize = image.get_filesize(size_format='B')
        self.assertEqual(filesize, size)

    def test_get_filesize_KiloBytes(self):
        image = core.Image(self.img)
        size = round(os.path.getsize(self.img) / 1024, 1)
        filesize = image.get_filesize(size_format='KB')
        self.assertAlmostEqual(filesize, size)

    def test_get_filesize_MegaBytes(self):
        image = core.Image(self.img)
        size = round(os.path.getsize(self.img) / (1024**2), 1)
        filesize = image.get_filesize(size_format='MB')
        self.assertAlmostEqual(filesize, size)

    def test_delete_image_OSError(self):
        not_existing = str(self.test_dir / 'not_existing.txt')
        image = core.Image(not_existing)
        with self.assertRaises(OSError):
            image.delete_image()

    def test_delete_image_no_error(self):
        suffix = 'jpg'
        img = str(self.test_dir / 'delete.{}'.format(suffix))
        utils.make_image(img, 1, 1, suffix)
        image = core.Image(img)
        self.assertTrue(os.path.exists(img))
        image.delete_image()
        self.assertFalse(os.path.exists(img))


class TestImageProcessingFunctions(unittest.TestCase):

    class Number:
        '''When <class ImageHash> instances is subtracted
        from another, an absolute value is returned. In order
        not to change (add abs()) the code because of the tests,
        this class is used.
        '''

        def __init__(self, x):
            self.x = x

        def __sub__(self, num):
            return abs(self.x - num.x)

    @classmethod
    def make_images(cls, number, name, suffix, filenames, dhash):
        '''Create files and <class Image> instances'''

        images = []

        for i in range(number):
            filename = str(cls.test_dir / '{name}{i}{suffix}'.format(
                name=name,
                i=i,
                suffix=suffix
            ))
            filenames.append(filename)
            with open(filename, 'w') as f:
                f.write('Whatever...')

            val = None if dhash is None else cls.Number(dhash)
            images.append(core.Image(filename, dhash=val))

        return images

    @classmethod
    def setUpClass(cls):
        # Create a temporary directory
        cls.test_dir = pathlib.Path(tempfile.mkdtemp())

        # Create good images
        cls.good_paths = [] # The paths of the images which hashes are ok
        cls.red = cls.make_images(3, 'red', '.jpg', cls.good_paths, 30)
        cls.yellow = cls.make_images(2, 'yellow', '.jpg', cls.good_paths, 20)
        cls.green = cls.make_images(1, 'green', '.jpg', cls.good_paths, 10)

        # Create 'corrupted' images (cannot be open without errors)
        cls.bad_paths = [] # The paths of the images which hashes are not ok
        cls.corrupted = [] # 'Corrupted' images
        for suffix in ('.bmp', '.jpeg', '.png'):
            cls.corrupted.extend(cls.make_images(1, 'corrupted', suffix,
                                                 cls.bad_paths, None))

    @classmethod
    def tearDownClass(cls):
        # Remove the directory after the test
        shutil.rmtree(cls.test_dir)

    ##############################TESTS#####################################

    def test_get_images_paths_empty_folders(self):
        images = core.get_images_paths([])
        self.assertSequenceEqual(images, [])

    def test_get_images_paths(self):
        # Make files with not supported suffixes and a directory
        # to test that they won't be in the 'paths'
        not_supported_suffixes = []
        self.make_images(1, 'not_supported', '.tiff', not_supported_suffixes, None)
        dirs = str(self.test_dir / 'not_image')
        not_supported_suffixes.append(dirs)
        os.makedirs(dirs)

        paths = set(core.get_images_paths([self.test_dir]))
        # The suffixes in 'good_paths' and 'bad_paths' are supported
        for name in self.good_paths + self.bad_paths:
            self.assertIn(name, paths)
        for name in not_supported_suffixes:
            self.assertNotIn(name, paths)

    def test_load_cached_hashes_FileNotFoundError(self):
        loaded = core.load_cached_hashes(str(self.test_dir / 'no_hashes.p'))
        self.assertDictEqual(loaded, {})

    def test_load_cached_hashes(self):
        # Create cache, write it on the disk and try to read
        cache_path = str(self.test_dir / 'test_hashes.p')
        cache = {'image.jpg': 1}
        with open(cache_path, 'wb') as f:
            pickle.dump(cache, f)

        loaded = core.load_cached_hashes(cache_path)
        self.assertDictEqual(loaded, cache)

    def test_check_cache_empty_paths(self):
        paths, cache = [], {}
        cached, not_cached = core.check_cache(paths, cache)
        self.assertListEqual(cached, [])
        self.assertListEqual(not_cached, [])

    def test_check_cache_empty_cache(self):
        cache = {}
        images_to_get = [core.Image(path, suffix=pathlib.Path(path).suffix)
                         for path in self.good_paths]
        cached, not_cached = core.check_cache(self.good_paths, cache)

        self.assertListEqual(cached, [])

        for i, _ in enumerate(not_cached):
            self.assertEqual(images_to_get[i].suffix, not_cached[i].suffix)
            self.assertEqual(images_to_get[i].path, not_cached[i].path)

    def test_check_cache_not_empty_cache(self):
        # Assume that images from 'bad_paths' are cached...
        cache = {path: 666 for path in self.bad_paths}
        # ...and from 'good_paths' are not
        images_to_get = [core.Image(path, suffix=pathlib.Path(path).suffix)
                         for path in self.good_paths]
        cached, not_cached = core.check_cache(self.good_paths, cache)

        for image in cached:
            self.assertIn(image.path, cache)
            self.assertEqual(image.hash, cache[image.path])
            self.assertEqual(image.suffix,
                             pathlib.Path(cache[image.path]).suffix)

        for i, _ in enumerate(not_cached):
            self.assertEqual(images_to_get[i].suffix, not_cached[i].suffix)
            self.assertEqual(images_to_get[i].path, not_cached[i].path)

    def test_caching_images(self):
        cache = {}
        cache_path = str(self.test_dir / 'test_hashes.p')
        images = [core.Image(path, dhash=666) for path in self.good_paths]
        cache_to_get = {path: 666 for path in self.good_paths}

        core.caching_images(images, cache, cache_path)

        # And now read cache and compare it with 'cache_to_get'
        with open(cache_path, 'rb') as f:
            cached_hashes = pickle.load(f)

        self.assertDictEqual(cached_hashes, cache_to_get)

    def test_images_grouping_0_or_1_images(self):
        images = []
        image_groups = core.images_grouping(images, 0)
        self.assertListEqual(image_groups, [])

        images = [core.Image(path='any.png')]
        image_groups = core.images_grouping(images, 0)
        self.assertListEqual(image_groups, [])

    def test_images_grouping(self):
        images = self.red + self.yellow + self.green + self.corrupted
        image_groups = core.images_grouping(images, 0)

        # In 'red' - 3 images, in 'yellow' - 2
        if len(image_groups[0]) > len(image_groups[1]):
            red, yellow = set(image_groups[0]), set(image_groups[1])
        else:
            red, yellow = set(image_groups[1]), set(image_groups[0])

        self.assertSetEqual(red, set(self.red))
        self.assertSetEqual(yellow, set(self.yellow))

        for image in self.corrupted:
            self.assertNotIn(image, red)
            self.assertNotIn(image, yellow)


if __name__ == '__main__':
    unittest.main()
