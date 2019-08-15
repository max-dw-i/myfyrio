import logging
import os
import pathlib
import shutil
import tempfile
from unittest import TestCase, mock

from doppelganger import core

logging.lastResort = None
CORE = 'doppelganger.core.'


class TestImageClass(TestCase):

    def setUp(self):
        self.image = core.Image('image.png', dhash='not_None_hash')

    @mock.patch(CORE + 'PILImage.open', side_effect=OSError)
    def test_calc_dhash_assign_None_to_hash_attr_if_OSError(self, mock_open):
        self.image.calc_dhash()
        self.assertIsNone(self.image.hash)

    @mock.patch(CORE + 'dhash.dhash_int', return_value='hash')
    @mock.patch(CORE + 'PILImage.open')
    def test_undecorated_calc_dhash_returns_dhash(self, mock_open, mock_dhash):
        result = self.image.calc_dhash.__wrapped__(self.image)
        self.assertEqual(self.image.hash, 'hash')
        self.assertEqual(result, self.image.hash)

    def test_decorated_calc_dhash_returns_Image_object(self):
        result = self.image.calc_dhash()
        self.assertIsInstance(result, core.Image)

    @mock.patch(CORE + 'PILImage.open', side_effect=OSError)
    def test_get_dimensions_raises_OSError(self, mock_open):
        with self.assertRaises(OSError):
            self.image.get_dimensions()

    @mock.patch(CORE + 'PILImage.open')
    def test_get_dimensions_returns_correct_values(self, mock_open):
        img = core.PILImage.Image()
        img._size = (13, 666)
        mock_open.return_value = img

        size = self.image.get_dimensions()

        self.assertEqual(size[0], 13)
        self.assertEqual(size[1], 666)

    def test_get_scaling_dimensions_raises_ValueError_if_pass_not_positive(self):
        for size in (-1, 0):
            with self.assertRaises(ValueError):
                self.image.get_scaling_dimensions(size)

    @mock.patch(CORE + 'Image.get_dimensions', side_effect=OSError)
    def test_get_scaling_dimensions_raises_OSError(self, mock_dim):
        with self.assertRaises(OSError):
            self.image.get_scaling_dimensions(1)

    @mock.patch(CORE + 'Image.get_dimensions')
    def test_get_scaling_dimensions_return_if_pass_square_image(self, mock_dim):
        w, h = 5, 5
        mock_dim.return_value = (w, h)
        new_size = self.image.get_scaling_dimensions(w*2)
        self.assertEqual(new_size[0], w*2)
        self.assertEqual(new_size[1], h*2)

    @mock.patch(CORE + 'Image.get_dimensions')
    def test_get_scaling_dimensions_return_if_pass_portrait_image(self, mock_dim):
        w, h = 1, 5
        mock_dim.return_value = (w, h)
        new_size = self.image.get_scaling_dimensions(h*2)
        self.assertEqual(new_size[0], w*2)
        self.assertEqual(new_size[1], h*2)

    @mock.patch(CORE + 'Image.get_dimensions')
    def test_get_scaling_dimensions_return_if_pass_landscape_image(self, mock_dim):
        w, h = 5, 1
        mock_dim.return_value = (w, h)
        new_size = self.image.get_scaling_dimensions(w*2)
        self.assertEqual(new_size[0], w*2)
        self.assertEqual(new_size[1], h*2)

    @mock.patch(CORE + 'os.path.getsize', side_effect=OSError)
    def test_get_filesize_raises_OSError(self, mock_size):
        with self.assertRaises(OSError):
            self.image.get_filesize()

    @mock.patch(CORE + 'os.path.getsize')
    def test_get_filesize_raises_ValueError_if_pass_wrong_format(self, mock_size):
        with self.assertRaises(ValueError):
            self.image.get_filesize(size_format='Kg')

    @mock.patch(CORE + 'os.path.getsize', return_value=1024)
    def test_get_filesize_return_if_Bytes_format(self, mock_size):
        filesize = self.image.get_filesize(size_format='B')
        self.assertEqual(filesize, 1024)

    @mock.patch(CORE + 'os.path.getsize', return_value=1024)
    def test_get_filesize_return_if_KiloBytes_format(self, mock_size):
        filesize = self.image.get_filesize(size_format='KB')
        self.assertAlmostEqual(filesize, 1)

    @mock.patch(CORE + 'os.path.getsize', return_value=1048576)
    def test_get_filesize_return_if_MegaBytes_format(self, mock_size):
        filesize = self.image.get_filesize(size_format='MB')
        self.assertAlmostEqual(filesize, 1)

    @mock.patch(CORE + 'os.remove', side_effect=OSError)
    def test_delete_image_raises_OSError(self, mock_remove):
        with self.assertRaises(OSError):
            self.image.delete_image()

    @mock.patch(CORE + 'os.remove')
    def test_delete_image_called(self, mock_remove):
        self.image.delete_image()
        self.assertTrue(mock_remove.called)


class TestGetImagesPathsFunction(TestCase):

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

        # Also create dirs and add them to 'unsupported'
        for d in ('dir', 'dir.jpg'):
            dirs = str(cls.test_dir / d)
            cls.unsupported.append(dirs)
            os.makedirs(dirs)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    def test_get_images_paths_returns_empty_list_if_pass_empty_folders(self):
        images = core.get_images_paths([])
        self.assertSequenceEqual(images, [])

    def test_get_images_paths_return(self):
        paths = set(core.get_images_paths([self.test_dir]))
        for path in paths:
            self.assertIn(path, self.supported)
            self.assertNotIn(path, self.unsupported)


class TestCacheFunctions(TestCase):

    @classmethod
    def setUpClass(cls):
        # Sets with file names that are cached and not
        cls.cached = ['image.{}'.format(suffix)
                      for suffix in ('.png', '.jpg', '.jpeg', '.bmp')]
        cls.not_cached = ['image.{}'.format(suffix)
                          for suffix in ('.tiff', '.txt')]

        # Make cache
        cls.cache = {filename: 666 for filename in cls.cached}

    @mock.patch(CORE + 'open', side_effect=FileNotFoundError)
    def test_load_cached_hashes_returns_empty_dict_if_FileNotFoundError(self, mock_cache):
        loaded = core.load_cached_hashes()
        self.assertDictEqual(loaded, {})

    @mock.patch(CORE + 'pickle.load', side_effect=EOFError)
    def test_load_cached_hashes_raises_EOFError_if_EOFError(self, mock_cache):
        with self.assertRaises(EOFError):
            core.load_cached_hashes()

    @mock.patch(CORE + 'pickle.load')
    def test_load_cached_hashes_return(self, mock_cache):
        mock_cache.return_value = self.cache
        loaded = core.load_cached_hashes()
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

    def test_check_cache_returns_correct_cached_list(self):
        cached, _ = core.check_cache(self.cached, self.cache)

        for image in cached:
            self.assertIn(image.path, self.cache)
            self.assertEqual(image.hash, self.cache[image.path])

    def test_check_cache_returns_correct_not_cached_list(self):
        expected_images = [core.Image(path, suffix=pathlib.Path(path).suffix)
                           for path in self.not_cached]
        _, not_cached = core.check_cache(self.not_cached, self.cache)

        for i, _ in enumerate(not_cached):
            self.assertEqual(expected_images[i].suffix, not_cached[i].suffix)
            self.assertEqual(expected_images[i].path, not_cached[i].path)

    @mock.patch(CORE + 'pickle.dump')
    @mock.patch(CORE + 'open')
    def test_caching_images(self, mock_open, mock_cache):
        '''!!! BE AWARE WHEN CHANGE THIS TEST. IF THERE'S
        AN ALREADY POPULATED CACHE FILE AND YOU DON'T PATCH
        OPEN(), YOU'LL REWRITE THE FILE
        '''

        images = [core.Image(path, dhash=666) for path in self.cached]
        core.caching_images(images, {})

        self.assertTrue(mock_cache.called)


class TestImagesGroupingFunction(TestCase):

    @classmethod
    def image_factory(cls, num, filename, dhash):
        '''Create <class Image> instances'''

        images = []

        for i in range(num):
            name, suffix = filename.split('.')
            name = '{}{}{}'.format(name, i, suffix)
            images.append(core.Image(name, dhash=dhash))

        return images

    @classmethod
    def setUpClass(cls):
        # Create readable images
        cls.red = cls.image_factory(3, 'red.jpg', 30)
        cls.yellow = cls.image_factory(2, 'yellow.jpg', 20)
        cls.green = cls.image_factory(1, 'green.jpg', 10)

        # Create 'corrupted' images (cannot be open without errors)
        cls.corrupted = cls.image_factory(3, 'corrupted.png', None)

    def test_images_grouping_returns_empty_list_if_pass_zero_or_one_len_list(self):
        images = []
        image_groups = core.images_grouping(images, 0)
        self.assertListEqual(image_groups, [])

        images = [core.Image(path='any.png')]
        image_groups = core.images_grouping(images, 0)
        self.assertListEqual(image_groups, [])

    def test_images_grouping_returns_duplicate_images(self):
        images = self.red + self.yellow + self.green
        image_groups = core.images_grouping(images, 0)

        # In 'red' - 3 images, in 'yellow' - 2
        if len(image_groups[0]) > len(image_groups[1]):
            red, yellow = set(image_groups[0]), set(image_groups[1])
        else:
            red, yellow = set(image_groups[1]), set(image_groups[0])

        self.assertSetEqual(red, set(self.red))
        self.assertSetEqual(yellow, set(self.yellow))

    def test_images_grouping_raises_TypeError(self):
        images = self.corrupted
        with self.assertRaises(TypeError):
            core.images_grouping(images, 0)
