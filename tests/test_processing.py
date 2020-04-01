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

import logging
from unittest import TestCase, mock

from PyQt5 import QtCore, QtTest, QtWidgets

from doppelganger import exception, processing, signals

# Configure a logger for testing purposes
logger = logging.getLogger('main')
logger.setLevel(logging.WARNING)
if not logger.handlers:
    nh = logging.NullHandler()
    logger.addHandler(nh)

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=unused-argument,missing-class-docstring

CORE = 'doppelganger.core.'
PROCESSING = 'doppelganger.processing.'


class TestFuncThumbnailFunc(TestCase):

    def setUp(self):
        self.img = mock.Mock()
        self.img.path = 'path'
        self.img.suffix = '.png'
        self.size = 222

        self.w, self.h = 111, 111
        self.DIM = PROCESSING + '_scaling_dimensions'
        self.IMG = PROCESSING + '_scaled_image'
        self.BA = PROCESSING + '_QImage_to_QByteArray'

    def test_scaling_dimensions_called_with_image_and_size_args(self):
        with mock.patch(self.DIM, return_value=(self.w, self.h)) as mock_dim:
            with mock.patch(self.IMG):
                with mock.patch(self.BA):
                    processing.thumbnail(self.img, self.size)

        mock_dim.assert_called_once_with(self.img, self.size)

    def test_args_scaled_image_called_with(self):
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG) as mock_scaled_img:
                with mock.patch(self.BA):
                    processing.thumbnail(self.img, self.size)

        mock_scaled_img.assert_called_once_with(self.img.path, self.w, self.h)

    def test_args_QImage_to_QByteArray_called_with(self):
        qimage = 'image'
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG, return_value=qimage):
                with mock.patch(self.BA) as mock_ba:
                    processing.thumbnail(self.img, self.size)

        mock_ba.assert_called_once_with(qimage, 'PNG')

    def test_return_QImage_to_QByteArray_result(self):
        ba_image = 'QByteArray_image'
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG):
                with mock.patch(self.BA, return_value=ba_image):
                    res = processing.thumbnail(self.img, self.size)

        self.assertEqual(res, ba_image)

    def test_log_error_if_raise_OSError(self):
        with mock.patch(self.DIM, side_effect=OSError):
            with self.assertLogs('main.processing', 'ERROR'):
                processing.thumbnail(self.img, self.size)

    def test_log_error_if_raise_ThumbnailError(self):
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG, side_effect=exception.ThumbnailError):
                with self.assertLogs('main.processing', 'ERROR'):
                    processing.thumbnail(self.img, self.size)

    def test_return_None_if_raise_OSError(self):
        with mock.patch(self.DIM, side_effect=OSError):
            res = processing.thumbnail(self.img, self.size)

        self.assertIsNone(res)

    def test_return_None_if_raise_ThumbnailError(self):
        with mock.patch(self.DIM, return_value=(self.w, self.h)):
            with mock.patch(self.IMG, side_effect=exception.ThumbnailError):
                res = processing.thumbnail(self.img, self.size)

        self.assertIsNone(res)

class TestFuncScalingDimensionsFunc(TestCase):

    def setUp(self):
        self.mock_image = mock.Mock()

    def test_return_if_pass_square_image(self):
        self.mock_image.width = 5
        self.mock_image.height = 5
        new_size = processing._scaling_dimensions(self.mock_image, 10)

        self.assertEqual(new_size[0], 10)
        self.assertEqual(new_size[1], 10)

    def test_return_if_pass_portrait_image(self):
        self.mock_image.width = 1
        self.mock_image.height = 5
        new_size = processing._scaling_dimensions(self.mock_image, 10)

        self.assertEqual(new_size[0], 2)
        self.assertEqual(new_size[1], 10)

    def test_return_if_pass_landscape_image(self):
        self.mock_image.width = 5
        self.mock_image.height = 1
        new_size = processing._scaling_dimensions(self.mock_image, 10)

        self.assertEqual(new_size[0], 10)
        self.assertEqual(new_size[1], 2)


class TestFuncScaledImageFunc(TestCase):

    def setUp(self):
        self.path = 'path'
        self.width = 1
        self.height = 2

        self.QIR = 'PyQt5.QtGui.QImageReader'
        self.reader = mock.Mock()
        self.reader.canRead.return_value = True
        self.image = mock.Mock()
        self.image.isNull.return_value = False
        self.reader.read.return_value = self.image

    def test_QImageReader_called_with_path_arg(self):
        with mock.patch(self.QIR, return_value=self.reader) as mock_QIR:
            processing._scaled_image(self.path, self.width, self.height)

        mock_QIR.assert_called_once_with(self.path)

    def test_format_from_content(self):
        from_content = self.reader.setDecideFormatFromContent
        with mock.patch(self.QIR, return_value=self.reader):
            processing._scaled_image(self.path, self.width, self.height)

        from_content.assert_called_once_with(True)

    def test_scaling_size_set(self):
        with mock.patch(self.QIR, return_value=self.reader):
            processing._scaled_image(self.path, self.width, self.height)

        self.reader.setScaledSize.assert_called_once()

    def test_raise_ThumbnailError_if_canRead_False(self):
        self.reader.canRead.return_value = False
        with mock.patch(self.QIR, return_value=self.reader):
            with self.assertRaises(exception.ThumbnailError):
                processing._scaled_image(self.path, self.width, self.height)

    def test_return_image_if_isNull_False(self):
        with mock.patch(self.QIR, return_value=self.reader):
            res = processing._scaled_image(self.path, self.width, self.height)

        self.assertEqual(res, self.image)

    def test_raise_ThumbnailError_if_isNull_True(self):
        self.image.isNull.return_value = True
        with mock.patch(self.QIR, return_value=self.reader):
            with self.assertRaises(exception.ThumbnailError):
                processing._scaled_image(self.path, self.width, self.height)


class TestFuncQImageToQByteArrayFunc(TestCase):

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
                processing._QImage_to_QByteArray(self.img, 'PNG')

        mock_buf.assert_called_once_with(self.ba)

    def test_QBuffer_open_called_with_WriteOnly(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                processing._QImage_to_QByteArray(self.img, 'PNG')

        self.buf.open.assert_called_once_with(QtCore.QIODevice.WriteOnly)

    def test_raise_ThumbnailError_if_QByteArray_open_return_False(self):
        self.buf.open.return_value = False
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                with self.assertRaises(exception.ThumbnailError):
                    processing._QImage_to_QByteArray(self.img, 'PNG')

    def test_args_QImage_save_called_with(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                processing._QImage_to_QByteArray(self.img, 'PNG')

        self.img.save.assert_called_once_with(self.buf, 'PNG', 100)

    def test_raise_ThumbnailError_if_QImage_save_return_False(self):
        self.img.save.return_value = False
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                with self.assertRaises(exception.ThumbnailError):
                    processing._QImage_to_QByteArray(self.img, 'PNG')

    def test_QBuffer_closed(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                processing._QImage_to_QByteArray(self.img, 'PNG')

        self.buf.close.assert_called_once_with()

    def test_return_iamge_in_QByteArray_format(self):
        with mock.patch(self.BA, return_value=self.ba):
            with mock.patch(self.BUF, return_value=self.buf):
                res = processing._QImage_to_QByteArray(self.img, 'PNG')

        self.assertEqual(res, self.ba)


class TestFuncSimilarityRate(TestCase):

    def setUp(self):
        self.img_group = [[mock.Mock()]]
        self.img = self.img_group[0][0]

    def test_similarity_rate_100(self):
        self.img.difference = 0
        processing.similarity_rate(self.img_group)

        self.assertEqual(self.img.difference, 100)

    def test_similarity_rate_0(self):
        self.img.difference = 128
        processing.similarity_rate(self.img_group)

        self.assertEqual(self.img.difference, 0)

    def test_similarity_rate(self):
        self.img.difference = 64
        processing.similarity_rate(self.img_group)

        self.assertEqual(self.img.difference, 50)


class TestClassImageProcessing(TestCase):

    def setUp(self):
        self.mw_signals = signals.Signals()
        self.folders = []
        self.sensitivity = 0
        self.CONF = {'sort': 0,
                     'subfolders': True,
                     'size': 200}
        self.proc = processing.ImageProcessing(self.mw_signals, self.folders,
                                               self.sensitivity, self.CONF)


class TestMethodInit(TestClassImageProcessing):

    def test_attrs_initial_values(self):
        self.assertListEqual(self.proc.folders, [])
        self.assertEqual(self.proc.sensitivity, 0)
        self.assertFalse(self.proc.interrupt)
        self.assertFalse(self.proc.errors)
        self.assertEqual(self.proc.progress_bar_value, 0.0)
        self.assertEqual(self.CONF, self.proc.conf)


class TestMethodFindImages(TestClassImageProcessing):

    @mock.patch(CORE+'find_image')
    def test_args_core_find_images_called_with(self, mock_find):
        self.proc._find_images()

        mock_find.assert_called_once_with(self.folders,
                                          self.CONF['subfolders'])

    @mock.patch(CORE+'find_image', return_value=(path for path in ['path']))
    def test_return_core_find_images_result(self, mock_paths):
        res = self.proc._find_images()

        self.assertSetEqual(res, {'path'})

    @mock.patch(CORE+'find_image', return_value=(path for path in ['path']))
    def test_raise_InterruptProcessing_if_attr_interrupt_True(self, mock_find):
        self.proc.interrupt = True
        with self.assertRaises(exception.InterruptProcessing):
            self.proc._find_images()

    @mock.patch(CORE+'find_image', return_value=(path for path in ['path']))
    def test_emits_update_info_signal_with_loaded_images_arg(self, mock_find):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 'loaded_images')
        self.assertEqual(spy[0][1], '1')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    @mock.patch(CORE+'find_image')
    def test_update_progress_bar_called_with_5(self, mock_find, mock_bar):
        self.proc._find_images()

        mock_bar.assert_called_once_with(5)


class TestMethodLoadCache(TestClassImageProcessing):

    @mock.patch(CORE+'load_cache', return_value={'path': 'hash'})
    def test_return_core_load_cache_result(self, mock_cache):
        res = self.proc._load_cache()

        self.assertEqual(res, {'path': 'hash'})

    @mock.patch(CORE+'load_cache', side_effect=EOFError)
    def test_return_empty_dict_if_core_load_cache_EOFErrores(self, mock_cache):
        res = self.proc._load_cache()

        self.assertDictEqual(res, {})

    @mock.patch(CORE+'load_cache', side_effect=OSError)
    def test_raise_OSError_if_core_load_cache_EOFErrores(self, mock_cache):
        with self.assertRaises(OSError):
            self.proc._load_cache()

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    @mock.patch(CORE+'load_cache')
    def test_update_progress_bar_called_with_10(self, mock_find, mock_bar):
        self.proc._load_cache()

        mock_bar.assert_called_once_with(10)


class TestMethodCheckCache(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.paths = ['path']
        self.cache = {'path': 'hash'}

    @mock.patch(CORE+'check_cache')
    def test_core_check_cache_called_with_paths_and_cache_args(self, mock_ch):
        self.proc._check_cache(self.paths, self.cache)

        mock_ch.assert_called_once_with(self.paths, self.cache)

    @mock.patch(CORE+'check_cache', return_value=['not_cached'])
    def test_return_core_check_cache_result(self, mock_ch):
        res = self.proc._check_cache(self.paths, self.cache)

        self.assertEqual(res, ['not_cached'])

    @mock.patch(CORE+'check_cache', return_value=['not_cached'])
    def test_emits_update_info_signal_with_found_in_cache_arg(self, mock_ch):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        self.proc._check_cache(self.paths, self.cache)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 'found_in_cache')
        self.assertEqual(spy[0][1], '0')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    @mock.patch(CORE+'check_cache', return_value=['not_cached'])
    def test_update_progress_bar_called_with_15_if_not_cached(self, mock_ch,
                                                              mock_bar):
        self.proc._check_cache(self.paths, self.cache)

        mock_bar.assert_called_once_with(15)

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    @mock.patch(CORE+'check_cache', return_value=[])
    def test_update_progress_bar_called_with_55_if_cached(self, mock_ch,
                                                          mock_bar):
        self.proc._check_cache(self.paths, self.cache)

        mock_bar.assert_called_once_with(55)


class TestMethodExtendCache(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.cache = {'path': 'hash'}
        self.paths = ['path2']
        self.hashes = ['hash2']

    def test_hash_added_to_cache_if_it_is_not_None(self):
        res = self.proc._extend_cache(self.cache, self.paths, self.hashes)

        self.assertDictEqual(res, {'path': 'hash', 'path2': 'hash2'})

    def test_log_error_if_hash_is_None(self):
        with self.assertLogs('main.processing', 'ERROR'):
            self.proc._extend_cache(self.cache, self.paths, [None])

    def test_set_error_attr_to_True_if_hash_is_None(self):
        self.proc._extend_cache(self.cache, self.paths, [None])

        self.assertTrue(self.proc.errors)

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_progress_bar_called_with_55(self, mock_bar):
        self.proc._extend_cache(self.cache, self.paths, self.hashes)

        mock_bar.assert_called_once_with(55)


class TestMethodImageGrouping(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.imgs = ['img']

    @mock.patch(CORE+'image_grouping')
    def test_args_core_image_grouping_called_with(self, mock_group):
        self.proc._image_grouping(self.imgs)

        mock_group.assert_called_once_with(self.imgs, self.proc.sensitivity)

    @mock.patch(CORE+'image_grouping', return_value=[['img']])
    def test_return_core_image_grouping_result(self, mock_group):
        res = self.proc._image_grouping(self.imgs)

        self.assertEqual(res, [['img']])

    @mock.patch(CORE+'image_grouping', return_value=[['img1', 'img2']])
    def test_emits_update_info_signal_with_proper_args(self, mock_group):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        self.proc._image_grouping(self.imgs)

        self.assertEqual(spy[0][0], 'image_groups')
        self.assertEqual(spy[0][1], '1')
        self.assertEqual(spy[1][0], 'duplicates')
        self.assertEqual(spy[1][1], '2')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    @mock.patch(CORE+'image_grouping')
    def test_update_progress_bar_called_with_65(self, mock_group, mock_bar):
        self.proc._image_grouping(self.imgs)

        mock_bar.assert_called_once_with(65)


class TestMethodMakeThumbnails(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.img_groups = [[mock.Mock()], [mock.Mock()]]

    @mock.patch(PROCESSING+'ImageProcessing._imap')
    def test_args_imap_called_with(self, mock_imap):
        self.proc._make_thumbnails(self.img_groups)

        mock_imap.assert_called_once_with(
            self.proc._thumbnail_args_unpacker,
            [(self.img_groups[0][0], self.proc.conf['size']),
             (self.img_groups[1][0], self.proc.conf['size'])],
            'thumbnails'
        )

    @mock.patch(PROCESSING+'ImageProcessing._imap')
    def test_return_same_image_groups(self, mock_imap):
        res = self.proc._make_thumbnails(self.img_groups)

        self.assertEqual(res[0][0], self.img_groups[0][0])
        self.assertEqual(res[1][0], self.img_groups[1][0])

    @mock.patch(PROCESSING+'ImageProcessing._imap', return_value=['t1', 't2'])
    def test_assign_thumbnails_to_image_attrs(self, mock_imap):
        self.proc._make_thumbnails(self.img_groups)

        self.assertEqual(self.img_groups[0][0].thumbnail, 't1')
        self.assertEqual(self.img_groups[1][0].thumbnail, 't2')


class TestMethodUpdateProgressBar(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.value = 5

    def test_change_progress_bar_value_attr(self):
        self.proc._update_progress_bar(self.value)

        self.assertEqual(self.proc.progress_bar_value, self.value)

    def test_emit_update_progressbar_signal(self):
        spy = QtTest.QSignalSpy(self.proc.signals.update_progressbar)
        self.proc._update_progress_bar(self.value)

        self.assertEqual(spy[0][0], self.value)


class TestMethodImap(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.func = mock.Mock()
        self.collection = ['item']
        self.label = 'label'

        self.mock_Pool = mock.MagicMock()
        mock_context_obj = mock.Mock()
        self.mock_Pool.__enter__.return_value = mock_context_obj
        self.imap_return = ['return' for item in self.collection]
        mock_context_obj.imap.return_value = self.imap_return

    def test_return_empty_list_if_pass_empty_collection(self):
        res = self.proc._imap(self.func, [], self.label)

        self.assertListEqual(res, [])

    def test_emit_update_info_with_passed_label_arg(self):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            self.proc._imap(self.func, self.collection, self.label)

        self.assertEqual(spy[0][0], self.label)
        self.assertEqual(spy[0][1], '1')
        self.assertEqual(spy[1][0], self.label)
        self.assertEqual(spy[1][1], '0')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_prog_bar_called_with_current_val_plus_step(self, mock_bar):
        self.proc.progress_bar_value = 21
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            self.proc._imap(self.func, self.collection, self.label)

        # step == 35 / len(collection) == 35 in this case
        mock_bar.assert_called_once_with(56)

    def test_return_imap_result(self):
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            res = self.proc._imap(self.func, self.collection, self.label)

        self.assertListEqual(res, self.imap_return)

    def test_raise_InterruptProcessing_if_interrupt_attr_is_True(self):
        self.proc.interrupt = True
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            with self.assertRaises(exception.InterruptProcessing):
                self.proc._imap(self.func, self.collection, self.label)


class TestMethodRun(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.FIND_IMAGES = PROCESSING+'ImageProcessing._find_images'

    # FUNCTION '_FIND_IMAGES' IS USED IN THESE TESTS JUST
    # SO WE DO NOT HAVE TO GO THROUGH MAIN BRANCH IN 'TRY'
    # SINCE WE TEST OTHER BLOCKS

    def test_log_info_if_some_func_raise_InterruptProcessing(self):
        exc = exception.InterruptProcessing
        with mock.patch(self.FIND_IMAGES, side_effect=exc):
            with self.assertLogs('main.processing', 'INFO'):
                self.proc.run()

    def test_log_error_if_some_func_raise_general_exception(self):
        with mock.patch(self.FIND_IMAGES, side_effect=Exception):
            with self.assertLogs('main.processing', 'ERROR'):
                self.proc.run()

    def test_set_errors_attr_True_if_some_func_raise_general_exception(self):
        with mock.patch(self.FIND_IMAGES, side_effect=Exception):
            self.proc.run()

        self.assertTrue(self.proc.errors)

    def test_emit_signal_finished(self):
        spy = QtTest.QSignalSpy(self.proc.signals.finished)
        with mock.patch(self.FIND_IMAGES, side_effect=Exception):
            self.proc.run()

        self.assertEqual(len(spy), 1)

    def test_emit_signal_error_if_attr_error_is_True(self):
        self.proc.errors = True
        spy = QtTest.QSignalSpy(self.proc.signals.error)
        with mock.patch(self.FIND_IMAGES, side_effect=Exception):
            self.proc.run()

        self.assertEqual(len(spy), 1)
