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
        shutil.rmtree(cls.test_dir)

    #############################TESTS##################################

    def test_calc_dhash_returns_None_if_OSError(self):
        image = core.Image(self.txt)
        image.calc_dhash()
        self.assertIsNone(image.hash)

    def test_calc_dhash_returns_ImageHash_if_no_error(self):
        image = core.Image(self.img)
        image.calc_dhash()
        self.assertIsInstance(image.hash, imagehash.ImageHash)

    def test_get_dimensions_raises_OSError_if_pass_not_image(self):
        image = core.Image(self.txt)
        with self.assertRaises(OSError):
            image.get_dimensions()

    def test_get_dimensions_returns_correct_values(self):
        image = core.Image(self.img)
        size = image.get_dimensions()
        self.assertEqual(size[0], self.w)
        self.assertEqual(size[1], self.h)

    def test_get_scaling_dimensions_raises_ValueError_if_pass_not_positive(self):
        image = core.Image(self.img)
        for size in (-1, 0):
            with self.assertRaises(ValueError):
                image.get_scaling_dimensions(size)

    def test_get_scaling_dimensions_raises_OSError_if_pass_not_image(self):
        image = core.Image(self.txt)
        with self.assertRaises(OSError):
            image.get_scaling_dimensions(1)

    def test_get_scaling_dimensions_return_if_pass_square_image(self):
        image = core.Image(self.img)
        new_size = image.get_scaling_dimensions(self.w*2)
        self.assertEqual(new_size[0], self.w*2)
        self.assertEqual(new_size[1], self.h*2)

    def test_get_scaling_dimensions_return_if_pass_portrait_image(self):
        suffix = 'jpg'
        img = str(self.test_dir / 'portrait.{}'.format(suffix))
        w, h = 1, 5
        utils.make_image(img, w, h, suffix)
        image = core.Image(img)
        new_size = image.get_scaling_dimensions(h*2)
        self.assertEqual(new_size[0], w*2)
        self.assertEqual(new_size[1], h*2)

    def test_get_scaling_dimensions_return_if_pass_landscape_image(self):
        suffix = 'jpg'
        img = str(self.test_dir / 'landscape.{}'.format(suffix))
        w, h = 5, 1
        utils.make_image(img, w, h, suffix)
        image = core.Image(img)
        new_size = image.get_scaling_dimensions(w*2)
        self.assertEqual(new_size[0], w*2)
        self.assertEqual(new_size[1], h*2)

    def test_get_filesize_raises_OSError_if_pass_not_existing_file(self):
        not_existing = str(self.test_dir / 'not_existing.txt')
        image = core.Image(not_existing)
        with self.assertRaises(OSError):
            image.get_filesize()

    def test_get_filesize_raises_ValueError_if_pass_wrong_format(self):
        image = core.Image(self.img)
        with self.assertRaises(ValueError):
            image.get_filesize(size_format='Kg')

    def test_get_filesize_return_if_Bytes_format(self):
        image = core.Image(self.img)
        size = os.path.getsize(self.img)
        filesize = image.get_filesize(size_format='B')
        self.assertEqual(filesize, size)

    def test_get_filesize_return_if_KiloBytes_format(self):
        image = core.Image(self.img)
        size = round(os.path.getsize(self.img) / 1024, 1)
        filesize = image.get_filesize(size_format='KB')
        self.assertAlmostEqual(filesize, size)

    def test_get_filesize_return_if_MegaBytes_format(self):
        image = core.Image(self.img)
        size = round(os.path.getsize(self.img) / (1024**2), 1)
        filesize = image.get_filesize(size_format='MB')
        self.assertAlmostEqual(filesize, size)

    def test_delete_image_raises_OSError_if_pass_not_existing_file(self):
        not_existing = str(self.test_dir / 'not_existing.txt')
        image = core.Image(not_existing)
        with self.assertRaises(OSError):
            image.delete_image()

    def test_delete_image_deletes_image_correctly(self):
        suffix = 'jpg'
        img = str(self.test_dir / 'delete.{}'.format(suffix))
        utils.make_image(img, 1, 1, suffix)
        image = core.Image(img)
        self.assertTrue(os.path.exists(img))
        image.delete_image()
        self.assertFalse(os.path.exists(img))


class TestGetImagesPathsFunction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = pathlib.Path(tempfile.mkdtemp())

        # Sets with file names which suffixes are supported and not
        cls.supported = [str(cls.test_dir / 'image.{}'.format(suffix))
                         for suffix in ('.png', '.jpg', '.jpeg', '.bmp')]
        cls.unsupported = [str(cls.test_dir / 'image.{}'.format(suffix))
                           for suffix in ('.tiff', '.txt')]

        # Create the files in the temporary directory
        for filename in cls.supported + cls.unsupported:
            with open(filename, 'w') as f:
                f.write('Whatever...')

        # Also create a dir and add it to 'unsupported'
        dirs = str(cls.test_dir / 'dir')
        cls.unsupported.append(dirs)
        os.makedirs(dirs)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    ##############################TESTS#####################################

    def test_get_images_paths_returns_empty_list_if_pass_empty_folders(self):
        images = core.get_images_paths([])
        self.assertSequenceEqual(images, [])

    def test_get_images_paths_return_is_correct(self):
        paths = set(core.get_images_paths([self.test_dir]))
        for path in paths:
            self.assertIn(path, self.supported)
            self.assertNotIn(path, self.unsupported)


class TestCacheFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = pathlib.Path(tempfile.mkdtemp())

        # Sets with file names that are cached and not
        cls.cached = [str(cls.test_dir / 'image.{}'.format(suffix))
                      for suffix in ('.png', '.jpg', '.jpeg', '.bmp')]
        cls.not_cached = [str(cls.test_dir / 'image.{}'.format(suffix))
                          for suffix in ('.tiff', '.txt')]

        # Make cache
        cls.cache = {filename: 666 for filename in cls.cached}
        cls.cache_path = str(cls.test_dir / 'cache.p')
        with open(cls.cache_path, 'wb') as f:
            pickle.dump(cls.cache, f)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    ##############################TESTS#####################################

    def test_load_cached_hashes_returns_empty_dict_if_pass_not_existing_cache_file(self):
        loaded = core.load_cached_hashes(str(self.test_dir / 'no_hashes.p'))
        self.assertDictEqual(loaded, {})

    def test_load_cached_hashes_loads_cache_file_correctly(self):
        loaded = core.load_cached_hashes(self.cache_path)
        self.assertDictEqual(loaded, self.cache)

    def test_check_cache_returns_empty_lists_if_pass_empty_paths(self):
        paths, cache = [], {}
        cached, not_cached = core.check_cache(paths, cache)
        self.assertListEqual(cached, [])
        self.assertListEqual(not_cached, [])

    def test_check_cache_returns_empty_cached_list_if_pass_empty_cache(self):
        cache = {}
        cached, _ = core.check_cache(self.not_cached, cache)
        self.assertListEqual(cached, [])

    def test_check_cache_returns_correct_cached_list_if_pass_not_empty_cache(self):
        cached, _ = core.check_cache(self.cached, self.cache)

        for image in cached:
            self.assertIn(image.path, self.cache)
            self.assertEqual(image.hash, self.cache[image.path])

    def test_check_cache_returns_correct_not_cached_list_if_pass_not_empty_cache(self):
        expected_images = [core.Image(path, suffix=pathlib.Path(path).suffix)
                           for path in self.not_cached]
        _, not_cached = core.check_cache(self.not_cached, self.cache)

        for i, _ in enumerate(not_cached):
            self.assertEqual(expected_images[i].suffix, not_cached[i].suffix)
            self.assertEqual(expected_images[i].path, not_cached[i].path)

    def test_caching_images_saves_cache_correctly(self):
        images = [core.Image(path, dhash=666) for path in self.cached]
        cache = {}
        cache_path = str(self.test_dir / 'new_cache.p')
        core.caching_images(images, cache, cache_path)

        # And now read cache and compare it with the expected_cache
        with open(cache_path, 'rb') as f:
            cached_hashes = pickle.load(f)

        self.assertDictEqual(cached_hashes, self.cache)


class TestImagesGroupingFunction(unittest.TestCase):

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
    def image_factory(cls, num, filename, dhash):
        '''Create <class Image> instances'''

        images = []

        for i in range(num):
            val = None if dhash is None else cls.Number(dhash)
            name, suffix = filename.split('.')
            name = str(cls.test_dir / '{}{}{}'.format(name, i, suffix))
            images.append(core.Image(name, dhash=val))

        return images

    @classmethod
    def setUpClass(cls):
        cls.test_dir = pathlib.Path(tempfile.mkdtemp())

        # Create readable images
        cls.red = cls.image_factory(3, 'red.jpg', 30)
        cls.yellow = cls.image_factory(2, 'yellow.jpg', 20)
        cls.green = cls.image_factory(1, 'green.jpg', 10)

        # Create 'corrupted' images (cannot be open without errors)
        cls.corrupted = cls.image_factory(3, 'corrupted.png', None)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    ##############################TESTS#####################################

    def test_images_grouping_returns_empty_list_if_pass_empty_or_with_one_image_list(self):
        images = []
        image_groups = core.images_grouping(images, 0)
        self.assertListEqual(image_groups, [])

        images = [core.Image(path='any.png')]
        image_groups = core.images_grouping(images, 0)
        self.assertListEqual(image_groups, [])

    def test_images_grouping_returns_duplicate_images(self):
        images = self.red + self.yellow + self.green + self.corrupted
        image_groups = core.images_grouping(images, 0)

        # In 'red' - 3 images, in 'yellow' - 2
        if len(image_groups[0]) > len(image_groups[1]):
            red, yellow = set(image_groups[0]), set(image_groups[1])
        else:
            red, yellow = set(image_groups[1]), set(image_groups[0])

        self.assertSetEqual(red, set(self.red))
        self.assertSetEqual(yellow, set(self.yellow))

    def test_images_grouping_doesnt_return_not_duplicateor_corrupted_images(self):
        images = self.red + self.yellow + self.green + self.corrupted
        image_groups = core.images_grouping(images, 0)

        flat_groups = [image for group in image_groups for image in group]

        for image in self.green:
            self.assertNotIn(image, flat_groups)

        for image in self.corrupted:
            self.assertNotIn(image, flat_groups)


if __name__ == '__main__':
    unittest.main()
