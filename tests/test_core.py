'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Doppelgänger.

Doppelgänger is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Doppelgänger is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Doppelgänger. If not, see <https://www.gnu.org/licenses/>.


This file incorporates work covered by the following copyright and
permission notice:

    MIT License

    Copyright (c) 2019 Maxim Shpak <maxim.shpak@posteo.uk>

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files
    (the "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to permit
    persons to whom the Software is furnished to do so, subject to
    the following conditions:

        The above copyright notice and this permission notice shall be
        included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
'''

import pathlib
from unittest import TestCase, mock

from doppelganger import core

CORE = 'doppelganger.core.'


# pylint: disable=unused-argument,missing-class-docstring,protected-access


class TestFindImagesFunction(TestCase):

    def setUp(self):
        self.mock_path = mock.Mock()

    def test_return_empty_set_if_pass_empty_folders_list(self):
        paths = core.find_images([])

        self.assertSetEqual(paths, set())

    def test_raise_FileNotFoundError(self):
        self.mock_path.exists.return_value = False
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            with self.assertRaises(FileNotFoundError):
                core.find_images(['folder'])

    def test_call_search_with_path_and_recursive_parameters(self):
        self.mock_path.exists.return_value = True
        recursive = True
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            with mock.patch(CORE+'_search', return_value=set()) as mock_search:
                core.find_images(['folder'], recursive=recursive)

        mock_search.assert_called_once_with(self.mock_path, recursive)

    def test_search_resulting_paths(self):
        self.mock_path.exists.return_value = True
        paths = {'path'}
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            with mock.patch(CORE+'_search', return_value=paths):
                res = core.find_images(['folder'])

        self.assertSetEqual(res, paths)


class TestSearchFunc(TestCase):

    def setUp(self):
        self.mock_path = mock.Mock()

    def test_patterns_if_recursive_parameter_is_True(self):
        self.mock_path.glob.return_value = []
        core._search(self.mock_path, recursive=True)
        calls = [mock.call('**/*.png'), mock.call('**/*.jpg'),
                 mock.call('**/*.jpeg'), mock.call('**/*.bmp')]

        self.mock_path.glob.assert_has_calls(calls)

    def test_patterns_if_recursive_parameter_is_False(self):
        self.mock_path.glob.return_value = []
        core._search(self.mock_path, recursive=False)
        calls = [mock.call('*.png'), mock.call('*.jpg'),
                 mock.call('*.jpeg'), mock.call('*.bmp')]

        self.mock_path.glob.assert_has_calls(calls)

    def test_search_return_empty_set_if_glob_return_empty_list(self):
        self.mock_path.glob.return_value = []
        res = core._search(self.mock_path, True)

        self.assertSetEqual(res, set())

    def test_search_add_path_if_it_is_file(self):
        returned_path = mock.Mock()
        returned_path.is_file.return_value = True
        self.mock_path.glob.return_value = [returned_path]
        res = core._search(self.mock_path, True)

        self.assertSetEqual(res, {str(returned_path)})

    def test_search_add_path_if_it_is_not_file(self):
        returned_path = mock.Mock()
        returned_path.is_file.return_value = False
        self.mock_path.glob.return_value = [returned_path]
        res = core._search(self.mock_path, True)

        self.assertSetEqual(res, set())


class TestImageGroupingFunc(TestCase):

    def setUp(self):
        self.mock_imgs = [mock.Mock() for i in range(2)]

        self.mock_bk = mock.Mock()

    def test_return_empty_list_if_no_images(self):
        res = core.image_grouping([], 0)

        self.assertListEqual(res, [])

    def test_return_empty_list_if_one_image(self):
        res = core.image_grouping(['image'], 0)

        self.assertListEqual(res, [])

    def test_BKTree_called_with_hamming_dist_and_images_args(self):
        with mock.patch('pybktree.BKTree') as mock_tree:
            core.image_grouping(self.mock_imgs, 0)

        mock_tree.assert_called_once_with(core.hamming, self.mock_imgs)

    def test_BKTree_raise_TypeError(self):
        with mock.patch('pybktree.BKTree', side_effect=TypeError):
            with self.assertRaises(TypeError):
                core.image_grouping(self.mock_imgs, 0)

    def test_find_called_with_image_and_sensitivity_args(self):
        self.mock_bk.find.return_value = ['image']
        sens = 0
        with mock.patch('pybktree.BKTree', return_value=self.mock_bk):
            core.image_grouping(self.mock_imgs, sens)

        calls = [mock.call(self.mock_imgs[0], sens),
                 mock.call(self.mock_imgs[1], sens)]
        self.mock_bk.find.assert_has_calls(calls)

    @mock.patch(CORE+'_new_group')
    def test_loop_continue_if_there_is_one_closest_image(self, mock_group):
        self.mock_bk.find.return_value = ['image']
        with mock.patch('pybktree.BKTree', return_value=self.mock_bk):
            core.image_grouping(self.mock_imgs, 0)

        mock_group.assert_not_called()

    @mock.patch(CORE+'_new_group')
    def test_new_group_called_with_closests_and_checked_args(self, mock_group):
        closests = ['img1', 'img2']
        self.mock_bk.find.return_value = closests
        with mock.patch('pybktree.BKTree', return_value=self.mock_bk):
            core.image_grouping(self.mock_imgs, 0)

        mock_group.assert_called_with(closests, set())

    @mock.patch(CORE+'_new_group', return_value='image')
    def test_new_group_func_return_added_to_new_group(self, mock_group):
        self.mock_bk.find.return_value = ['img1', 'img2']
        with mock.patch('pybktree.BKTree', return_value=self.mock_bk):
            res = core.image_grouping(self.mock_imgs, 0)

        # Since we have to do at least 2 iterations (or '_new_group'
        # will not be called at all), we'll have 2 'image' in the list
        self.assertListEqual(res, ['image', 'image'])

    def test_loop_continue_if_image_was_checked(self):
        closests = [(0, self.mock_imgs[0]), (0, self.mock_imgs[1])]
        self.mock_bk.find.return_value = closests
        with mock.patch('pybktree.BKTree', return_value=self.mock_bk):
            core.image_grouping(self.mock_imgs, 0)

        self.mock_bk.find.assert_called_once()


class TestNewGroupFunc(TestCase):

    def setUp(self):
        self.img = mock.Mock()
        self.img.difference = None

    def test_image_not_added_to_group_if_already_was_checked(self):
        res = core._new_group([(0, self.img)], {self.img})

        self.assertListEqual(res, [])

    def test_distance_assigned_to_difference_attribute(self):
        dist = 0
        core._new_group([(dist, self.img)], set())

        self.assertEqual(self.img.difference, dist)

    def test_image_added_to_group(self):
        res = core._new_group([(0, self.img)], set())

        self.assertListEqual(res, [self.img])

    def test_image_added_to_checked(self):
        checked = set()
        core._new_group([(0, self.img)], checked)

        self.assertSetEqual(checked, {self.img})


class TestLoadCacheFunc(TestCase):

    @mock.patch('pickle.load')
    def test_load_from_cache_p(self, mock_load):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            core.load_cache()

        mock_open.assert_called_once_with('cache.p', 'rb')

    @mock.patch('pickle.load', return_value='hashes')
    def test_return_loaded_hashes(self, mock_load):
        with mock.patch('builtins.open', mock.mock_open()):
            res = core.load_cache()

        self.assertEqual(res, 'hashes')

    @mock.patch('builtins.open', side_effect=FileNotFoundError)
    def test_return_empty_dict_if_FileNotFoundError(self, mock_open):
        res = core.load_cache()

        self.assertDictEqual(res, {})

    @mock.patch('builtins.open', side_effect=EOFError)
    def test_raise_EOFError_if_EOFError(self, mock_open):
        with self.assertRaises(EOFError):
            core.load_cache()


class TestCheckCacheFunc(TestCase):

    def setUp(self):
        self.paths = ['path1', 'path2']
        self.cache = {'path2': 'hash'}

    def test_return_empty_lists_if_pass_empty_paths(self):
        paths, cache = [], {}
        cached, not_cached = core.check_cache(paths, cache)

        self.assertListEqual(cached, [])
        self.assertListEqual(not_cached, [])

    def test_return_empty_cached_list_if_pass_empty_cache(self):
        cache = {}
        cached, _ = core.check_cache(self.paths, cache)

        self.assertListEqual(cached, [])

    def test_return_correct_cached_list(self):
        cached, _ = core.check_cache(self.paths, self.cache)

        self.assertEqual(len(cached), 1)
        self.assertEqual(cached[0].path, 'path2')
        self.assertEqual(cached[0].hash, 'hash')

    def test_return_correct_not_cached_list(self):
        _, not_cached = core.check_cache(self.paths, self.cache)

        self.assertEqual(len(not_cached), 1)
        self.assertEqual(not_cached[0].path, 'path1')
        self.assertEqual(not_cached[0].hash, None)


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

    @mock.patch(CORE + 'pickle.dump')
    @mock.patch(CORE + 'open')
    def test_caching(self, mock_open, mock_cache):
        '''!!! BE AWARE WHEN CHANGE THIS TEST. IF THERE'S
        ALREADY POPULATED CACHE FILE AND YOU DON'T PATCH
        OPEN(), YOU'LL REWRITE THE FILE
        '''

        images = [core.Image(path, dhash=666) for path in self.cached]
        new_cache = {}
        expected = {path: 666 for path in self.cached}
        core.caching(images, new_cache)

        self.assertDictEqual(expected, new_cache)
        self.assertTrue(mock_cache.called)

    @mock.patch(CORE + 'pickle.dump')
    @mock.patch(CORE + 'open')
    def test_caching_with_None_hash(self, mock_open, mock_cache):
        '''!!! BE AWARE WHEN CHANGE THIS TEST. IF THERE'S
        ALREADY POPULATED CACHE FILE AND YOU DON'T PATCH
        OPEN(), YOU'LL REWRITE THE FILE
        '''

        images = [core.Image(path, dhash=None) for path in self.cached]
        new_cache = {}
        core.caching(images, new_cache)

        self.assertDictEqual({}, new_cache)
        self.assertTrue(mock_cache.called)



class TestImageClass(TestCase):

    def setUp(self):
        self.image = core.Image('image.png', dhash='not_None_hash')

    # Image.dhash

    @mock.patch(CORE + 'PILImage.open', side_effect=OSError)
    def test_dhash_assign_None_to_hash_attr_if_OSError(self, mock_open):
        self.image.dhash()

        self.assertIsNone(self.image.hash)

    @mock.patch(CORE + 'dhash.dhash_int', return_value='hash')
    @mock.patch(CORE + 'PILImage.open')
    def test_undecorated_dhash_return_dhash(self, mock_open, mock_dhash):
        result = self.image.dhash.__wrapped__(self.image) # pylint: disable=no-member

        self.assertEqual(self.image.hash, 'hash')
        self.assertEqual(result, self.image.hash)

    def test_decorated_dhash_return_Image_object(self):
        result = self.image.dhash()

        self.assertIsInstance(result, core.Image)

    # Image.dimensions

    @mock.patch(CORE + 'PILImage.open', side_effect=OSError)
    def test_dimensions_raise_OSError(self, mock_open):
        with self.assertRaises(OSError):
            self.image.dimensions()

    @mock.patch(CORE + 'PILImage.open')
    def test_dimensions_return_correct_values(self, mock_open):
        img = core.PILImage.Image()
        img._size = (13, 666)
        mock_open.return_value = img

        size = self.image.dimensions()

        self.assertEqual(size[0], 13)
        self.assertEqual(size[1], 666)

    @mock.patch(CORE + 'PILImage.open')
    def test_dimensions_return_saved_values(self, mock_open):
        self.image.width, self.image.height = 13, 666

        size = self.image.dimensions()

        self.assertEqual(size[0], 13)
        self.assertEqual(size[1], 666)
        self.assertFalse(mock_open.called)

    # Image.filesize

    def test_filesize_return_saved_value(self):
        self.image.size = 444
        filesize = self.image.filesize(size_format=0)

        self.assertEqual(filesize, self.image.size)

    @mock.patch(CORE + 'os.path.getsize', side_effect=OSError)
    def test_filesize_raise_OSError(self, mock_size):
        with self.assertRaises(OSError):
            self.image.filesize()

    @mock.patch(CORE + 'os.path.getsize')
    def test_filesize_raise_ValueError_if_pass_wrong_format(self, mock_size):
        with self.assertRaises(ValueError):
            self.image.filesize(size_format=13)

    @mock.patch(CORE + 'os.path.getsize', return_value=1024)
    def test_filesize_return_if_Bytes_format(self, mock_size):
        filesize = self.image.filesize(size_format=0)

        self.assertEqual(filesize, 1024)

    @mock.patch(CORE + 'os.path.getsize', return_value=1024)
    def test_filesize_return_if_KiloBytes_format(self, mock_size):
        filesize = self.image.filesize(size_format=1)

        self.assertAlmostEqual(filesize, 1)

    @mock.patch(CORE + 'os.path.getsize', return_value=1048576)
    def test_filesize_return_if_MegaBytes_format(self, mock_size):
        filesize = self.image.filesize(size_format=2)

        self.assertAlmostEqual(filesize, 1)

    # Image.delete

    @mock.patch(CORE + 'os.remove', side_effect=OSError)
    def test_delete_raise_OSError(self, mock_remove):
        with self.assertRaises(OSError):
            self.image.delete()

    @mock.patch(CORE + 'os.remove')
    def test_delete_called(self, mock_remove):
        self.image.delete()

        self.assertTrue(mock_remove.called)

    # Image.move

    @mock.patch(CORE + 'os.rename', side_effect=OSError)
    def test_move_raise_OSError(self, mock_rename):
        with self.assertRaises(OSError):
            self.image.move('new_dst')

    @mock.patch(CORE + 'os.rename')
    def test_move_called(self, mock_rename):
        dst = 'new_dst'
        self.image.move(dst)
        new_path = str(pathlib.Path(dst) / pathlib.Path(self.image.path))

        mock_rename.assert_called_once_with(self.image.path, new_path)

    # Image.rename

    @mock.patch('pathlib.Path.rename')
    def test_rename(self, mock_rename):
        new_name = 'new_name'
        self.image.rename(new_name)

        self.assertTrue(mock_rename.called)
        self.assertEqual(new_name, self.image.path)

    @mock.patch('pathlib.Path.rename', side_effect=FileExistsError)
    def test_rename_raise_FileExistsError(self, mock_rename):
        new_name = 'new_name'
        with self.assertRaises(FileExistsError):
            self.image.rename(new_name)

    # Image.del_parent_dir

    @mock.patch('pathlib.Path.rmdir')
    @mock.patch('pathlib.Path.glob', return_value=[])
    def test_del_parent_dir_true(self, mock_glob, mock_rm):
        self.image.del_parent_dir()

        self.assertTrue(mock_rm.called)

    @mock.patch('pathlib.Path.rmdir')
    @mock.patch('pathlib.Path.glob', return_value=['test_path'])
    def test_del_parent_dir_false(self, mock_glob, mock_rm):
        self.image.del_parent_dir()

        self.assertFalse(mock_rm.called)


class TestSort(TestCase):

    def test_similarity_sort(self):
        img1 = core.Image('test', difference=5)
        img2 = core.Image('test', difference=0)
        img3 = core.Image('test', difference=3)
        img_groups = [[img1, img2, img3]]

        s = core.Sort(img_groups)
        s.sort(0)

        self.assertListEqual(img_groups[0], [img2, img3, img1])

    def test_size_sort(self):
        '''Image.filesize returns values in KB by default.
        So do not use small numbers or you might get incorrect
        sort results
        '''

        img1 = core.Image('test')
        img1.size = 3072
        img2 = core.Image('test')
        img2.size = 1024
        img3 = core.Image('test')
        img3.size = 2048
        img_groups = [[img1, img2, img3]]

        s = core.Sort(img_groups)
        s.sort(1)

        self.assertListEqual(img_groups[0], [img1, img3, img2])

    def test_dimensions_sort(self):
        img1 = core.Image('test')
        img1.width = 4
        img1.height = 6
        img2 = core.Image('test')
        img2.width = 1
        img2.height = 1
        img3 = core.Image('test')
        img3.width = 5
        img3.height = 3
        img_groups = [[img1, img2, img3]]

        s = core.Sort(img_groups)
        s.sort(2)

        self.assertListEqual(img_groups[0], [img1, img3, img2])

    def test_path_sort(self):
        img1 = core.Image('test3')
        img2 = core.Image('test1')
        img3 = core.Image('test2')
        img_groups = [[img1, img2, img3]]

        s = core.Sort(img_groups)
        s.sort(3)

        self.assertListEqual(img_groups[0], [img2, img3, img1])
