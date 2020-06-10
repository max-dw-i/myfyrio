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
from multiprocessing import pool
from unittest import TestCase, mock

from PyQt5 import QtGui, QtTest, QtWidgets

from doppelganger import cache, core, resources, workers
from doppelganger.gui import thumbnailwidget

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


# pylint: disable=missing-class-docstring

CORE = 'doppelganger.core.'
CACHE = 'doppelganger.cache.'
PROCESSING = 'doppelganger.workers.'


class TestClassImageProcessing(TestCase):

    def setUp(self):
        self.folders = []
        self.conf = {'sort': 0,
                     'subfolders': True,
                     'size': 200,
                     'filter_img_size': False,
                     'min_width': 5,
                     'max_width': 10,
                     'min_height': 5,
                     'max_height': 10,
                     'cores': 16,
                     'sensitivity': 0}
        self.proc = workers.ImageProcessing(self.folders, self.conf)


class TestMethodInit(TestClassImageProcessing):

    def test_attrs_initial_values(self):
        self.assertListEqual(self.proc._folders, [])
        self.assertEqual(self.proc._conf, self.conf)
        self.assertFalse(self.proc._interrupted)
        self.assertFalse(self.proc._error)
        self.assertEqual(self.proc._progressbar_value, 0.0)

    def test_attributes(self):
        self.assertEqual(workers.ImageProcessing.PROG_MIN, 0)
        self.assertEqual(workers.ImageProcessing.PROG_CHECK_CACHE, 5)
        self.assertEqual(workers.ImageProcessing.PROG_CALC, 35)
        self.assertEqual(workers.ImageProcessing.PROG_UPD_CACHE, 40)
        self.assertEqual(workers.ImageProcessing.PROG_GROUPING, 70)
        self.assertEqual(workers.ImageProcessing.PROG_MAX, 70)


class TestClassImageProcessingMethodRun(TestClassImageProcessing):

    PATCH_FIND = PROCESSING+'ImageProcessing._find_images'
    PATCH_LOAD = PROCESSING+'ImageProcessing._load_cache'

    def test_early_return_if_images_not_found(self):
        with mock.patch(self.PATCH_FIND, return_value=[]):
            with mock.patch(self.PATCH_LOAD) as mock_load_call:
                self.proc.run()

        mock_load_call.assert_not_called()

    # FUNCTION '_FIND_IMAGES' IS USED IN THESE TESTS JUST
    # SO WE DO NOT HAVE TO GO THROUGH MAIN BRANCH IN 'TRY'
    # SINCE WE TEST OTHER BLOCKS

    def test_log_error_if_some_func_raise_any_Exception(self):
        with mock.patch(self.PATCH_FIND, side_effect=Exception):
            with self.assertLogs('main.workers', 'ERROR'):
                self.proc.run()

    def test_set_attr_error_to_True_if_some_func_raise_any_Exception(self):
        with mock.patch(self.PATCH_FIND, side_effect=Exception):
            self.proc.run()

        self.assertTrue(self.proc.error)

    def test_emit_signal_error_if_attr_error_is_True(self):
        self.proc._error = True
        spy = QtTest.QSignalSpy(self.proc.error)
        with mock.patch(self.PATCH_FIND, side_effect=Exception):
            self.proc.run()

        self.assertEqual(len(spy), 1)


class TestClassImageProcessingMethodFindImages(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.mock_image = mock.Mock(spec=core.Image)
        self.mock_image.width = 5
        self.mock_image.height = 5
        self.found_images = (img for img in [self.mock_image])

    def test_core_find_images_called_with_folders_and_recursive_args(self):
        with mock.patch(CORE+'find_image') as mock_find_call:
            self.proc._find_images()

        mock_find_call.assert_called_once_with(self.folders,
                                               self.conf['subfolders'])

    def test_return_images_if_no_size_filter(self):
        self.mock_image.width = 100
        self.mock_image.height = 100
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, {self.mock_image})

    def test_emit_images_loaded_signal_if_no_size_filter(self):
        self.mock_image.width = 100
        self.mock_image.height = 100
        spy = QtTest.QSignalSpy(self.proc.images_loaded)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 1)

    def test_return_images_if_size_filter_and_image_fits(self):
        self.conf['filter_img_size'] = True
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, {self.mock_image})

    def test_emit_images_loaded_signal_if_size_filter_and_image_fits(self):
        self.conf['filter_img_size'] = True
        spy = QtTest.QSignalSpy(self.proc.images_loaded)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 1)

    def test_return_empty_set_if_size_filter_and_too_small_width(self):
        self.conf['filter_img_size'] = True
        self.mock_image.width = 4
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_not_emit_images_loaded_if_size_filter_and_too_small_width(self):
        self.conf['filter_img_size'] = True
        self.mock_image.width = 4
        spy = QtTest.QSignalSpy(self.proc.images_loaded)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 0)

    def test_emit_empty_finished_if_size_filter_and_too_small_width(self):
        self.conf['filter_img_size'] = True
        self.mock_image.width = 4
        spy = QtTest.QSignalSpy(self.proc.finished)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertListEqual(spy[0][0], [])

    def test_return_empty_set_if_size_filter_and_too_big_width(self):
        self.conf['filter_img_size'] = True
        self.mock_image.width = 11
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_not_emit_images_loaded_if_size_filter_and_too_big_width(self):
        self.conf['filter_img_size'] = True
        self.mock_image.width = 11
        spy = QtTest.QSignalSpy(self.proc.images_loaded)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 0)

    def test_emit_empty_finished_if_size_filter_and_too_big_width(self):
        self.conf['filter_img_size'] = True
        self.mock_image.width = 11
        spy = QtTest.QSignalSpy(self.proc.finished)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertListEqual(spy[0][0], [])

    def test_return_empty_set_if_size_filter_and_too_small_height(self):
        self.conf['filter_img_size'] = True
        self.mock_image.height = 4
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_not_emit_images_loaded_if_size_filter_and_too_small_height(self):
        self.conf['filter_img_size'] = True
        self.mock_image.height = 4
        spy = QtTest.QSignalSpy(self.proc.images_loaded)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 0)

    def test_emit_empty_finished_if_size_filter_and_too_small_height(self):
        self.conf['filter_img_size'] = True
        self.mock_image.height = 4
        spy = QtTest.QSignalSpy(self.proc.finished)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertListEqual(spy[0][0], [])

    def test_return_empty_set_if_size_filter_and_too_big_height(self):
        self.conf['filter_img_size'] = True
        self.mock_image.height = 11
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_not_emit_images_loaded_if_size_filter_and_too_big_height(self):
        self.conf['filter_img_size'] = True
        self.mock_image.height = 11
        spy = QtTest.QSignalSpy(self.proc.images_loaded)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 0)

    def test_emit_empty_finished_if_size_filter_and_too_big_height(self):
        self.conf['filter_img_size'] = True
        self.mock_image.height = 11
        spy = QtTest.QSignalSpy(self.proc.finished)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertListEqual(spy[0][0], [])

    def test_emit_interrupted_signal_if_attr_interrupt_True(self):
        self.proc._interrupted = True
        spy = QtTest.QSignalSpy(self.proc.interrupted)
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)

    def test_return_empty_set_if_attr_interrupt_True(self):
        self.proc._interrupted = True
        with mock.patch(CORE+'find_image', return_value=self.found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())

    def test_emit_empty_finished_signal_if_images_not_found(self):
        found_images = (img for img in [])
        spy = QtTest.QSignalSpy(self.proc.finished)
        with mock.patch(CORE+'find_image', return_value=found_images):
            self.proc._find_images()

        self.assertEqual(len(spy), 1)
        self.assertListEqual(spy[0][0], [])

    def test_return_empty_set_if_images_not_found(self):
        found_images = (img for img in [])
        with mock.patch(CORE+'find_image', return_value=found_images):
            res = self.proc._find_images()

        self.assertSetEqual(res, set())


class TestClassImageProcessingMethodLoadCache(TestClassImageProcessing):

    def test_load_called_with_cache_file_path(self):
        mock_cache = mock.Mock(spec=cache.Cache)
        with mock.patch(PROCESSING+'Cache', return_value=mock_cache):
            self.proc._load_cache()

        mock_cache.load.assert_called_once_with(
            resources.Cache.CACHE.abs_path # pylint: disable=no-member
        )

    def test_return_Cache_object(self):
        mock_cache = mock.Mock(spec=cache.Cache)
        with mock.patch(PROCESSING+'Cache', return_value=mock_cache):
            res = self.proc._load_cache()

        self.assertEqual(res, mock_cache)

    def test_cache_empty_if_load_raise_FileNotFoundError(self):
        with mock.patch(PROCESSING+'Cache.load',
                        side_effect=FileNotFoundError):
            res = self.proc._load_cache()

        self.assertDictEqual(res.data, {})

    def test_cache_empty_if_load_raise_EOFError(self):
        with mock.patch(PROCESSING+'Cache.load', side_effect=EOFError):
            res = self.proc._load_cache()

        self.assertDictEqual(res.data, {})

    def test_logging_if_load_raise_EOFError(self):
        with mock.patch(PROCESSING+'Cache.load', side_effect=EOFError):
            with self.assertLogs('main.workers', 'ERROR'):
                self.proc._load_cache()

    def test_set_attr_error_to_True_if_load_raise_EOFError(self):
        self.proc._error = False
        with mock.patch(PROCESSING+'Cache.load', side_effect=EOFError):
            self.proc._load_cache()

        self.assertTrue(self.proc._error)


class TestMethodCheckCache(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.mock_img1 = mock.Mock(spec=core.Image)
        self.mock_img1.path = 'path'
        self.mock_img2 = mock.Mock(spec=core.Image)
        self.mock_img2.path = 'path_not_in_cache'
        self.paths = [self.mock_img1, self.mock_img2]
        self.cache = {'path': 'hash'}

    def test_return_right_cached_and_not_cached_lists(self):
        cached, not_cached = self.proc._check_cache(self.paths, self.cache)

        self.assertListEqual(cached, [self.mock_img1])
        self.assertListEqual(not_cached, [self.mock_img2])

    def test_hash_from_cache_assigned_to_attr_dhash_of_cached_image(self):
        self.proc._check_cache(self.paths, self.cache)

        self.assertEqual(self.mock_img1.dhash, 'hash')

    def test_emit_found_in_cache_with_found_in_cache_images_number_arg(self):
        spy = QtTest.QSignalSpy(self.proc.found_in_cache)
        self.proc._check_cache(self.paths, self.cache)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 1)

    def test_update_progressbar_called_with_35_if_there_arent_not_cached(self):
        paths = self.paths[:1]
        PATCH_PROGBAR = PROCESSING+'ImageProcessing._update_progressbar'
        with mock.patch(PATCH_PROGBAR) as mock_bar_call:
            self.proc._check_cache(paths, self.cache)

        mock_bar_call.assert_called_once_with(
            workers.ImageProcessing.PROG_CALC
        )

    def test_update_progressbar_called_with_5_if_there_are_not_cached(self):
        PATCH_PROGBAR = PROCESSING+'ImageProcessing._update_progressbar'
        with mock.patch(PATCH_PROGBAR) as mock_bar_call:
            self.proc._check_cache(self.paths, self.cache)

        mock_bar_call.assert_called_once_with(
            workers.ImageProcessing.PROG_CHECK_CACHE
        )


class TestClassImageProcessingMethodCalculateHashes(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        mock_img = mock.Mock(spec=core.Image)
        self.images = [mock_img]

        self.mock_Pool = mock.MagicMock(spec=pool.Pool)
        self.mock_context_obj = mock.Mock()
        self.mock_Pool.__enter__.return_value = self.mock_context_obj
        imap_return = (h for h in self.images)
        self.mock_context_obj.imap.return_value = imap_return

    def test_Pool_called_with_available_cores_result(self):
        with mock.patch(PROCESSING+'Pool') as mock_Pool_call:
            with mock.patch(PROCESSING+'ImageProcessing._available_cores',
                            return_value=7):
                self.proc._calculate_hashes(self.images)

        mock_Pool_call.assert_called_once_with(processes=7)

    def test_imap_called_with_dhash_parallel_and_images_args(self):
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            self.proc._calculate_hashes(self.images)

        self.mock_context_obj.imap.assert_called_once_with(
            core.Image.dhash_parallel, self.images
        )

    def test_return_same_passed_images(self):
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            res = self.proc._calculate_hashes(self.images)

        self.assertListEqual(res, self.images)

    def test_emit_hashes_calculated_with_calculated_hashes_number_arg(self):
        spy = QtTest.QSignalSpy(self.proc.hashes_calculated)
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            self.proc._calculate_hashes(self.images)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 1)

    def test_update_progressbar_called_with_current_value_plus_step(self):
        self.proc._progressbar_value = 2
        PATCH_PROGBAR = PROCESSING+'ImageProcessing._update_progressbar'
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            with mock.patch(PATCH_PROGBAR) as mock_bar_call:
                self.proc._calculate_hashes(self.images)

        # step == 30 / len(collection) == 30 in this case
        calls = [mock.call(32), mock.call(workers.ImageProcessing.PROG_CALC)]
        mock_bar_call.assert_has_calls(calls)

    def test_return_sublist_of_passed_images_if_attr_interrupted_is_True(self):
        self.proc._interrupted = True
        with mock.patch(PROCESSING+'Pool', return_value=self.mock_Pool):
            res = self.proc._calculate_hashes(self.images)

        self.assertGreater(self.images, res)


class TestClassImageProcessingMethodUpdateCache(TestClassImageProcessing):

    PATCH_SAVE = PROCESSING + 'Cache.save'

    def setUp(self):
        super().setUp()

        self.mock_cache = mock.MagicMock(spec=cache.Cache)

        self.mock_image = mock.Mock(spec=core.Image)
        self.mock_image.path = 'path'
        self.mock_image.dhash = 'hash'
        self.images = [self.mock_image]

    def test_hash_added_to_cache_if_it_is_not_minus_1(self):
        self.proc._update_cache(self.mock_cache, self.images)

        self.mock_cache.__setitem__.assert_called_once_with('path', 'hash')

    def test_log_error_if_hash_is_minus_1(self):
        self.mock_image.dhash = -1
        with self.assertLogs('main.workers', 'ERROR'):
            self.proc._update_cache(self.mock_cache, self.images)

    def test_set_attr_error_to_True_if_hash_is_minus_1(self):
        self.proc._error = False
        self.mock_image.dhash = -1
        self.proc._update_cache(self.mock_cache, self.images)

        self.assertTrue(self.proc._error)

    def test_cache_save_called_with_cache_file_path_arg(self):
        self.proc._update_cache(self.mock_cache, self.images)

        self.mock_cache.save.assert_called_once_with(
            resources.Cache.CACHE.abs_path # pylint: disable=no-member
        )

    def test_logging_if_cache_save_raise_OSError(self):
        self.mock_cache.save.side_effect = OSError
        with self.assertLogs('main.workers', 'ERROR'):
            self.proc._update_cache(self.mock_cache, self.images)

    def test_attr_eror_set_to_True_if_cache_save_raise_OSError(self):
        self.proc._error = False
        self.mock_cache.save.side_effect = OSError
        self.proc._update_cache(self.mock_cache, self.images)

        self.assertTrue(self.proc._error)

    @mock.patch(PROCESSING+'ImageProcessing._update_progressbar')
    def test_update_progressbar_called_with_40(self, mock_bar):
        self.proc._update_cache(self.mock_cache, self.images)

        mock_bar.assert_called_once_with(
            workers.ImageProcessing.PROG_UPD_CACHE
        )


class TestClassImageProcessingMethodImageGrouping(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.images = ['image1', 'image2']
        self.groups = [self.images]

    def test_core_image_grouping_called_with_images_and_sensitivity_args(self):
        with mock.patch(CORE+'image_grouping') as mock_group_call:
            self.proc._image_grouping(self.images)

        mock_group_call.assert_called_once_with(self.images,
                                                self.conf['sensitivity'])

    def test_emit_finished_signal_with_found_groups_arg(self):
        gen = (gs for gs in [self.groups])
        spy = QtTest.QSignalSpy(self.proc.finished)
        with mock.patch(CORE+'image_grouping', return_value=gen):
            self.proc._image_grouping(self.images)

        self.assertEqual(len(spy), 1)
        self.assertListEqual(spy[0][0], self.groups)

    def test_emit_interrupted_signal_if_attr_interrupted_is_True(self):
        self.proc._interrupted = True
        gen = (gs for gs in [self.groups])
        spy = QtTest.QSignalSpy(self.proc.interrupted)
        with mock.patch(CORE+'image_grouping', return_value=gen):
            self.proc._image_grouping(self.images)

        self.assertEqual(len(spy), 1)

    def test_not_emit_finished_signal_if_attr_interrupted_is_True(self):
        self.proc._interrupted = True
        gen = (gs for gs in [self.groups])
        spy = QtTest.QSignalSpy(self.proc.finished)
        with mock.patch(CORE+'image_grouping', return_value=gen):
            self.proc._image_grouping(self.images)

        self.assertEqual(len(spy), 0)

    def test_emit_duplicates_found_signal_with_duplicates_found_num_arg(self):
        gen = (gs for gs in [self.groups])
        spy = QtTest.QSignalSpy(self.proc.duplicates_found)
        with mock.patch(CORE+'image_grouping', return_value=gen):
            self.proc._image_grouping(self.images)

        self.assertEqual(spy[0][0], 2)

    def test_emit_groups_found_signal_with_duplicate_groups_found_arg(self):
        gen = (gs for gs in [self.groups])
        spy = QtTest.QSignalSpy(self.proc.groups_found)
        with mock.patch(CORE+'image_grouping', return_value=gen):
            self.proc._image_grouping(self.images)

        self.assertEqual(spy[0][0], 1)

    def test_update_progress_bar_called_with_65(self):
        self.proc._progressbar_value = 30
        gen = (gs for gs in [self.groups])
        with mock.patch(CORE+'image_grouping', return_value=gen):
            PATCH_PROGBAR = PROCESSING + 'ImageProcessing._update_progressbar'
            with mock.patch(PATCH_PROGBAR) as mock_bar_call:
                self.proc._image_grouping(self.images)

        # step == 30 / len(images) == 15 in this case
        calls = [mock.call(45),
                 mock.call(workers.ImageProcessing.PROG_GROUPING)]
        mock_bar_call.assert_has_calls(calls)


class TestClassImageProcessingMethodAvailableCores(TestClassImageProcessing):

    def setUp(self):
        super().setUp()

        self.mock_sched = mock.MagicMock(spec=set)
        self.mock_sched.__len__.return_value = 1

    def test_sched_getaffinity_called_with_0(self):
        with mock.patch('os.sched_getaffinity',
                        return_value=self.mock_sched) as mock_sched_call:
            self.proc._available_cores()

        mock_sched_call.assert_called_once_with(0)

    def test_return_available_cores_if_cores_num_in_conf_too_big(self):
        available_cores = 8
        self.mock_sched.__len__.return_value = available_cores
        with mock.patch('os.sched_getaffinity', return_value=self.mock_sched):
            res = self.proc._available_cores()

        self.assertEqual(res, available_cores)

    def test_return_config_cores_if_cores_num_in_conf_is_ok(self):
        available_cores = 32
        self.mock_sched.__len__.return_value = available_cores
        with mock.patch('os.sched_getaffinity', return_value=self.mock_sched):
            res = self.proc._available_cores()

        self.assertEqual(res, self.proc._conf['cores'])


class TestClassImageProcessingMetodUpdateProgressbar(TestClassImageProcessing):

    def test_emit_update_progressbar_signal_if_whole_part_changed(self):
        self.proc._progressbar_value = 10.5
        spy = QtTest.QSignalSpy(self.proc.update_progressbar)
        self.proc._update_progressbar(11.2)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 11)

    def test_not_emit_update_progressbar_if_whole_part_not_changed(self):
        self.proc._progressbar_value = 10.5
        spy = QtTest.QSignalSpy(self.proc.update_progressbar)
        self.proc._update_progressbar(10.7)

        self.assertEqual(len(spy), 0)


class TestClassThumbnailProcessing(TestCase):

    def setUp(self):
        self.mock_image = mock.Mock(spec=core.Image)
        self.mock_image.thumb = None
        self.size = 200

        self.proc = workers.ThumbnailProcessing(self.mock_image, self.size)


class TestClassThumbnailProcessingMethodInit(TestClassThumbnailProcessing):

    def test_init_values(self):
        self.assertIs(self.proc._image, self.mock_image)
        self.assertEqual(self.proc._size, self.size)
        self.assertIsNone(self.proc._widget)


class TestClassThumbnailProcessingMethodRun(TestClassThumbnailProcessing):

    def test_image_thumbnail_called_with_size_arg_if_widget_None(self):
        self.mock_image.thumbnail.return_value = QtGui.QImage()
        self.proc.run()

        self.mock_image.thumbnail.assert_called_once_with(self.size)

    def test_logging_if_image_thumbnail_raise_OSError_and_widget_None(self):
        self.mock_image.thumbnail.side_effect = OSError
        with self.assertLogs('main.workers', 'ERROR'):
            self.proc.run()

    def test_empty_QImage_assigned_to_thumb_if_OSError_and_widget_None(self):
        self.mock_image.thumbnail.side_effect = OSError
        self.proc.run()

        self.assertEqual(self.proc._image.thumb, QtGui.QImage())

    def test_signal_finished_emitted_if_widget_None(self):
        spy = QtTest.QSignalSpy(self.proc.finished)
        self.proc.run()

        self.assertEqual(len(spy), 1)

    def test_thumbnail_called_with_size_arg_if_widg_not_None_and_visible(self):
        widget = mock.Mock(spec=thumbnailwidget.ThumbnailWidget)
        widget.isVisible.return_value = True
        self.proc._widget = widget
        self.mock_image.thumbnail.return_value = QtGui.QImage()
        self.proc.run()

        self.mock_image.thumbnail.assert_called_once_with(self.size)

    def test_logging_if_OSError_and_widget_not_None_and_visible(self):
        widget = mock.Mock(spec=thumbnailwidget.ThumbnailWidget)
        widget.isVisible.return_value = True
        self.proc._widget = widget
        self.mock_image.thumbnail.side_effect = OSError
        with self.assertLogs('main.workers', 'ERROR'):
            self.proc.run()

    def test_empty_QImage_set_to_thumb_if_OSError_widg_not_None_and_vis(self):
        widget = mock.Mock(spec=thumbnailwidget.ThumbnailWidget)
        widget.isVisible.return_value = True
        self.proc._widget = widget
        self.mock_image.thumbnail.side_effect = OSError
        self.proc.run()

        self.assertEqual(self.proc._image.thumb, QtGui.QImage())

    def test_signal_finished_emitted_if_widget_not_None_and_visible(self):
        widget = mock.Mock(spec=thumbnailwidget.ThumbnailWidget)
        widget.isVisible.return_value = True
        self.proc._widget = widget
        spy = QtTest.QSignalSpy(self.proc.finished)
        self.proc.run()

        self.assertEqual(len(spy), 1)

    def test_thumbnail_not_called_with_size_arg_if_widg_not_None_not_vis(self):
        widget = mock.Mock(spec=thumbnailwidget.ThumbnailWidget)
        widget.isVisible.return_value = False
        self.proc._widget = widget
        self.mock_image.thumbnail.return_value = QtGui.QImage()
        self.proc.run()

        self.mock_image.thumbnail.assert_not_called()

    def test_empty_QImage_not_to_thumb_if_OSError_widg_not_None_not_vis(self):
        widget = mock.Mock(spec=thumbnailwidget.ThumbnailWidget)
        widget.isVisible.return_value = False
        self.proc._widget = widget
        self.mock_image.thumbnail.side_effect = OSError
        self.proc.run()

        self.assertIsNone(self.proc._image.thumb)

    def test_signal_finished_not_emitted_if_widget_not_None_and_not_vis(self):
        widget = mock.Mock(spec=thumbnailwidget.ThumbnailWidget)
        widget.isVisible.return_value = False
        self.proc._widget = widget
        spy = QtTest.QSignalSpy(self.proc.finished)
        self.proc.run()

        self.assertEqual(len(spy), 0)
