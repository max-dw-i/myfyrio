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
CACHE = 'doppelganger.cache.'
PROCESSING = 'doppelganger.processing.'


class TestClassImageProcessing(TestCase):

    def setUp(self):
        self.mw_signals = signals.Signals()
        self.folders = []
        self.sensitivity = 0
        self.CONF = {'sort': 0,
                     'subfolders': True,
                     'size': 200,
                     'filter_img_size': False,
                     'min_width': 5,
                     'max_width': 10,
                     'min_height': 5,
                     'max_height': 10,
                     'cores': 16}
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

    def setUp(self):
        super().setUp()

        self.mock_image = mock.Mock()
        self.mock_image.width = 5
        self.mock_image.height = 5
        self.found_images = (img for img in [self.mock_image])

    def test_args_core_find_images_called_with(self):
        with mock.patch(CORE+'find_image') as mock_find:
            self.proc._find_images()

        mock_find.assert_called_once_with(self.folders,
                                          self.CONF['subfolders'])

    def test_return_if_no_image_filter_size(self):
        self.mock_image.width = 100
        self.mock_image.height = 100
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, {self.mock_image})

    def test_return_if_image_filter_size_and_image_fits(self):
        self.CONF['filter_img_size'] = True
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, {self.mock_image})

    def test_return_if_image_filter_size_and_too_small_image_width(self):
        self.CONF['filter_img_size'] = True
        self.mock_image.width = 4
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_return_if_image_filter_size_and_too_big_image_width(self):
        self.CONF['filter_img_size'] = True
        self.mock_image.width = 11
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_return_if_image_filter_size_and_too_small_image_height(self):
        self.CONF['filter_img_size'] = True
        self.mock_image.height = 4
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_return_if_image_filter_size_and_too_big_image_height(self):
        self.CONF['filter_img_size'] = True
        self.mock_image.height = 11
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_raise_InterruptProcessing_if_attr_interrupt_True(self):
        self.proc.interrupt = True
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            with self.assertRaises(exception.InterruptProcessing):
                self.proc._find_images()

    def test_emits_update_info_signal_with_loaded_images_arg(self):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 'loaded_images')
        self.assertEqual(spy[0][1], '1')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_progress_bar_called_with_5(self, mock_bar):
        with mock.patch(CORE+'find_image'):
            self.proc._find_images()

        mock_bar.assert_called_once_with(5)


class TestMethodLoadCache(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.mock_Cache = mock.Mock()

    def test_return_Cache_object(self):
        with mock.patch(PROCESSING+'Cache', return_value=self.mock_Cache):
            res = self.proc._load_cache()

        self.assertIs(res, self.mock_Cache)

    def test_args_Cache_load_called_with(self):
        with mock.patch(PROCESSING+'Cache', return_value=self.mock_Cache):
            self.proc._load_cache()

        self.mock_Cache.load.assert_called_once_with(str(self.proc.CACHE_FILE))

    def test_raise_OSError_if_core_load_cache_EOFErrores(self):
        self.mock_Cache.load.side_effect = OSError
        with mock.patch(PROCESSING+'Cache', return_value=self.mock_Cache):
            with self.assertRaises(OSError):
                self.proc._load_cache()

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_progress_bar_called_with_10(self, mock_bar):
        with mock.patch(PROCESSING+'Cache', return_value=self.mock_Cache):
            self.proc._load_cache()

        mock_bar.assert_called_once_with(10)


class TestMethodCheckCache(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.mock_img1 = mock.Mock()
        self.mock_img1.path = 'path'
        self.mock_img2 = mock.Mock()
        self.mock_img2.path = 'path_not_in_cache'
        self.paths = [self.mock_img1, self.mock_img2]
        self.cache = {'path': 'hash'}

    def test_return_proper_lists(self):
        cached, not_cached = self.proc._check_cache(self.paths, self.cache)

        self.assertListEqual(cached, [self.mock_img1])
        self.assertListEqual(not_cached, [self.mock_img2])

    def test_emits_update_info_signal_with_found_in_cache_arg(self):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        self.proc._check_cache(self.paths, self.cache)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 'found_in_cache')
        self.assertEqual(spy[0][1], '1')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_progress_bar_called_with_15_if_not_cached(self, mock_bar):
        self.proc._check_cache(self.paths, self.cache)

        mock_bar.assert_called_once_with(15)

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_progress_bar_called_with_55_if_cached(self, mock_bar):
        paths = self.paths[:1]
        self.proc._check_cache(paths, self.cache)

        mock_bar.assert_called_once_with(55)


class TestMethodUpdateCache(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.cache = {'path': 'hash'}
        self.mock_img = mock.Mock()
        self.mock_img.path = 'path2'
        self.mock_img.dhash = 'hash2'
        self.images = [self.mock_img]

    def test_hash_added_to_cache_if_it_is_not_minus_1(self):
        res = self.proc._update_cache(self.cache, self.images)

        self.assertDictEqual(res, {'path': 'hash', 'path2': 'hash2'})

    def test_log_error_if_hash_is_minus_1(self):
        self.mock_img.dhash = -1
        with self.assertLogs('main.processing', 'ERROR'):
            self.proc._update_cache(self.cache, self.images)

    def test_set_error_attr_to_True_if_hash_is_minus_1(self):
        self.mock_img.dhash = -1
        self.proc._update_cache(self.cache, self.images)

        self.assertTrue(self.proc.errors)

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_progress_bar_called_with_55(self, mock_bar):
        self.proc._update_cache(self.cache, self.images)

        mock_bar.assert_called_once_with(55)


class TestMethodCalculateHashes(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.mock_img = mock.Mock()
        self.mock_img = 'path'
        self.images = [self.mock_img]

        self.mock_Pool = mock.MagicMock()
        self.mock_context_obj = mock.Mock()
        self.mock_Pool.__enter__.return_value = self.mock_context_obj
        self.imap_return = (h for h in self.images)
        self.mock_context_obj.imap.return_value = self.imap_return

    def test_Pool_called_with_available_cores_result(self):
        with mock.patch(PROCESSING+'Pool') as mock_Pool_call:
            with mock.patch(PROCESSING+'ImageProcessing._available_cores',
                            return_value=7):
                self.proc._calculate_hashes(self.images)

        mock_Pool_call.assert_called_once_with(processes=7)

    def test_emit_update_info(self):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            self.proc._calculate_hashes(self.images)

        self.assertEqual(spy[0][0], 'remaining_images')
        self.assertEqual(spy[0][1], '1')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_prog_bar_called_with_current_val_plus_step(self, mock_bar):
        self.proc.progress_bar_value = 21
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            self.proc._calculate_hashes(self.images)

        # step == 35 / len(collection) == 35 in this case
        mock_bar.assert_called_once_with(56)

    def test_func_result(self):
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            res = self.proc._calculate_hashes(self.images)

        self.assertListEqual(res, self.images)

    def test_raise_InterruptProcessing_if_interrupt_attr_is_True(self):
        self.proc.interrupt = True
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            with self.assertRaises(exception.InterruptProcessing):
                self.proc._calculate_hashes(self.images)


class TestMethodImageGrouping(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.imgs = ['img']

    @mock.patch(CORE+'image_grouping')
    def test_args_core_image_grouping_called_with(self, mock_group):
        self.proc._image_grouping(self.imgs)

        mock_group.assert_called_once_with(self.imgs, self.proc.sensitivity)

    @mock.patch(CORE+'image_grouping', return_value=(gs for gs in [[['img']]]))
    def test_return_core_image_grouping_result(self, mock_group):
        res = self.proc._image_grouping(self.imgs)

        self.assertEqual(res, [['img']])

    @mock.patch(CORE+'image_grouping', return_value=(gs for gs in [[['img']]]))
    def test_raise_InterruptProcessing(self, mock_group):
        self.proc.interrupt = True
        with self.assertRaises(exception.InterruptProcessing):
            self.proc._image_grouping(self.imgs)

    @mock.patch(CORE+'image_grouping',
                return_value=(gs for gs in [[['img1', 'img2']]]))
    def test_emits_update_info_signal_with_proper_args(self, mock_group):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        self.proc._image_grouping(self.imgs)

        self.assertEqual(spy[0][0], 'duplicates')
        self.assertEqual(spy[0][1], '2')
        self.assertEqual(spy[1][0], 'image_groups')
        self.assertEqual(spy[1][1], '1')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    @mock.patch(CORE+'image_grouping')
    def test_update_progress_bar_called_with_65(self, mock_group, mock_bar):
        self.proc._image_grouping(self.imgs)

        mock_bar.assert_called_once_with(65)


class TestMethodMakeThumbnails(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.img_groups = [[mock.Mock()]]
        self.thumbnails = ['thumb1']

        self.func = mock.Mock()
        self.collection = ['item']
        self.label = 'label'

        self.mock_Pool = mock.MagicMock()
        self.mock_context_obj = mock.Mock()
        self.mock_Pool.__enter__.return_value = self.mock_context_obj
        self.imap_return = (th for th in self.thumbnails)
        self.mock_context_obj.imap.return_value = self.imap_return

    def test_Pool_called_with_available_cores_result(self):
        with mock.patch(PROCESSING+'Pool') as mock_Pool_call:
            with mock.patch(PROCESSING+'ImageProcessing._available_cores',
                            return_value=7):
                list(self.proc._make_thumbnails(self.img_groups))

        mock_Pool_call.assert_called_once_with(processes=7)

    def test_args_imap_called_with(self):
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            list(self.proc._make_thumbnails(self.img_groups))

        self.mock_context_obj.imap.assert_called_once_with(
            self.proc._thumbnail_args_unpacker,
            [(self.img_groups[0][0], self.proc.conf['size'])]
        )

    def test_raise_InterruptProcessing_if_interrupt_attr_is_True(self):
        self.proc.interrupt = True
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            with self.assertRaises(exception.InterruptProcessing):
                list(self.proc._make_thumbnails(self.img_groups))

    def test_assign_thumbnails_to_image_attrs(self):
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            list(self.proc._make_thumbnails(self.img_groups))

        self.assertEqual(self.img_groups[0][0].thumb, self.thumbnails[0])

    def test_emit_image_groups(self):
        # Add another group
        self.img_groups.append([mock.Mock()])
        self.thumbnails.append('thumb2')
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            res = list(self.proc._make_thumbnails(self.img_groups))

        self.assertListEqual(res[0], self.img_groups[0])
        self.assertListEqual(res[1], self.img_groups[1])

    def test_emit_update_info(self):
        spy = QtTest.QSignalSpy(self.proc.signals.update_info)
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            list(self.proc._make_thumbnails(self.img_groups))

        self.assertEqual(spy[0][0], 'thumbnails')
        self.assertEqual(spy[0][1], '1')

    @mock.patch(PROCESSING+'ImageProcessing._update_progress_bar')
    def test_update_prog_bar_called_with_current_val_plus_step(self, mock_bar):
        self.proc.progress_bar_value = 21
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            list(self.proc._make_thumbnails(self.img_groups))

        # step == 35 / len(collection) == 35 in this case
        mock_bar.assert_called_once_with(56)


class TestMethodThumbnailArgsUnpacker(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.mock_image = mock.Mock()
        self.size = 333

    def test_Image_thumbnail_called_with_size_arg(self):
        self.proc._thumbnail_args_unpacker((self.mock_image, self.size))

        self.mock_image.thumbnail.assert_called_once_with(self.size)

    def test_return_Image_thumbnail_result(self):
        thumbnail = 'thumbnail'
        self.mock_image.thumbnail.return_value = thumbnail
        res = self.proc._thumbnail_args_unpacker((self.mock_image, self.size))

        self.assertEqual(res, thumbnail)

    def test_log_if_Image_thumbnail_raise_OSError(self):
        self.mock_image.thumbnail.side_effect = OSError
        with self.assertLogs('main.processing', 'ERROR'):
            self.proc._thumbnail_args_unpacker((self.mock_image, self.size))

    def test_return_empty_QByteArray_if_Image_thumbnail_raise_OSError(self):
        self.mock_image.thumbnail.side_effect = OSError
        res = self.proc._thumbnail_args_unpacker((self.mock_image, self.size))

        self.assertIsInstance(res, QtCore.QByteArray)
        self.assertEqual(res.size(), 0)


class TestMethodAvailableCores(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.mock_sched = mock.MagicMock()
        self.mock_sched.__len__.return_value = 1

    def test_sched_getaffinity_called_with_0(self):
        with mock.patch('os.sched_getaffinity',
                        return_value=self.mock_sched) as mock_sched_call:
            self.proc._available_cores()

        mock_sched_call.assert_called_once_with(0)

    def test_return_available_cores(self):
        available_cores = 8
        self.mock_sched.__len__.return_value = available_cores
        with mock.patch('os.sched_getaffinity', return_value=self.mock_sched):
            res = self.proc._available_cores()

        self.assertEqual(res, available_cores)

    def test_return_config_cores(self):
        available_cores = 32
        self.mock_sched.__len__.return_value = available_cores
        with mock.patch('os.sched_getaffinity', return_value=self.mock_sched):
            res = self.proc._available_cores()

        self.assertEqual(res, self.proc.conf['cores'])


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
