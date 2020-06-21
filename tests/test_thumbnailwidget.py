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

from PyQt5 import QtCore, QtGui, QtWidgets

from doppelganger import core, workers
from doppelganger.gui import thumbnailwidget
from doppelganger.resources import Image

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


VIEW = 'doppelganger.gui.thumbnailwidget.'


# pylint: disable=unused-argument,missing-class-docstring


class TestThumbnailWidget(TestCase):

    ThW = VIEW + 'ThumbnailWidget.'

    def setUp(self):
        self.mock_image = mock.Mock(spec=core.Image)
        self.mock_image.thumb = None
        self.mock_image.path = 'path'
        self.size = 333
        self.lazy = True

        with mock.patch(self.ThW+'_setEmptyPixmap'):
            with mock.patch(self.ThW+'_setSize'):
                self.w = thumbnailwidget.ThumbnailWidget(self.mock_image,
                                                         self.size, self.lazy)


class TestThumbnailWidgetMethodInit(TestThumbnailWidget):

    def test_init_values(self):
        self.assertEqual(self.w.KEEP_TIME_MSEC, 10000)

        self.assertEqual(self.w._image, self.mock_image)
        self.assertEqual(self.w._size, self.size)
        self.assertEqual(self.w._lazy, self.lazy)
        self.assertTrue(self.w.empty, True)

    def test_size_policy(self):
        size_policy = self.w.sizePolicy()
        self.assertEqual(size_policy.horizontalPolicy(),
                         QtWidgets.QSizePolicy.Fixed)
        self.assertEqual(size_policy.verticalPolicy(),
                         QtWidgets.QSizePolicy.Fixed)

    def test_frame_style(self):
        self.assertEqual(self.w.frameStyle(), QtWidgets.QFrame.Box)

    def test_setEmptyPixmap_called_and_set_to_attr_pixmap(self):
        mock_pixmap = mock.Mock(spec=QtGui.QPixmap)
        with mock.patch(self.ThW+'_setEmptyPixmap',
                        return_value=mock_pixmap) as mock_empty_call:
            with mock.patch(self.ThW+'_setSize'):
                w = thumbnailwidget.ThumbnailWidget(self.mock_image,
                                                    self.size, self.lazy)

        mock_empty_call.assert_called_once_with()
        self.assertEqual(w._pixmap, mock_pixmap)

    def test_setSize_called(self):
        with mock.patch(self.ThW+'_setSize') as mock_size_call:
            thumbnailwidget.ThumbnailWidget(self.mock_image, self.size,
                                            True)

        mock_size_call.assert_called_once_with()

    def test_QTimer_made_if_lazy(self):
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            with mock.patch(self.ThW+'_setSize'):
                w = thumbnailwidget.ThumbnailWidget(self.mock_image,
                                                    self.size, True)

        self.assertIsInstance(w._qtimer, QtCore.QTimer)

    def test_makeThumbnail_called_if_not_lazy(self):
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            with mock.patch(self.ThW+'_makeThumbnail') as mock_make_call:
                with mock.patch(self.ThW+'_setThumbnail'):
                    thumbnailwidget.ThumbnailWidget(self.mock_image, self.size,
                                                    False)

        mock_make_call.assert_called_once_with()

    def test_setThumbnail_called_if_not_lazy(self):
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            with mock.patch(self.ThW+'_makeThumbnail'):
                with mock.patch(self.ThW+'_setThumbnail') as mock_set_call:
                    thumbnailwidget.ThumbnailWidget(self.mock_image, self.size,
                                                    False)

        mock_set_call.assert_called_once_with()


class TestThumbnailWidgetMethodSetSize(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.width, self.height = 1905, 1917
        self.mock_image.scaling_dimensions.return_value = (self.width,
                                                           self.height)

    def test_scaling_dimensions_called_with_attr_size(self):
        self.w._setSize()

        self.mock_image.scaling_dimensions.assert_called_once_with(self.size)

    def test_fixed_width_set(self):
        self.w._setSize()

        self.assertEqual(self.w.minimumWidth(), self.width)
        self.assertEqual(self.w.maximumWidth(), self.width)

    def test_fixed_height_set(self):
        self.w._setSize()

        self.assertEqual(self.w.minimumHeight(), self.height)
        self.assertEqual(self.w.maximumHeight(), self.height)

    def test_updateGeometry_called(self):
        with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
            self.w._setEmptyPixmap()

        mock_upd_call.assert_called_once_with()


class TestThumbnailWidgetMethodSetEmptyPixmap(TestThumbnailWidget):

    def test_null_QPixmap_made(self):
        with mock.patch('PyQt5.QtGui.QPixmap') as mock_QPixmap_call:
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setEmptyPixmap()

        mock_QPixmap_call.assert_called_once_with()

    def test_pixmap_returned(self):
        mock_pixmap = mock.Mock(spec=QtGui.QPixmap)
        with mock.patch('PyQt5.QtGui.QPixmap', return_value=mock_pixmap):
            with mock.patch(self.ThW+'setPixmap'):
                res = self.w._setEmptyPixmap()

        self.assertEqual(res, mock_pixmap)

    def test_setPixmap_called_with_QPixmap_result(self):
        mock_pixmap = mock.Mock(spec=QtGui.QPixmap)
        with mock.patch('PyQt5.QtGui.QPixmap', return_value=mock_pixmap):
            with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
                self.w._setEmptyPixmap()

        mock_setPixmap_call.assert_called_once_with(mock_pixmap)

    def test_updateGeometry_called(self):
        with mock.patch('PyQt5.QtGui.QPixmap'):
            with mock.patch(self.ThW+'setPixmap'):
                with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                    self.w._setEmptyPixmap()

        mock_upd_call.assert_called_once_with()

    def test_attr_empty_set_to_True(self):
        self.w.empty = False
        with mock.patch('PyQt5.QtGui.QPixmap'):
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setEmptyPixmap()

        self.assertTrue(self.w.empty)


class TestThumbnailWidgetMethodSetThumbnail(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.mock_pixmap = mock.Mock(spec=QtGui.QPixmap)
        self.w._pixmap = self.mock_pixmap

    def test_convertFromImage_called_with_image_thumb_arg_if_not_lazy(self):
        self.w._lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'setPixmap'):
            self.w._setThumbnail()

        self.mock_pixmap.convertFromImage.assert_called_once_with(
            self.w._image.thumb
        )

    def test_setPixmap_called_with_image_from_attr_thumb_if_not_lazy(self):
        self.w._lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
            self.w._setThumbnail()

        mock_setPixmap_call.assert_called_once_with(self.mock_pixmap)

    def test_errorThumbnail_called_if_image_thumb_cant_be_read__not_lazy(self):
        self.w._lazy = False
        self.mock_pixmap.convertFromImage.return_value = False
        with mock.patch(self.ThW+'setPixmap'):
            with mock.patch(self.ThW+'_errorThumbnail') as mock_err_call:
                self.w._setThumbnail()

        mock_err_call.assert_called_once_with()

    def test_setPixmap_called__error_img_if_thumb_cant_be_read__not_lazy(self):
        self.w._lazy = False
        self.mock_pixmap.convertFromImage.return_value = False
        with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
            with mock.patch(self.ThW+'_errorThumbnail',
                            return_value='error_image'):
                self.w._setThumbnail()

        mock_setPixmap_call.assert_called_once_with('error_image')

    def test_updateGeometry_called_if_not_lazy(self):
        self.w._lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'setPixmap'):
            with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                self.w._setThumbnail()

        mock_upd_call.assert_called_once_with()

    def test_empty_attr_set_to_False_if_not_lazy(self):
        self.w._lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        self.w.empty = True
        with mock.patch(self.ThW+'setPixmap'):
            self.w._setThumbnail()

        self.assertFalse(self.w.empty)

    def test_qtimer_start_not_called_if_not_lazy(self):
        self.w._lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        qtimer = mock.Mock(spec=QtCore.QTimer)
        self.w._qtimer = qtimer
        with mock.patch(self.ThW+'setPixmap'):
            self.w._setThumbnail()

        qtimer.start.assert_not_called()

    def test_convertFromImage_called_with_img_thumb_if_lazy_and_visible(self):
        self.w._lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setThumbnail()

        self.mock_pixmap.convertFromImage.assert_called_once_with(
            self.w._image.thumb
        )

    def test_setPixmap_called_with_img_read_from_thumb_if_lazy_and_vis(self):
        self.w._lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
                self.w._setThumbnail()

        mock_setPixmap_call.assert_called_once_with(self.mock_pixmap)

    def test_errorThumbnail_called_if_img_cant_be_read_if_lazy_and_vis(self):
        self.w._lazy = True
        self.mock_pixmap.convertFromImage.return_value = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                with mock.patch(self.ThW+'_errorThumbnail') as mock_err_call:
                    self.w._setThumbnail()

        mock_err_call.assert_called_once_with()

    def test_setPixmap_called__err_img_if_thumb_cant_be_read__lazy__vis(self):
        self.w._lazy = True
        self.mock_pixmap.convertFromImage.return_value = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
                with mock.patch(self.ThW+'_errorThumbnail',
                                return_value='error_image'):
                    self.w._setThumbnail()

        mock_setPixmap_call.assert_called_once_with('error_image')

    def test_updateGeometry_called_if_lazy_and_visible(self):
        self.w._lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                    self.w._setThumbnail()

        mock_upd_call.assert_called_once_with()

    def test_empty_attr_set_to_False_if_lazy_and_visible(self):
        self.w._lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        self.w.empty = True
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setThumbnail()

        self.assertFalse(self.w.empty)

    def test_qtimer_start_called_if_lazy_and_visible(self):
        self.w._lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        qtimer = mock.Mock(spec=QtCore.QTimer)
        self.w._qtimer = qtimer
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setThumbnail()

        qtimer.start.assert_called_once_with(10000)

    def test_convertFromImage_not_called_if_lazy_and_not_visible(self):
        self.w._lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            self.w._setThumbnail()

        self.mock_pixmap.convertFromImage.assert_not_called()

    def test_setPixmap_not_called_if_lazy_and_not_visible(self):
        self.w._lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
                self.w._setThumbnail()

        mock_setPixmap_call.assert_not_called()

    def test_errorThumbnail_not_called_if_lazy_and_not_visible(self):
        self.w._lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'_errorThumbnail') as mock_err_call:
                self.w._setThumbnail()

        mock_err_call.assert_not_called()

    def test_updateGeometry_not_called_if_lazy_and_not_visible(self):
        self.w._lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                self.w._setThumbnail()

        mock_upd_call.assert_not_called()

    def test_empty_attr_stay_True_if_lazy_and_not_visible(self):
        self.w._lazy = True
        self.w.empty = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            self.w._setThumbnail()

        self.assertTrue(self.w.empty)

    def test_qtimer_start_not_called_if_lazy_and_not_visible(self):
        self.w._lazy = True
        qtimer = mock.Mock(spec=QtCore.QTimer)
        self.w._qtimer = qtimer
        with mock.patch(self.ThW+'isVisible', return_value=False):
            self.w._setThumbnail()

        qtimer.start.assert_not_called()

    def test_assign_None_to_image_attr_thumb_if_lazy_and_not_visible(self):
        self.w._lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            self.w._setThumbnail()

        self.assertIsNone(self.w._image.thumb)


class TestThumbnailWidgetMethodErrorThumbnail(TestThumbnailWidget):

    def test_logging(self):
        with self.assertLogs('main.thumbnailwidget', 'ERROR'):
            self.w._errorThumbnail()

    def test_QPixmap_called_with_error_image_path(self):
        with mock.patch('PyQt5.QtGui.QPixmap') as mock_pixmap_call:
            self.w._errorThumbnail()

        mock_pixmap_call.assert_called_once_with(Image.ERR_IMG.abs_path) # pylint: disable=no-member

    def test_return_scaled_image_with_size_from_attr_size(self):
        mock_pixmap = mock.Mock(spec=QtGui.QPixmap)
        mock_pixmap.scaled.return_value = 'scaled_img'
        with mock.patch('PyQt5.QtGui.QPixmap', return_value=mock_pixmap):
            res = self.w._errorThumbnail()

        mock_pixmap.scaled.assert_called_once_with(self.w._size, self.w._size)
        self.assertEqual(res, 'scaled_img')


class TestThumbnailWidgetMethodMakeThumbnail(TestThumbnailWidget):

    PROC = 'doppelganger.workers.'

    def test_args_ThumbnailProcessing_called_with_if_lazy(self):
        self.w._lazy = True
        with mock.patch(self.PROC+'ThumbnailProcessing') as mock_proc_call:
            with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance'):
                self.w._makeThumbnail()

        mock_proc_call.assert_called_once_with(self.w._image, self.w._size,
                                               self.w)

    def test_ThumbnailProcessing_finished_connected_to_setThumbnail_if_l(self):
        mock_proc = mock.Mock(spec=workers.ThumbnailProcessing)
        with mock.patch(self.PROC+'ThumbnailProcessing',
                        return_value=mock_proc):
            with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance'):
                self.w._makeThumbnail()

        mock_proc.finished.connect.assert_called_once_with(
            self.w._setThumbnail
        )

    def test_worker_created_if_lazy(self):
        mock_processing_obj = mock.Mock(spec=workers.ThumbnailProcessing)
        with mock.patch(self.PROC+'ThumbnailProcessing',
                        return_value=mock_processing_obj):
            with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance'):
                with mock.patch(self.PROC+'Worker') as mock_worker_call:
                    self.w._makeThumbnail()

        mock_worker_call.assert_called_once_with(mock_processing_obj.run)

    def test_worker_pushed_to_thread_if_lazy(self):
        mock_threadpool = mock.Mock(spec=QtCore.QThreadPool)
        mock_worker = mock.Mock(spec=workers.Worker)
        with mock.patch(self.PROC+'ThumbnailProcessing'):
            with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance',
                            return_value=mock_threadpool):
                with mock.patch(self.PROC+'Worker', return_value=mock_worker):
                    self.w._makeThumbnail()

        mock_threadpool.start.assert_called_once_with(mock_worker)

    def test_ThumbnailProcessing_called_with_image_and_size_if_not_lazy(self):
        self.w._lazy = False
        with mock.patch(self.PROC+'ThumbnailProcessing') as mock_proc_call:
            self.w._makeThumbnail()

        mock_proc_call.assert_called_once_with(self.w._image, self.w._size)

    def test_ThumbnailProcessing_run_called_if_not_lazy(self):
        self.w._lazy = False
        mock_th_proc = mock.Mock(spec=workers.ThumbnailProcessing)
        with mock.patch(self.PROC+'ThumbnailProcessing',
                        return_value=mock_th_proc):
            self.w._makeThumbnail()

        mock_th_proc.run.assert_called_once_with()


class TestThumbnailWidgetMethodPaintEvent(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.mock_event = mock.Mock(spec=QtCore.QEvent)
        self.w._qtimer = mock.Mock(spec=QtCore.QTimer)

    def test_render_called_if_lazy_and_empty(self):
        self.w._lazy, self.w.empty = True, True
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent'):
            with mock.patch(self.ThW+'_makeThumbnail') as mock_make_call:
                self.w.paintEvent(self.mock_event)

        mock_make_call.assert_called_once_with()

    def test_QLabel_paintEvent_called_if_lazy_and_empty(self):
        self.w._lazy, self.w.empty = True, True
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent') as mock_ev_call:
            with mock.patch(self.ThW+'_makeThumbnail'):
                self.w.paintEvent(self.mock_event)

        mock_ev_call.assert_called_once_with(self.mock_event)

    def test_render_not_called_if_lazy_and_not_empty(self):
        self.w._lazy, self.w.empty = True, False
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent'):
            with mock.patch(self.ThW+'_makeThumbnail') as mock_make_call:
                self.w.paintEvent(self.mock_event)

        mock_make_call.assert_not_called()

    def test_QLabel_paintEvent_called_if_lazy_and_not_empty(self):
        self.w._lazy, self.w.empty = True, False
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent') as mock_ev_call:
            with mock.patch(self.ThW+'_makeThumbnail'):
                self.w.paintEvent(self.mock_event)

        mock_ev_call.assert_called_once_with(self.mock_event)

    def test_render_not_called_if_not_lazy(self):
        self.w._lazy = False
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent'):
            with mock.patch(self.ThW+'_makeThumbnail') as mock_make_call:
                self.w.paintEvent(self.mock_event)

        mock_make_call.assert_not_called()

    def test_QLabel_paintEvent_called_if_not_lazy(self):
        self.w._lazy = False
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent') as mock_ev_call:
            with mock.patch(self.ThW+'_makeThumbnail'):
                self.w.paintEvent(self.mock_event)

        mock_ev_call.assert_called_once_with(self.mock_event)


class TestThumbnailWidgetMethodClear(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.w._qtimer = mock.Mock(spec=QtCore.QTimer)

    def test_qtimer_stop_not_called_if_empty(self):
        self.w.empty = True
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            self.w._clear()

        self.w._qtimer.stop.assert_not_called()

    def test_setEmptyPixmap_not_called_if_empty(self):
        self.w.empty = True
        with mock.patch(self.ThW+'_setEmptyPixmap') as mock_set_call:
            self.w._clear()

        mock_set_call.assert_not_called()

    def test_attr_image_thumb_is_not_None_if_empty(self):
        self.w.empty = True
        self.w._image.thumb = 'thumb'
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            self.w._clear()

        self.assertIsNotNone(self.w._image.thumb)

    def test_attr_empty_stay_True_if_empty(self):
        self.w.empty = True
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            self.w._clear()

        self.assertTrue(self.w.empty)

    def test_qtimer_stop_not_called_if_not_empty_and_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.w._qtimer.stop.assert_not_called()

    def test_setEmptyPixmap_not_called_if_not_empty_and_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'_setEmptyPixmap') as mock_set_call:
                self.w._clear()

        mock_set_call.assert_not_called()

    def test_attr_image_thumb_is_not_None_if_not_empty_and_visible(self):
        self.w.empty = False
        self.w._image.thumb = 'thumb'
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.assertIsNotNone(self.w._image.thumb)

    def test_attr_empty_stay_False_if_not_empty_and_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.assertFalse(self.w.empty)

    def test_setEmptyPixmap_called_if_not_empty_and_not_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'_setEmptyPixmap') as mock_set_call:
                self.w._clear()

        mock_set_call.assert_called_once_with()

    def test_attr_image_thumb_set_to_None_if_not_empty_and_not_visible(self):
        self.w.empty = False
        self.w._image.thumb = 'thumb'
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.assertIsNone(self.w._image.thumb)

    def test_attr_empty_set_to_True_if_not_empty_and_not_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.assertTrue(self.w.empty)


class TestThumbnailWidgetMethodMark(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.w._pixmap = mock.Mock(spec=QtGui.QPixmap)
        self.copy = mock.Mock(spec=QtGui.QPixmap)

    @mock.patch('PyQt5.QtGui.QBrush')
    @mock.patch('PyQt5.QtGui.QPainter')
    def test_setPixmap_called_with_darker_thumbnail(self, mock_paint, mock_br):
        self.w._pixmap.copy.return_value = self.copy
        with mock.patch(self.ThW+'setPixmap') as mock_pixmap_call:
            self.w._mark()

        mock_pixmap_call.assert_called_once_with(self.copy)


class TestThumbnailWidgetMethodSetMarked(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.w._pixmap = mock.Mock(spec=QtGui.QPixmap)

    def test_mark_called_if_pass_True(self):
        with mock.patch(self.ThW+'_mark') as mock_mark_call:
            self.w.setMarked(True)

        mock_mark_call.assert_called_once_with()

    def test_setPixmap_with_pixmap_attr_called_if_pass_False(self):
        with mock.patch(self.ThW+'setPixmap') as mock_pixmap_call:
            self.w.setMarked(False)

        mock_pixmap_call.assert_called_once_with(self.w._pixmap)
