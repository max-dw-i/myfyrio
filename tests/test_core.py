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
'''

from unittest import TestCase, mock

from PyQt5 import QtCore, QtGui

from doppelganger import core

CORE = 'doppelganger.core.'


# pylint: disable=unused-argument,missing-class-docstring


class TestFuncFindImage(TestCase):

    def setUp(self):
        self.mock_path = mock.Mock()

    def test_return_nothing_if_pass_empty_folders_list(self):
        paths = list(core.find_image([]))

        self.assertListEqual(paths, [])

    def test_raise_FileNotFoundError(self):
        self.mock_path.exists.return_value = False
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            with self.assertRaises(FileNotFoundError):
                res = list(core.find_image(['folder'])) #pylint: disable=unused-variable

    def test_glob_pattern_if_recursive_search(self):
        self.mock_path.exists.return_value = True
        self.mock_path.glob.return_value = []
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], # pylint: disable=unused-variable
                                       recursive=True))

        self.mock_path.glob.assert_called_once_with('**/*')

    def test_glob_pattern_if_nonrecursive_search(self):
        self.mock_path.exists.return_value = True
        self.mock_path.glob.return_value = []
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], # pylint: disable=unused-variable
                                       recursive=False))

        self.mock_path.glob.assert_called_once_with('*')

    def test_return_nothing_if_path_isnt_file(self):
        self.mock_path.exists.return_value = True
        image_path = mock.Mock()
        image_path.is_file.return_value = False
        self.mock_path.glob.return_value = [image_path]
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], recursive=False))

        self.assertListEqual(res, [])

    def test_return_nothing_if_path_is_file_but_wrong_suffix(self):
        self.mock_path.exists.return_value = True
        image_path = mock.Mock()
        image_path.is_file.return_value = True
        image_path.suffix = '.www'
        self.mock_path.glob.return_value = [image_path]
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], recursive=False))

        self.assertListEqual(res, [])

    def test_return_proper_Image_obj(self):
        img_path = 'img_path'
        self.mock_path.exists.return_value = True
        image_path = mock.MagicMock()
        image_path.is_file.return_value = True
        image_path.suffix = '.png'
        image_path.__str__.return_value = img_path
        self.mock_path.glob.return_value = [image_path]
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], recursive=False))

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].path, 'img_path')


class TestFuncImageGrouping(TestCase):

    def setUp(self):
        self.image1 = mock.Mock()
        self.image1.hash = 0
        self.image2 = mock.Mock
        self.image2.hash = 1
        self.images = [self.image1, self.image2]
        self.tree = 'bktree'

    def test_return_empty_list_if_no_images(self):
        res = list(core.image_grouping([], 0))

        self.assertListEqual(res[-1], [])

    def test_return_empty_list_if_one_image(self):
        with mock.patch('pybktree.BKTree'):
            with mock.patch(CORE+'_closest', return_value=(None, None)):
                res = list(core.image_grouping(['image'], 0))

        self.assertListEqual(res[-1], [])

    def test_BKTree_called_with_hamming_dist_and_images_args(self):
        with mock.patch('pybktree.BKTree') as mock_tree:
            with mock.patch(CORE+'_closest', return_value=(None, None)):
                list(core.image_grouping(self.images, 0))

        mock_tree.assert_called_once_with(core.Image.hamming, self.images)

    def test_BKTree_raise_TypeError(self):
        with mock.patch('pybktree.BKTree', side_effect=TypeError):
            with self.assertRaises(TypeError):
                list(core.image_grouping(self.images, 0))

    def test_find_called_with_image_and_sensitivity_args(self):
        sens = 0
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest',
                            return_value=(None, None)) as mock_closest_call:
                list(core.image_grouping(self.images, sens))

        calls = [mock.call(self.tree, self.image1, sens),
                 mock.call(self.tree, self.image2, sens)]
        mock_closest_call.assert_has_calls(calls)

    @mock.patch(CORE+'_add_new_group')
    def test_loop_continue_if_there_is_no_closest_image(self, mock_group):
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest', return_value=(None, None)):
                list(core.image_grouping(self.images, 0))

        mock_group.assert_not_called()

    def test_return_if_image_and_closest_not_in_checked(self):
        closest1 = (17, mock.Mock())
        closest2 = (19, mock.Mock())
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest', side_effect=[closest1, closest2]):
                res = list(core.image_grouping(self.images, 0))

        self.assertListEqual(res[-1], [[self.image1, closest1[1]],
                                       [self.image2, closest2[1]]])

    def test_return_if_image_in_checked_and_closest_not_in_checked(self):
        closest1 = (17, self.image2)
        closest2 = (19, mock.Mock())
        closest2[1].hash = 2
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest', side_effect=[closest1, closest2]):
                res = list(core.image_grouping(self.images, 0))

        self.assertListEqual(res[-1], [[self.image1, self.image2,
                                        closest2[1]]])

    def test_return_if_image_not_in_checked_and_closest_in_checked(self):
        closest1 = (17, mock.Mock())
        closest2 = (19, self.image1)
        closest1[1].hash = 2
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest', side_effect=[closest1, closest2]):
                res = list(core.image_grouping(self.images, 0))

        self.assertListEqual(res[-1], [[self.image1, closest1[1],
                                        self.image2]])


class TestFuncClosest(TestCase):

    def setUp(self):
        self.mock_tree = mock.Mock()
        self.mock_image = mock.Mock()
        self.mock_tree.find.return_value = [(0, self.mock_image)]
        self.sensitivity = 0

    def test_pybktree_find_called_with_image_and_sensitivity_args(self):
        core._closest(self.mock_tree, self.mock_image, self.sensitivity)

        self.mock_tree.find.assert_called_once_with(self.mock_image,
                                                    self.sensitivity)

    def test_return_None_if_result_is_image_itself(self):
        res = core._closest(self.mock_tree, self.mock_image, self.sensitivity)

        self.assertTupleEqual(res, (None, None))

    def test_return_if_image_itself_is_first(self):
        close_img = mock.Mock()
        self.mock_tree.find.return_value = [(0, self.mock_image),
                                            (0, close_img)]
        res = core._closest(self.mock_tree, self.mock_image, self.sensitivity)

        self.assertTupleEqual(res, (0, close_img))

    def test_return_if_image_itself_is_second(self):
        close_img = mock.Mock()
        self.mock_tree.find.return_value = [(0, close_img),
                                            (0, self.mock_image)]
        res = core._closest(self.mock_tree, self.mock_image, self.sensitivity)

        self.assertTupleEqual(res, (0, close_img))


class TestFuncAddImgToExistingGroup(TestCase):

    def setUp(self):
        self.mock_image = mock.Mock()
        self.mock_image.hash = 235
        self.checked = {self.mock_image: 0}
        self.image_groups = [[self.mock_image]]

        self.mock_img_not_in = mock.Mock()
        self.mock_img_not_in.hash = 487

    def test_image_added_to_proper_group(self):
        core._add_img_to_existing_group(self.mock_image, self.mock_img_not_in,
                                        self.checked, self.image_groups)

        self.assertListEqual(self.image_groups, [[self.mock_image,
                                                  self.mock_img_not_in]])

    def test_assign_distance_to_image_difference_attr(self):
        dist = 999
        self.mock_image.hamming.return_value = dist
        core._add_img_to_existing_group(self.mock_image, self.mock_img_not_in,
                                        self.checked, self.image_groups)

        self.assertEqual(self.mock_img_not_in.difference, dist)

    def test_checked_dict_changed_properly(self):
        core._add_img_to_existing_group(self.mock_image, self.mock_img_not_in,
                                        self.checked, self.image_groups)

        self.assertDictEqual(self.checked, {self.mock_image: 0,
                                            self.mock_img_not_in: 0})


class TestFuncAddNewGroup(TestCase):

    def setUp(self):
        self.mock_main_image = mock.Mock()
        self.mock_closest_img = mock.Mock()
        self.checked = {}
        self.image_groups = []
        self.distance = 888

    def test_images_added_to_proper_group(self):
        core._add_new_group(self.mock_main_image, self.mock_closest_img,
                            self.checked, self.image_groups, self.distance)

        self.assertListEqual(self.image_groups, [[self.mock_main_image,
                                                  self.mock_closest_img]])

    def test_assign_distance_to_image_difference_attr(self):
        core._add_new_group(self.mock_main_image, self.mock_closest_img,
                            self.checked, self.image_groups, self.distance)

        self.assertEqual(self.mock_closest_img.difference, self.distance)

    def test_checked_dict_changed_properly(self):
        core._add_new_group(self.mock_main_image, self.mock_closest_img,
                            self.checked, self.image_groups, self.distance)

        self.assertDictEqual(self.checked, {self.mock_main_image: 0,
                                            self.mock_closest_img: 0})


class TestClassImage(TestCase):

    def setUp(self):
        self.image = core.Image('image.png')


class TestMethodCalculateDhash(TestClassImage):

    def setUp(self):
        super().setUp()

        self.mock_Qimage = mock.Mock()

    def test_Image_scaled_called_with_size_9(self):
        with mock.patch(CORE+'Image.scaled') as mock_scaled:
            with mock.patch(CORE+'Image._form_hash'):
                self.image.calculate_dhash()

        mock_scaled.assert_called_once_with(9, 9)

    def test_scaled_img_converted_to_greyscale(self):
        with mock.patch(CORE+'Image.scaled', return_value=self.mock_Qimage):
            with mock.patch(CORE+'Image._form_hash'):
                self.image.calculate_dhash()

        self.mock_Qimage.convertToFormat.assert_called_once_with(
            QtGui.QImage.Format_Grayscale8
        )

    def test_form_hash_called_with_grey_img_and_size_8(self):
        self.mock_Qimage.convertToFormat.return_value = 'grey_img'
        with mock.patch(CORE+'Image.scaled', return_value=self.mock_Qimage):
            with mock.patch(CORE+'Image._form_hash') as mock_hash:
                self.image.calculate_dhash()

        mock_hash.assert_called_once_with('grey_img', 8)

    def test_form_hash_result_assigned_to_attr_dhash(self):
        with mock.patch(CORE+'Image.scaled', return_value=self.mock_Qimage):
            with mock.patch(CORE+'Image._form_hash', return_value='hash'):
                self.image.calculate_dhash()

        self.assertEqual(self.image.dhash, 'hash')

    def test_return_attr_dhash(self):
        with mock.patch(CORE+'Image.scaled', return_value=self.mock_Qimage):
            with mock.patch(CORE+'Image._form_hash', return_value='hash'):
                res = self.image.calculate_dhash()

        self.assertEqual(res, self.image.dhash)

    def test_assign_minus_1_to_attr_dhash_if_Image_scaled_raise_OSError(self):
        with mock.patch(CORE+'Image.scaled', side_effect=OSError):
            self.image.calculate_dhash()

        self.assertEqual(self.image.dhash, -1)

    def test_return_attr_dhash_if_Image_scaled_raise_OSError(self):
        with mock.patch(CORE+'Image.scaled', side_effect=OSError):
            res = self.image.calculate_dhash()

        self.assertEqual(res, self.image.dhash)


class TestMethodSimilarity(TestClassImage):

    def test_similarity_rate_100(self):
        self.image.difference = 0
        res = self.image.similarity()

        self.assertEqual(res, 100)

    def test_similarity_rate_0(self):
        self.image.difference = 128
        res = self.image.similarity()

        self.assertEqual(res, 0)

    def test_similarity_rate(self):
        self.image.difference = 64
        res = self.image.similarity()

        self.assertEqual(res, 50)


class TestFuncThumbnailFunc(TestClassImage):

    def setUp(self):
        super().setUp()

        self.image._suffix = 'png'
        self.size = 222

        self.w, self.h = 111, 111
        self.DIM = CORE + 'Image.scaling_dimensions'
        self.IMG = CORE + 'Image.scaled'
        self.BA = CORE + 'Image._QImage_to_QByteArray'

    def test_scaling_dimensions_called_with_size_arg(self):
        with mock.patch(self.DIM, return_value=(self.w, self.h)) as mock_dim:
            with mock.patch(self.IMG):
                with mock.patch(self.BA):
                    self.image.thumbnail(self.size)

        mock_dim.assert_called_once_with(self.size)

    def test_args_scaled_image_called_with(self):
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG) as mock_scaled_img:
                with mock.patch(self.BA):
                    self.image.thumbnail(self.size)

        mock_scaled_img.assert_called_once_with(self.w, self.h)

    def test_args_QImage_to_QByteArray_called_with(self):
        qimage = 'image'
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG, return_value=qimage):
                with mock.patch(self.BA) as mock_ba:
                    self.image.thumbnail(self.size)

        mock_ba.assert_called_once_with(qimage, 'PNG')

    def test_QImage_to_QByteArray_result_assigned_to_attr_thumb(self):
        ba_image = 'QByteArray_image'
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG):
                with mock.patch(self.BA, return_value=ba_image):
                    self.image.thumbnail(self.size)

        self.assertEqual(self.image.thumb, ba_image)

    def test_return_QImage_to_QByteArray_result(self):
        ba_image = 'QByteArray_image'
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG):
                with mock.patch(self.BA, return_value=ba_image):
                    res = self.image.thumbnail(self.size)

        self.assertEqual(res, ba_image)


class TestMethodScalingDimensions(TestClassImage):

    def test_return_if_pass_square_image(self):
        self.image._width = 5
        self.image._height = 5
        new_size = self.image.scaling_dimensions(10)

        self.assertEqual(new_size[0], 10)
        self.assertEqual(new_size[1], 10)

    def test_return_if_pass_portrait_image(self):
        self.image._width = 1
        self.image._height = 5
        new_size = self.image.scaling_dimensions(10)

        self.assertEqual(new_size[0], 2)
        self.assertEqual(new_size[1], 10)

    def test_return_if_pass_landscape_image(self):
        self.image._width = 5
        self.image._height = 1
        new_size = self.image.scaling_dimensions(10)

        self.assertEqual(new_size[0], 10)
        self.assertEqual(new_size[1], 2)


class TestMethodScaled(TestClassImage):

    def setUp(self):
        super().setUp()

        self.width = 1
        self.height = 2

        self.QIR = 'PyQt5.QtGui.QImageReader'
        self.reader = mock.Mock()
        self.reader.canRead.return_value = True
        self.qimage = mock.Mock()
        self.qimage.isNull.return_value = False
        self.reader.read.return_value = self.qimage

    def test_QImageReader_called_with_path_arg(self):
        with mock.patch(self.QIR, return_value=self.reader) as mock_QIR:
            self.image.scaled(self.width, self.height)

        mock_QIR.assert_called_once_with(self.image.path)

    def test_scaling_size_set(self):
        with mock.patch(self.QIR, return_value=self.reader):
            self.image.scaled(self.width, self.height)

        self.reader.setScaledSize.assert_called_once()

    def test_raise_OSError_if_canRead_False(self):
        self.reader.canRead.return_value = False
        with mock.patch(self.QIR, return_value=self.reader):
            with self.assertRaises(OSError):
                self.image.scaled(self.width, self.height)

    def test_return_image_if_isNull_False(self):
        with mock.patch(self.QIR, return_value=self.reader):
            res = self.image.scaled(self.width, self.height)

        self.assertEqual(res, self.qimage)

    def test_raise_OSError_if_isNull_True(self):
        self.qimage.isNull.return_value = True
        with mock.patch(self.QIR, return_value=self.reader):
            with self.assertRaises(OSError):
                self.image.scaled(self.width, self.height)


class TestMethodQImageToQByteArrayFunc(TestClassImage):

    def setUp(self):
        self.img = mock.Mock()
        self.ba = mock.Mock()
        self.buf = mock.Mock()
        self.buf.open.return_value = True
        self.img.save.return_value = True

        self.BUF = 'PyQt5.QtCore.QBuffer'
        self.BA = 'PyQt5.QtCore.QByteArray'

    def test_QBuffer_called_with_QByteArray_arg(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf) as mock_buf:
                core.Image._QImage_to_QByteArray(self.img, 'PNG')

        mock_buf.assert_called_once_with(self.ba)

    def test_QBuffer_open_called_with_WriteOnly(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                core.Image._QImage_to_QByteArray(self.img, 'PNG')

        self.buf.open.assert_called_once_with(QtCore.QIODevice.WriteOnly)

    def test_raise_ThumbnailError_if_QByteArray_open_return_False(self):
        self.buf.open.return_value = False
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                with self.assertRaises(OSError):
                    core.Image._QImage_to_QByteArray(self.img, 'PNG')

    def test_args_QImage_save_called_with(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                core.Image._QImage_to_QByteArray(self.img, 'PNG')

        self.img.save.assert_called_once_with(self.buf, 'PNG', 100)

    def test_raise_ThumbnailError_if_QImage_save_return_False(self):
        self.img.save.return_value = False
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                with self.assertRaises(OSError):
                    core.Image._QImage_to_QByteArray(self.img, 'PNG')

    def test_QBuffer_closed(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                core.Image._QImage_to_QByteArray(self.img, 'PNG')

        self.buf.close.assert_called_once_with()

    def test_return_iamge_in_QByteArray_format(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                res = core.Image._QImage_to_QByteArray(self.img, 'PNG')

        self.assertEqual(res, self.ba)


class TestMethodSetDimensions(TestClassImage):

    def test_QImageReader_called_with_path_arg(self):
        with mock.patch('PyQt5.QtGui.QImageReader') as mock_qimg_reader:
            self.image._set_dimensions()

        mock_qimg_reader.assert_called_once_with(self.image.path)

    def test_width_and_height_assigned_to_proper_attrs(self):
        width = 333
        height = 444
        mock_qimg = mock.Mock()
        mock_qsize = mock.Mock()
        mock_qimg.size.return_value = mock_qsize
        mock_qsize.width.return_value = width
        mock_qsize.height.return_value = height

        with mock.patch('PyQt5.QtGui.QImageReader', return_value=mock_qimg):
            self.image._set_dimensions()

        self.assertEqual(self.image._width, width)
        self.assertEqual(self.image._height, height)


class TestPropertyWidth(TestClassImage):

    def test_dimensions_called_if_width_is_None(self):
        self.image._width = None
        with mock.patch(CORE + 'Image._set_dimensions') as mock_dim:
            self.image.width # pylint: disable=pointless-statement

        mock_dim.assert_called_once_with()

    def test_return_width_attr(self):
        w = 34
        self.image._width = w
        res = self.image.width

        self.assertEqual(res, w)


class TestPropertyHeight(TestClassImage):

    def test_dimensions_called_if_height_is_None(self):
        self.image._height = None
        with mock.patch(CORE + 'Image._set_dimensions') as mock_dim:
            self.image.height # pylint: disable=pointless-statement

        mock_dim.assert_called_once_with()

    def test_return_height_attr(self):
        h = 34
        self.image._height = h
        res = self.image.height

        self.assertEqual(res, h)


class TestMethodSetFilesize(TestClassImage):

    @mock.patch('os.path.getsize', return_value=1024)
    def test_getsize_called_with_image_path_arg(self, mock_size):
        self.image.filesize()

        mock_size.assert_called_once_with(self.image.path)

    @mock.patch('os.path.getsize', side_effect=OSError)
    def test_raise_OSError_if_getsize_raise_OSError(self, mock_size):
        with self.assertRaises(OSError):
            self.image.filesize()

    @mock.patch('os.path.getsize', return_value=1024)
    def test_assign_result_of_getsize_to_size_attr(self, mock_size):
        self.image.filesize(core.SizeFormat.B)

        self.assertEqual(self.image.size, 1024)


class TestMethodFilesize(TestClassImage):

    def h_set_filesize(self):
        self.image.size = 1

    def test_return_image_size_attr_if_Bytes_format(self):
        self.image.size = 1024
        filesize = self.image.filesize(size_format=core.SizeFormat.B)

        self.assertAlmostEqual(filesize, self.image.size)

    def test_return_image_size_attr_if_KiloBytes_format(self):
        self.image.size = 1024
        filesize = self.image.filesize(size_format=core.SizeFormat.KB)

        self.assertAlmostEqual(filesize, 1)

    def test_return_image_size_attr_if_MegaBytes_format(self):
        self.image.size = 1024**2
        filesize = self.image.filesize(size_format=core.SizeFormat.MB)

        self.assertAlmostEqual(filesize, 1)

    def test_set_filesize_called_if_size_attr_is_None(self):
        self.image.size = None
        with mock.patch(CORE + 'Image._set_filesize',
                        side_effect=self.h_set_filesize) as mock_size_call:
            self.image.filesize(size_format=core.SizeFormat.B)

        mock_size_call.assert_called_once_with()

    def test_set_filesize_not_called_if_size_attr_is_not_None(self):
        self.image.size = 1024
        with mock.patch(CORE + 'Image._set_filesize') as mock_size_call:
            self.image.filesize(size_format=core.SizeFormat.B)

        mock_size_call.assert_not_called()


class TestPropertySuffix(TestClassImage):

    def test_args_Path_called_with_if_attr_suffix_is_None(self):
        with mock.patch(CORE+'Path') as mock_Path:
            self.image.suffix # pylint: disable=pointless-statement

        mock_Path.assert_called_once_with(self.image.path)

    def test_assign_Path_result_to_attr_suffix_if_it_is_None(self):
        dot_suffix = '.jpg'
        mock_Path = mock.Mock()
        mock_Path.suffix = dot_suffix
        with mock.patch(CORE+'Path', return_value=mock_Path):
            self.image.suffix # pylint: disable=pointless-statement

        self.assertEqual(self.image.suffix, dot_suffix[1:])

    def test_return_attr_suffix_if_it_is_not_None(self):
        self.image._suffix = 'jpg'
        with mock.patch(CORE+'Path'):
            res = self.image.suffix

        self.assertEqual(res, self.image._suffix)


class TestMethodDelete(TestClassImage):

    @mock.patch('os.remove', side_effect=OSError)
    def test_raise_OSError_if_remove_raise_OSError(self, mock_remove):
        with self.assertRaises(OSError):
            self.image.delete()

    @mock.patch('os.remove')
    def test_remove_called_with_image_path_arg(self, mock_remove):
        self.image.delete()

        mock_remove.assert_called_once_with(self.image.path)

    # func 'move'

    @mock.patch('os.rename', side_effect=OSError)
    def test_raise_OSError_if_move_raise_OSError(self, mock_move):
        with self.assertRaises(OSError):
            self.image.move('new_dst')

    @mock.patch('os.rename')
    def test_what_args_is_Path_called_with(self, mock_move):
        new_dst = 'new_dst'
        mock_path = mock.MagicMock()
        calls = [mock.call(self.image.path), mock.call(new_dst)]
        with mock.patch(CORE+'Path', return_value=mock_path) as patch:
            self.image.move(new_dst)

        patch.assert_has_calls(calls)

    @mock.patch('os.rename')
    def test_move_called_with_image_path_and_new_path_args(self, mock_move):
        dst = 'new_dst'
        new_path = dst + '/' + self.image.path
        mock_path = mock.MagicMock()
        mock_path.__truediv__.return_value = new_path
        with mock.patch(CORE+'Path', return_value=mock_path):
            self.image.move(dst)

        mock_move.assert_called_once_with(self.image.path, new_path)


class TestMethodRename(TestClassImage):

    def setUp(self):
        super().setUp()

        self.new_name = 'new_name.png'
        self.mock_path = mock.MagicMock()
        self.mock_path.parent.__truediv__.return_value = self.new_name

    def test_rename_called_with_new_name_arg(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.rename(self.new_name)

        self.mock_path.rename.assert_called_once_with(self.new_name)

    def test_new_name_assigned_to_image_path_attr(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.rename(self.new_name)

        self.assertEqual(self.image.path, self.new_name)

    def test_raise_FileExistsError_if_rename_raise_FileExistsError(self):
        self.mock_path.rename.side_effect = FileExistsError
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            with self.assertRaises(FileExistsError):
                self.image.rename(self.new_name)


class TestMethodDelParentDir(TestClassImage):

    def setUp(self):
        super().setUp()

        self.mock_path = mock.Mock()
        self.mock_path.parent.glob.return_value = []

    def test_Path_called_with_image_path_arg(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path) as patch:
            self.image.del_parent_dir()

        patch.assert_called_once_with(self.image.path)

    def test_glob_search_all_files(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.del_parent_dir()

        self.mock_path.parent.glob.assert_called_once_with('*')

    def test_rmdir_not_called_if_dir_is_not_empty(self):
        self.mock_path.parent.glob.return_value = ['file']
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.del_parent_dir()

        self.mock_path.parent.rmdir.assert_not_called()

    def test_rmdir_called_if_dir_is_empty(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.del_parent_dir()

        self.mock_path.parent.rmdir.assert_called_once_with()


class TestSort(TestCase):

    def setUp(self):
        self.img1 = core.Image('test3')
        self.img1.difference = 5
        self.img1.size = 3072
        self.img1._width = 4
        self.img1._height = 6
        self.img2 = core.Image('test1')
        self.img2.difference = 0
        self.img2.size = 1024
        self.img2._width = 1
        self.img2._height = 1
        self.img3 = core.Image('test2')
        self.img3.difference = 3
        self.img3.size = 2048
        self.img3._width = 5
        self.img3._height = 3
        self.img_group = [self.img1, self.img2, self.img3]

    def test_similarity_sort(self):
        s = core.Sort(self.img_group)
        s.sort(0)

        self.assertListEqual(self.img_group,
                             [self.img2, self.img3, self.img1])

    def test_size_sort(self):
        '''Image.filesize returns values in KB by default.
        So do not use small numbers or you might get incorrect
        sort results
        '''

        s = core.Sort(self.img_group)
        s.sort(1)

        self.assertListEqual(self.img_group,
                             [self.img1, self.img3, self.img2])

    def test_dimensions_sort(self):
        s = core.Sort(self.img_group)
        s.sort(2)

        self.assertListEqual(self.img_group,
                             [self.img1, self.img3, self.img2])

    def test_path_sort(self):
        s = core.Sort(self.img_group)
        s.sort(3)

        self.assertListEqual(self.img_group,
                             [self.img2, self.img3, self.img1])
