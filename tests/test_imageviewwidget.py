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
import subprocess
import sys
from unittest import TestCase, mock

from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

from doppelganger import core, imageviewwidget

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


# pylint: disable=unused-argument,missing-class-docstring,protected-access


class TestInfoLabelWidget(TestCase):

    def setUp(self):
        self.w = imageviewwidget.InfoLabelWidget('test', 200)

    @mock.patch('doppelganger.imageviewwidget.InfoLabelWidget._word_wrap', return_value='test_wrapped')
    def test_init(self, mock_wrap):
        w = imageviewwidget.InfoLabelWidget('test', 200)

        self.assertEqual(w.text(), 'test_wrapped')
        self.assertEqual(w.alignment(), QtCore.Qt.AlignHCenter)
        self.assertEqual(w.widget_size, 200)

    @mock.patch('doppelganger.imageviewwidget.InfoLabelWidget._word_wrap', return_value='text')
    def test_setText(self, mock_wrap):
        new_text = 'text'
        self.w.setText(new_text)

        self.assertEqual(new_text, self.w.text())
        mock_wrap.assert_called_once()

    @mock.patch('PyQt5.QtCore.QSize.width', return_value=200)
    def test_word_wrap_more_than_one_line(self, mock_width):
        res = self.w._word_wrap('test')

        self.assertEqual(res, '\nt\ne\ns\nt')

    @mock.patch('PyQt5.QtCore.QSize.width', return_value=200 - 40 - 1)
    def test_word_wrap_one_line(self, mock_width):
        res = self.w._word_wrap('test')

        self.assertEqual(res, 'test')

class TestSimilarityLabel(TestInfoLabelWidget):
    '''The same test as for TestInfoLabelWidget'''


class ImageSizeLabel(TestInfoLabelWidget):
    '''The same test as for TestInfoLabelWidget'''


class ImagePathLabel(TestCase):

    @mock.patch('doppelganger.imageviewwidget.QtCore.QFileInfo.canonicalFilePath', return_value='test_path')
    @mock.patch('doppelganger.imageviewwidget.InfoLabelWidget.__init__')
    def test_init(self, mock_init, mock_path):
        imageviewwidget.ImagePathLabel('test', 200)

        mock_init.assert_called_once_with('test_path', 200, None)


class TestImageInfoWidget(TestCase):

    @mock.patch('doppelganger.imageviewwidget.QtCore.QFileInfo.canonicalFilePath', return_value='path')
    def test_init(self, mock_path):
        CONF = {
            'size': 200,
            'show_similarity': True,
            'show_size': True,
            'show_path': True,
            'sort': 0,
            'delete_dirs': False,
            'size_format': 1,
            'subfolders': True,
            'close_confirmation': False,
        }
        path, difference, dimensions, filesize = 'path', 0, (1, 2), 3
        w = imageviewwidget.ImageInfoWidget(path, difference, dimensions, filesize, CONF)

        similarity_label = w.findChild(imageviewwidget.SimilarityLabel)
        image_size_label = w.findChild(imageviewwidget.ImageSizeLabel)
        image_path_label = w.findChild(imageviewwidget.ImagePathLabel)

        self.assertEqual(w.layout().alignment(), QtCore.Qt.AlignBottom)
        self.assertEqual(similarity_label.text(), f'{difference}%')
        self.assertEqual(image_size_label.text(), '1x2, 3 KB')
        self.assertEqual(image_path_label.text(), path)

    @mock.patch('doppelganger.imageviewwidget.QtCore.QFileInfo.canonicalFilePath', return_value='path')
    def test_init_with_widgets_turned_off(self, mock_path):
        CONF = {
            'size': 200,
            'show_similarity': False,
            'show_size': False,
            'show_path': False,
            'sort': 0,
            'cache_thumbnails': False,
            'delete_dirs': False,
            'size_format': 'B'
        }
        path, difference, dimensions, filesize = 'path', 0, (1, 2), 3
        w = imageviewwidget.ImageInfoWidget(path, difference, dimensions, filesize, CONF)

        similarity_label = w.findChild(imageviewwidget.SimilarityLabel)
        image_size_label = w.findChild(imageviewwidget.ImageSizeLabel)
        image_path_label = w.findChild(imageviewwidget.ImagePathLabel)

        self.assertIsNone(similarity_label)
        self.assertIsNone(image_size_label)
        self.assertIsNone(image_path_label)

    def test_get_image_size(self):
        result = imageviewwidget.ImageInfoWidget._get_image_size((1, 2), 3, 1)
        expected = '1x2, 3 KB'

        self.assertEqual(result, expected)


class TestThumbnailWidget(TestCase):

    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap', return_value='pix')
    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget.setPixmap')
    def test_init(self, mock_set, mock_pixmap):
        th = 'thumbnail'
        w = imageviewwidget.ThumbnailWidget(th, 666)

        self.assertEqual(w.alignment(), QtCore.Qt.AlignHCenter)
        mock_pixmap.assert_called_once_with(th, 666)
        mock_set.assert_called_once_with('pix')
        self.assertTrue(mock_set.called)

    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap')
    def test_QByteArray_to_QPixmap_returns_error_image_if_thumbnail_is_None(self, mock_qp):
        imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap(None, 666)

        mock_qp.assert_called_once_with(imageviewwidget.IMG_ERROR)

    def test_QByteArray_to_QPixmap_returns_QPixmap_obj_if_thumbnail_is_None(self):
        qp = imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap(None, 666)

        self.assertIsInstance(qp, QtGui.QPixmap)

    def test_QByteArray_to_QPixmap_returns_error_image_with_SIZEs(self):
        qp = imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap(None, 666)

        self.assertEqual(666, qp.height())
        self.assertEqual(666, qp.width())

    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap')
    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap.isNull', return_value=True)
    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_error_image_if_isNull(
            self, mock_load, mock_null, mock_qp
        ):
        imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail', 666)

        mock_qp.assert_called_with(imageviewwidget.IMG_ERROR)

    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap.isNull', return_value=True)
    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_QPixmap_obj_if_isNull(self, mock_load, mock_null):
        qp = imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail', 666)

        self.assertIsInstance(qp, QtGui.QPixmap)

    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap.isNull', return_value=True)
    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_logs_errors_if_isNull(self, mock_load, mock_null):
        with self.assertLogs('main.widgets', 'ERROR'):
            imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail', 666)

    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap.isNull', return_value=False)
    @mock.patch('doppelganger.imageviewwidget.QtGui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_QPixmap_obj(self, mock_load, mock_null):
        qp = imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail', 666)

        self.assertIsInstance(qp, QtGui.QPixmap)

    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap')
    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget.setPixmap')
    def test_unmark(self, mock_set, mock_qp):
        w = imageviewwidget.ThumbnailWidget('thumbnail', 666)
        w.unmark()

        mock_set.assert_called_with(w.pixmap)

    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget._QByteArray_to_QPixmap')
    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget.setPixmap')
    def test_mark(self, mock_set, mock_qp):
        w = imageviewwidget.ThumbnailWidget('thumbnail', 666)
        w.unmark()

        self.assertTrue(mock_qp.called)


class TestDuplicateWidget(TestCase):

    def setUp(self):
        self.CONF = {
            'size': 200,
            'show_similarity': True,
            'show_size': True,
            'show_path': True,
            'sort': 0,
            'delete_dirs': False,
            'size_format': 1,
            'subfolders': True,
            'close_confirmation': False,
        }
        self.path, self.difference = 'image.png', 1
        self.image = core.Image(self.path, difference=self.difference)
        self.w = imageviewwidget.DuplicateWidget(self.image, self.CONF)

    def test_init(self):
        self.assertEqual(self.w.width(), 200)
        self.assertIsInstance(self.w.layout(), QtWidgets.QVBoxLayout)
        self.assertEqual(self.w.layout().alignment(), QtCore.Qt.AlignTop)
        self.assertEqual(self.w.image, self.image)
        self.assertFalse(self.w.selected)
        self.assertEqual(self.w.conf, self.CONF)

    def test_ThumbnailWidget_n_ImageInfoWidget_in_DuplicateWidget(self):
        th_widgets = self.w.findChildren(
            imageviewwidget.ThumbnailWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        info_widgets = self.w.findChildren(
            imageviewwidget.ImageInfoWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        self.assertEqual(len(th_widgets), 1)
        self.assertEqual(len(info_widgets), 1)

    @mock.patch('doppelganger.core.Image.filesize', return_value=3)
    @mock.patch('doppelganger.core.Image.dimensions', side_effect=OSError)
    @mock.patch('doppelganger.imageviewwidget.ImageInfoWidget')
    def test_widgets_if_get_dimensions_raises_OSError(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, (0, 0), 3,
                                          self.CONF, self.w)

    @mock.patch('doppelganger.core.Image.filesize', return_value=3)
    @mock.patch('doppelganger.core.Image.dimensions', side_effect=OSError)
    @mock.patch('doppelganger.imageviewwidget.ImageInfoWidget')
    def test_widgets_logs_if_get_dimensions_raises_OSError(self, mock_info, mock_dim, mock_size):
        with self.assertLogs('main.widgets', 'ERROR'):
            self.w._widgets()

    @mock.patch('doppelganger.core.Image.filesize', side_effect=OSError)
    @mock.patch('doppelganger.core.Image.dimensions', return_value=2)
    @mock.patch('doppelganger.imageviewwidget.ImageInfoWidget')
    def test_widgets_if_get_filesize_raises_OSError(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, 2, 0,
                                          self.CONF, self.w)

    @mock.patch('doppelganger.core.Image.filesize', side_effect=OSError)
    @mock.patch('doppelganger.core.Image.dimensions', return_value=2)
    @mock.patch('doppelganger.imageviewwidget.ImageInfoWidget')
    def test_widgets_logs_if_get_filesize_raises_OSError(self, mock_info, mock_dim, mock_size):
        with self.assertLogs('main.widgets', 'ERROR'):
            self.w._widgets()

    @mock.patch('doppelganger.core.Image.filesize', return_value=3)
    @mock.patch('doppelganger.core.Image.dimensions', return_value=2)
    @mock.patch('doppelganger.imageviewwidget.ImageInfoWidget')
    def test_widgets_ImageInfoWidget_called_with_what_args(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, 2, 3,
                                          self.CONF, self.w)

    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget')
    def test_widgets_calls_ThumbnailWidget(self, mock_th):
        self.w._widgets()

        self.assertTrue(mock_th.called)

    @mock.patch('doppelganger.imageviewwidget.subprocess.run')
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

        with mock.patch('doppelganger.imageviewwidget.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')

            with self.assertLogs('main.widgets', 'ERROR'):
                self.w._open_image()

    @mock.patch('doppelganger.imageviewwidget.ImagePathLabel.setText')
    @mock.patch('doppelganger.core.Image.rename')
    @mock.patch('PyQt5.QtWidgets.QInputDialog.getText', return_value=('test', True))
    def test_rename_image(self, mock_get, mock_rename, mock_set):
        mw = QtWidgets.QMainWindow()
        mw.setCentralWidget(self.w)

        self.w._rename_image()

        mock_rename.assert_called_once_with('test')
        mock_set.assert_called_once_with(self.image.path)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.core.Image.rename', side_effect=FileExistsError)
    @mock.patch('PyQt5.QtWidgets.QInputDialog.getText', return_value=('test', True))
    def test_rename_image_if_raise_FileExistsError(self, mock_get, mock_rename, mock_exec):
        mw = QtWidgets.QMainWindow()
        mw.setCentralWidget(self.w)

        with self.assertLogs('main.widgets', 'ERROR'):
            self.w._rename_image()

        mock_exec.assert_called_once()

    def test_contextMenuEvent(self):
        pass

    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget.unmark')
    def test_click_on_selected_widget(self, mock_unmark):
        self.w.selected = True
        spy = QtTest.QSignalSpy(self.w.signals.clicked)
        self.w.click()

        self.assertFalse(self.w.selected)
        self.assertTrue(mock_unmark.called)
        self.assertEqual(len(spy), 1)

    @mock.patch('doppelganger.imageviewwidget.ThumbnailWidget.mark')
    def test_click_on_unselected_widget(self, mock_mark):
        self.w.selected = False
        spy = QtTest.QSignalSpy(self.w.signals.clicked)
        self.w.click()

        self.assertTrue(self.w.selected)
        self.assertTrue(mock_mark.called)
        self.assertEqual(len(spy), 1)

    @mock.patch('doppelganger.imageviewwidget.DuplicateWidget.click')
    def test_mouseReleaseEvent(self, mock_click):
        mw = QtWidgets.QMainWindow()
        mw.setCentralWidget(self.w)
        QtTest.QTest.mouseClick(self.w, QtCore.Qt.LeftButton)

        self.assertTrue(mock_click.called)

    @mock.patch('PyQt5.QtCore.QObject.deleteLater')
    @mock.patch('doppelganger.core.Image.delete')
    def test_delete(self, mock_img, mock_later):
        self.w.delete()

        self.assertTrue(mock_img.called)
        self.assertFalse(self.w.selected)
        self.assertTrue(mock_later.called)

    @mock.patch('doppelganger.core.Image.delete', side_effect=OSError)
    def test_delete_raises_OSError(self, mock_img):
        with self.assertRaises(OSError):
            self.w.delete()

    @mock.patch('PyQt5.QtCore.QObject.deleteLater')
    @mock.patch('doppelganger.core.Image.move')
    def test_move(self, mock_img, mock_later):
        dst = 'new_dst'
        self.w.move(dst)

        mock_img.assert_called_once_with(dst)
        self.assertFalse(self.w.selected)
        self.assertTrue(mock_later.called)

    @mock.patch('doppelganger.core.Image.move', side_effect=OSError)
    def test_move_raises_OSError(self, mock_img):
        dst = 'new_dst'
        with self.assertRaises(OSError):
            self.w.move(dst)


class TestImageGroupWidget(TestCase):

    def setUp(self):
        self.CONF = {
            'size': 200,
            'show_similarity': True,
            'show_size': True,
            'show_path': True,
            'sort': 0,
            'delete_dirs': False,
            'size_format': 1,
            'subfolders': True,
            'close_confirmation': False,
        }
        self.w = imageviewwidget.ImageGroupWidget([core.Image('image.png')], self.CONF)

    def test_widget_alignment(self):
        l = self.w.layout()

        self.assertEqual(l.alignment(), QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def test_number_of_created_widgets(self):
        w = self.w.findChildren(
            imageviewwidget.DuplicateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        self.assertEqual(len(self.w), len(w))

    def test_getSelectedWidgets(self):
        ws = self.w.findChildren(
            imageviewwidget.DuplicateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        ws[0].selected = True

        self.assertListEqual(self.w.getSelectedWidgets(), ws)

    def test_auto_select(self):
        w = imageviewwidget.ImageGroupWidget(
            [core.Image('image1.png'), core.Image('image2.png')],
            self.CONF
        )
        w.auto_select()

        self.assertFalse(w.duplicate_widgets[0].selected)
        self.assertTrue(w.duplicate_widgets[1].selected)

    def test_len(self):
        self.assertEqual(len(self.w), 1)



class TestImageViewWidget(TestCase):

    def setUp(self):
        self.w = imageviewwidget.ImageViewWidget()
        self.conf = {
            'size': 200,
            'show_similarity': True,
            'show_size': True,
            'show_path': True,
            'sort': 0,
            'delete_dirs': False,
            'size_format': 1,
            'subfolders': True,
            'close_confirmation': False,
        }

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_render_empty_image_groups(self, mock_msgbox):
        self.w.render(self.conf, [])

        self.assertTrue(mock_msgbox.called)

    def test_render(self):
        image_groups = [[core.Image('image.jpg')]]
        self.w.render(self.conf, image_groups)
        rendered_widgets = self.w.findChildren(imageviewwidget.ImageGroupWidget)

        self.assertEqual(len(rendered_widgets), len(image_groups))
        self.assertIsInstance(rendered_widgets[0], imageviewwidget.ImageGroupWidget)

    def test_hasSelectedWidgets_False(self):
        self.w.layout.addWidget(
            imageviewwidget.ImageGroupWidget([core.Image('image.png')], self.conf)
        )
        w = self.w.findChild(imageviewwidget.DuplicateWidget)

        self.assertFalse(w.selected)

    def test_hasSelectedWidgets_True(self):
        self.w.layout.addWidget(
            imageviewwidget.ImageGroupWidget([core.Image('image.png')], self.conf)
        )
        w = self.w.findChild(imageviewwidget.DuplicateWidget)
        w.selected = True

        self.assertTrue(w.selected)

    def test_clear(self):
        self.w.clear()
        group_widgets = self.w.findChildren(imageviewwidget.ImageGroupWidget)

        self.assertFalse(group_widgets)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.imageviewwidget.DuplicateWidget.delete', side_effect=OSError)
    def test_call_on_selected_widgets_delete_raises_OSError(self, mock_delete, mock_box):
        image_group = [core.Image('img1.png')]
        self.w.layout.addWidget(
            imageviewwidget.ImageGroupWidget(image_group, self.conf)
        )
        w = self.w.findChild(imageviewwidget.DuplicateWidget)
        w.selected = True
        with self.assertLogs('main.widgets', 'ERROR'):
            self.w.call_on_selected_widgets(self.conf)

        mock_delete.assert_called_once()
        self.assertTrue(mock_box.called)

    @mock.patch('doppelganger.core.Image.del_parent_dir')
    @mock.patch('doppelganger.imageviewwidget.DuplicateWidget.delete')
    def test_call_on_selected_widgets_delete_empty_dir(self, mock_delete, mock_dir):
        image_group = [core.Image('img1.png')]
        self.w.layout.addWidget(
            imageviewwidget.ImageGroupWidget(image_group, self.conf)
        )
        w = self.w.findChild(imageviewwidget.DuplicateWidget)
        w.selected = True
        self.conf['delete_dirs'] = True

        self.w.call_on_selected_widgets(self.conf)

        self.assertTrue(mock_dir.called)

    @mock.patch('doppelganger.core.Image.del_parent_dir')
    @mock.patch('doppelganger.imageviewwidget.DuplicateWidget.delete')
    def test_call_on_selected_widgets_not_delete_empty_dir(self, mock_delete, mock_dir):
        image_group = [core.Image('img1.png')]
        self.w.layout.addWidget(
            imageviewwidget.ImageGroupWidget(image_group, self.conf)
        )
        w = self.w.findChild(imageviewwidget.DuplicateWidget)
        w.selected = True
        self.conf['delete_dirs'] = False

        self.w.call_on_selected_widgets(self.conf)

        self.assertFalse(mock_dir.called)

    @mock.patch('doppelganger.imageviewwidget.ImageGroupWidget.deleteLater')
    def test_call_on_selected_widgets_deleteLater_on_ImageGroupWidget(self, mock_later):
        image_group = [core.Image('img1.png')]
        self.w.layout.addWidget(
            imageviewwidget.ImageGroupWidget(image_group, self.conf)
        )
        self.w.call_on_selected_widgets(self.conf)

        mock_later.assert_called_once()
