'''Copyright 2019 Maxim Shpak <maxim.shpak@posteo.uk>

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
import subprocess
import sys
from unittest import TestCase, mock

from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

from doppelganger import core, widgets

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


class TestInfoLabelWidget(TestCase):

    @mock.patch('doppelganger.widgets.InfoLabelWidget._word_wrap', return_value='test_wrapped')
    def test_init(self, mock_wrap):
        w = widgets.InfoLabelWidget('test')

        self.assertEqual(w.text(), 'test_wrapped')
        self.assertEqual(w.alignment(), QtCore.Qt.AlignHCenter)

    @mock.patch('PyQt5.QtCore.QSize.width', return_value=widgets.SIZE)
    def test_word_wrap_more_than_one_line(self, mock_width):
        w = widgets.InfoLabelWidget('test')
        res = w._word_wrap('test')

        self.assertEqual(res, '\nt\ne\ns\nt')

    @mock.patch('PyQt5.QtCore.QSize.width', return_value=widgets.SIZE - 40 - 1)
    def test_word_wrap_one_line(self, mock_width):
        w = widgets.InfoLabelWidget('test')
        res = w._word_wrap('test')

        self.assertEqual(res, 'test')

class TestSimilarityLabel(TestInfoLabelWidget):
    '''The same test as for TestInfoLabelWidget'''


class ImageSizeLabel(TestInfoLabelWidget):
    '''The same test as for TestInfoLabelWidget'''


class ImagePathLabel(TestCase):

    @mock.patch('doppelganger.widgets.QtCore.QFileInfo.canonicalFilePath', return_value='test_path')
    @mock.patch('doppelganger.widgets.InfoLabelWidget.__init__')
    def test_init(self, mock_init, mock_path):
        widgets.ImagePathLabel('test')

        mock_init.assert_called_once_with('test_path', None)


class TestImageInfoWidget(TestCase):

    @mock.patch('doppelganger.widgets.QtCore.QFileInfo.canonicalFilePath', return_value='path')
    def test_init(self, mock_path):
        path, difference, dimensions, filesize = 'path', 0, (1, 2), 3
        w = widgets.ImageInfoWidget(path, difference, dimensions, filesize)

        similarity_label = w.findChild(widgets.SimilarityLabel)
        image_size_label = w.findChild(widgets.ImageSizeLabel)
        image_path_label = w.findChild(widgets.ImagePathLabel)

        self.assertEqual(w.layout().alignment(), QtCore.Qt.AlignBottom)
        self.assertEqual(similarity_label.text(), str(difference))
        self.assertEqual(image_size_label.text(), '1x2, 3 KB')
        self.assertEqual(image_path_label.text(), path)

    def test_get_image_size(self):
        result = widgets.ImageInfoWidget._get_image_size((1, 2), 3)
        expected = '1x2, 3 KB'

        self.assertEqual(result, expected)


class TestThumbnailWidget(TestCase):

    @mock.patch('doppelganger.widgets.ThumbnailWidget._QByteArray_to_QPixmap', return_value='pix')
    @mock.patch('doppelganger.widgets.ThumbnailWidget.setPixmap')
    def test_init(self, mock_set, mock_pixmap):
        th = 'thumbnail'
        w = widgets.ThumbnailWidget(th)

        self.assertEqual(w.alignment(), QtCore.Qt.AlignHCenter)
        mock_pixmap.assert_called_once_with(th)
        mock_set.assert_called_once_with('pix')
        self.assertTrue(mock_set.called)

    @mock.patch('doppelganger.widgets.QtGui.QPixmap')
    def test_QByteArray_to_QPixmap_returns_error_image_if_thumbnail_is_None(self, mock_qp):
        widgets.ThumbnailWidget._QByteArray_to_QPixmap(None)

        mock_qp.assert_called_once_with(widgets.IMAGE_ERROR)

    def test_QByteArray_to_QPixmap_returns_QPixmap_obj_if_thumbnail_is_None(self):
        qp = widgets.ThumbnailWidget._QByteArray_to_QPixmap(None)

        self.assertIsInstance(qp, QtGui.QPixmap)

    def test_QByteArray_to_QPixmap_returns_error_image_with_SIZEs(self):
        qp = widgets.ThumbnailWidget._QByteArray_to_QPixmap(None)

        self.assertEqual(widgets.SIZE, qp.height())
        self.assertEqual(widgets.SIZE, qp.width())

    @mock.patch('doppelganger.widgets.QtGui.QPixmap')
    @mock.patch('doppelganger.widgets.QtGui.QPixmap.isNull', return_value=True)
    @mock.patch('doppelganger.widgets.QtGui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_error_image_if_isNull(
            self, mock_load, mock_null, mock_qp
        ):
        widgets.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail')

        mock_qp.assert_called_with(widgets.IMAGE_ERROR)

    @mock.patch('doppelganger.widgets.QtGui.QPixmap.isNull', return_value=True)
    @mock.patch('doppelganger.widgets.QtGui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_QPixmap_obj_if_isNull(self, mock_load, mock_null):
        qp = widgets.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail')

        self.assertIsInstance(qp, QtGui.QPixmap)

    @mock.patch('doppelganger.widgets.QtGui.QPixmap.isNull', return_value=True)
    @mock.patch('doppelganger.widgets.QtGui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_logs_errors_if_isNull(self, mock_load, mock_null):
        with self.assertLogs('main.widgets', 'ERROR'):
            widgets.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail')

    @mock.patch('doppelganger.widgets.QtGui.QPixmap.isNull', return_value=False)
    @mock.patch('doppelganger.widgets.QtGui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_QPixmap_obj(self, mock_load, mock_null):
        qp = widgets.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail')

        self.assertIsInstance(qp, QtGui.QPixmap)

    @mock.patch('doppelganger.widgets.ThumbnailWidget._QByteArray_to_QPixmap')
    @mock.patch('doppelganger.widgets.ThumbnailWidget.setPixmap')
    def test_unmark(self, mock_set, mock_qp):
        w = widgets.ThumbnailWidget('thumbnail')
        w.unmark()

        mock_set.assert_called_with(w.pixmap)

    @mock.patch('doppelganger.widgets.ThumbnailWidget._QByteArray_to_QPixmap')
    @mock.patch('doppelganger.widgets.ThumbnailWidget.setPixmap')
    def test_mark(self, mock_set, mock_qp):
        w = widgets.ThumbnailWidget('thumbnail')
        w.unmark()

        self.assertTrue(mock_qp.called)


class TestDuplicateWidget(TestCase):

    def setUp(self):
        self.path, self.difference = 'image.png', 1
        self.image = core.Image(self.path, difference=self.difference)
        self.w = widgets.DuplicateWidget(self.image)

    def test_init(self):
        self.assertEqual(self.w.width(), 200)
        self.assertIsInstance(self.w.layout(), QtWidgets.QVBoxLayout)
        self.assertEqual(self.w.layout().alignment(), QtCore.Qt.AlignTop)
        self.assertEqual(self.w.image, self.image)
        self.assertFalse(self.w.selected)

    def test_ThumbnailWidget_n_ImageInfoWidget_in_DuplicateWidget(self):
        th_widgets = self.w.findChildren(
            widgets.ThumbnailWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        info_widgets = self.w.findChildren(
            widgets.ImageInfoWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        self.assertEqual(len(th_widgets), 1)
        self.assertEqual(len(info_widgets), 1)

    @mock.patch('doppelganger.core.Image.filesize', return_value=3)
    @mock.patch('doppelganger.core.Image.dimensions', side_effect=OSError)
    @mock.patch('doppelganger.widgets.ImageInfoWidget')
    def test_widgets_if_get_dimensions_raises_OSError(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, (0, 0), 3, self.w)

    @mock.patch('doppelganger.core.Image.filesize', return_value=3)
    @mock.patch('doppelganger.core.Image.dimensions', side_effect=OSError)
    @mock.patch('doppelganger.widgets.ImageInfoWidget')
    def test_widgets_logs_if_get_dimensions_raises_OSError(self, mock_info, mock_dim, mock_size):
        with self.assertLogs('main.widgets', 'ERROR'):
            self.w._widgets()

    @mock.patch('doppelganger.core.Image.filesize', side_effect=OSError)
    @mock.patch('doppelganger.core.Image.dimensions', return_value=2)
    @mock.patch('doppelganger.widgets.ImageInfoWidget')
    def test_widgets_if_get_filesize_raises_OSError(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, 2, 0, self.w)

    @mock.patch('doppelganger.core.Image.filesize', side_effect=OSError)
    @mock.patch('doppelganger.core.Image.dimensions', return_value=2)
    @mock.patch('doppelganger.widgets.ImageInfoWidget')
    def test_widgets_logs_if_get_filesize_raises_OSError(self, mock_info, mock_dim, mock_size):
        with self.assertLogs('main.widgets', 'ERROR'):
            self.w._widgets()

    @mock.patch('doppelganger.core.Image.filesize', return_value=3)
    @mock.patch('doppelganger.core.Image.dimensions', return_value=2)
    @mock.patch('doppelganger.widgets.ImageInfoWidget')
    def test_widgets_ImageInfoWidget_called_with_what_args(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, 2, 3, self.w)

    @mock.patch('doppelganger.widgets.ThumbnailWidget')
    def test_widgets_calls_ThumbnailWidget(self, mock_th):
        self.w._widgets()

        self.assertTrue(mock_th.called)

    @mock.patch('doppelganger.widgets.subprocess.run')
    def test_open_image(self, mock_run):
        mw = QtWidgets.QMainWindow()
        mw.setCentralWidget(self.w)
        open_image_command = {'linux': 'xdg-open',
                              'win32': 'explorer',
                              'darwin': 'open'}[sys.platform]
        self.w._open_image()

        mock_run.assert_called_once_with(
            [open_image_command, self.w.image.path],
            check=True
        )

    def test_open_image_raise_CalledProcessError(self):
        mw = QtWidgets.QMainWindow()
        mw.setCentralWidget(self.w)

        with mock.patch('doppelganger.widgets.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')

            with self.assertLogs('main.widgets', 'ERROR'):
                        self.w._open_image()

    def test_contextMenuEvent(self):
        pass

    @mock.patch('doppelganger.widgets.ThumbnailWidget.unmark')
    def test_mouseReleaseEvent_on_selected_widget(self, mock_unmark):
        mw = QtWidgets.QMainWindow()
        mw.setCentralWidget(self.w)
        self.w.selected = True
        spy = QtTest.QSignalSpy(self.w.clicked)
        QtTest.QTest.mouseClick(self.w, QtCore.Qt.LeftButton)

        self.assertFalse(self.w.selected)
        self.assertTrue(mock_unmark.called)
        self.assertEqual(len(spy), 1)

    @mock.patch('doppelganger.widgets.ThumbnailWidget.mark')
    def test_mouseReleaseEvent_on_unselected_widget(self, mock_mark):
        mw = QtWidgets.QMainWindow()
        mw.setCentralWidget(self.w)
        self.w.selected = False
        spy = QtTest.QSignalSpy(self.w.clicked)
        QtTest.QTest.mouseClick(self.w, QtCore.Qt.LeftButton)

        self.assertTrue(self.w.selected)
        self.assertTrue(mock_mark.called)
        self.assertEqual(len(spy), 1)

    @mock.patch('PyQt5.QtCore.QObject.deleteLater')
    @mock.patch('doppelganger.core.Image.delete')
    def test_delete(self, mock_img, mock_later):
        self.w.delete()

        self.assertTrue(mock_img.called)
        self.assertFalse(self.w.selected)
        self.assertTrue(mock_later.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.core.Image.delete', side_effect=OSError)
    def test_delete_raises_OSError(self, mock_img, mock_box):
        with self.assertRaises(OSError):
            self.w.delete()

        self.assertTrue(mock_box.called)

    @mock.patch('PyQt5.QtCore.QObject.deleteLater')
    @mock.patch('doppelganger.core.Image.move')
    def test_move(self, mock_img, mock_later):
        dst = 'new_dst'
        self.w.move(dst)

        mock_img.assert_called_once_with(dst)
        self.assertFalse(self.w.selected)
        self.assertTrue(mock_later.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.core.Image.move', side_effect=OSError)
    def test_move_raises_OSError(self, mock_img, mock_box):
        dst = 'new_dst'
        with self.assertRaises(OSError):
            self.w.move(dst)

        self.assertTrue(mock_box.called)


class TestImageGroupWidget(TestCase):

    def setUp(self):
        self.w = widgets.ImageGroupWidget([core.Image('image.png')])

    def test_widget_alignment(self):
        l = self.w.layout()

        self.assertEqual(l.alignment(), QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def test_number_of_created_widgets(self):
        w = self.w.findChildren(
            widgets.DuplicateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        self.assertEqual(len(self.w), len(w))

    def test_getSelectedWidgets(self):
        ws = self.w.findChildren(
            widgets.DuplicateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        ws[0].selected = True

        self.assertListEqual(self.w.getSelectedWidgets(), ws)

    def test_len(self):
        self.w = widgets.ImageGroupWidget([core.Image('image.png')])

        self.assertEqual(len(self.w), 1)
