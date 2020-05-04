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

from doppelganger import signals
from doppelganger.core import SizeFormat
from doppelganger.gui import imageviewwidget

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


VIEW = 'doppelganger.gui.imageviewwidget.'


# pylint: disable=unused-argument,missing-class-docstring


class TestInfoLabel(TestCase):

    def setUp(self):
        self.text = 'text'
        self.width = 200
        self.w = imageviewwidget.InfoLabel(self.text, self.width)


class TestInfoLabelMethodInit(TestInfoLabel):

    def test_init_values(self):
        self.assertEqual(self.w.widget_width, self.width)

    def test_alignment(self):
        self.assertEqual(self.w.alignment(), QtCore.Qt.AlignHCenter)

    def test_text_is_set(self):
        self.assertEqual(self.w.text(), self.text)


class TestInfoLabelMethodSetText(TestInfoLabel):

    def test_wordWrap_called(self):
        with mock.patch(VIEW+'InfoLabel._wordWrap') as mock_wrap_call:
            with mock.patch('PyQt5.QtWidgets.QLabel.setText'):
                self.w.setText(self.text)

        mock_wrap_call.assert_called_once_with(self.text)

    def test_parent_setText_called(self):
        wrapped = 'wrapped\ntext'
        with mock.patch(VIEW+'InfoLabel._wordWrap', return_value=wrapped):
            with mock.patch('PyQt5.QtWidgets.QLabel.setText') as mock_set_call:
                self.w.setText(self.text)

        mock_set_call.assert_called_once_with(wrapped)

    def test_updateGeometry_called(self):
        QLabel = 'PyQt5.QtWidgets.QLabel.'
        with mock.patch(QLabel+'setText'):
            with mock.patch(QLabel+'updateGeometry') as mock_upd_call:
                self.w.setText(self.text)

        mock_upd_call.assert_called_once_with()


class TestInfoLabelMethodWordWrap(TestInfoLabel):

    @mock.patch('PyQt5.QtCore.QSize.width', return_value=200)
    def test_word_wrap_more_than_one_line(self, mock_width):
        res = self.w._wordWrap('test')

        self.assertEqual(res, '\nt\ne\ns\nt')

    @mock.patch('PyQt5.QtCore.QSize.width', return_value=200 - 10)
    def test_word_wrap_one_line(self, mock_width):
        res = self.w._wordWrap('test')

        self.assertEqual(res, 'test')


class ImageSizeLabel(TestCase):

    @mock.patch(VIEW+'InfoLabel.__init__')
    def test_init(self, mock_init):
        w, h = 100, 200
        file_size = 222
        size_format = SizeFormat.MB
        widget_width = 55
        imageviewwidget.ImageSizeLabel(w, h, file_size, size_format,
                                       widget_width)

        mock_init.assert_called_once_with('100x200, 222 MB', 55, None)

class ImagePathLabel(TestCase):

    @mock.patch(VIEW+'InfoLabel.__init__')
    def test_init(self, mock_init):
        path = 'path'
        mock_qfile = mock.Mock()
        with mock.patch('PyQt5.QtCore.QFileInfo',
                        return_value=mock_qfile) as mock_q_file_call:
            imageviewwidget.ImagePathLabel(path, 200)

        mock_q_file_call.assert_called_once_with(path)
        mock_qfile.canonicalFilePath.assert_called_once_with()


class TestThumbnailWidget(TestCase):

    ThW = VIEW + 'ThumbnailWidget.'

    def setUp(self):
        self.mock_thumbnail = mock.Mock()
        self.size = 333

        with mock.patch(self.ThW+'_QByteArrayToQPixmap'):
            with mock.patch(self.ThW+'setPixmap'):
                self.w =imageviewwidget.ThumbnailWidget(self.mock_thumbnail,
                                                        self.size)


class TestThumbnailWidgetMethodInit(TestThumbnailWidget):

    def test_init_values(self):
        self.assertEqual(self.w.thumbnail, self.mock_thumbnail)
        self.assertEqual(self.w.size, self.size)

    def test_alignment(self):
        self.assertEqual(self.w.alignment(), QtCore.Qt.AlignHCenter)

    def test_setPixmap_called_with_QByteArrayToQPixmap_result(self):
        QBAImage = 'QBAImage'
        with mock.patch(self.ThW+'_QByteArrayToQPixmap',
                        return_value=QBAImage):
            with mock.patch(self.ThW+'setPixmap') as mock_pix_call:
                imageviewwidget.ThumbnailWidget(self.mock_thumbnail, self.size)

        mock_pix_call.assert_called_once_with(QBAImage)

    def test_updateGeometry_called(self):
        with mock.patch(self.ThW+'_QByteArrayToQPixmap'):
            with mock.patch(self.ThW+'setPixmap'):
                with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                    imageviewwidget.ThumbnailWidget(self.mock_thumbnail,
                                                    self.size)

        mock_upd_call.assert_called_once_with()


class TestThumbnailWidgetMethodQByteArrayToQPixmap(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.mock_qpixmap = mock.Mock()

    def test_return_scaled_error_img_if_thumbnail_is_None(self):
        self.w.thumbnail = None
        self.mock_qpixmap.scaled.return_value = 'error_img'
        err_img_path = 'absolute_path'
        with mock.patch('PyQt5.QtGui.QPixmap',
                        return_value=self.mock_qpixmap) as mock_qpixmap_call:
            with mock.patch('doppelganger.gui.imageviewwidget.resource',
                            return_value=err_img_path):
                res = self.w._QByteArrayToQPixmap()

        mock_qpixmap_call.assert_called_once_with(err_img_path)
        self.mock_qpixmap.scaled.assert_called_once_with(self.size, self.size)
        self.assertEqual(res, 'error_img')

    def test_return_qpixmap_thumbnail_if_isNull_is_False(self):
        self.mock_qpixmap.isNull.return_value = False
        with mock.patch('PyQt5.QtGui.QPixmap', return_value=self.mock_qpixmap):
            res = self.w._QByteArrayToQPixmap()

        self.mock_qpixmap.loadFromData.assert_called_once_with(
            self.mock_thumbnail
        )
        self.assertEqual(res, self.mock_qpixmap)

    def test_return_scaled_error_img_if_isNull_is_True(self):
        self.mock_qpixmap.isNull.return_value = True
        self.mock_qpixmap.scaled.return_value = 'error_img'
        err_img_path = 'absolute_path'
        with mock.patch('PyQt5.QtGui.QPixmap',
                        return_value=self.mock_qpixmap) as mock_qpixmap_call:
            with mock.patch('doppelganger.gui.imageviewwidget.resource',
                            return_value=err_img_path):
                res = self.w._QByteArrayToQPixmap()

        mock_qpixmap_call.assert_called_with(err_img_path)
        self.mock_qpixmap.scaled.assert_called_once_with(self.size, self.size)
        self.assertEqual(res, 'error_img')

    def test_log_error_if_isNull_is_True(self):
        self.mock_qpixmap.isNull.return_value = True
        with mock.patch('PyQt5.QtGui.QPixmap', return_value=self.mock_qpixmap):
            with self.assertLogs('main.widgets', 'ERROR'):
                self.w._QByteArrayToQPixmap()


class TestThumbnailWidgetMethodMark(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.w.pixmap = mock.Mock()
        self.copy = mock.Mock()

    @mock.patch('PyQt5.QtGui.QBrush')
    @mock.patch('PyQt5.QtGui.QPainter')
    def test_setPixmap_called_with_darker_thumbnail(self, mock_paint, mock_br):
        self.w.pixmap.copy.return_value = self.copy
        with mock.patch(VIEW+'ThumbnailWidget.setPixmap') as mock_pixmap_call:
            self.w.mark()

        mock_pixmap_call.assert_called_once_with(self.copy)


class TestThumbnailWidgetMethodUnmark(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.w.pixmap = mock.Mock()

    def test_setPixmap_with_pixmap_attr_called(self):
        with mock.patch(VIEW+'ThumbnailWidget.setPixmap') as mock_pixmap_call:
            self.w.unmark()

        mock_pixmap_call.assert_called_once_with(self.w.pixmap)


class TestDuplicateWidget(TestCase):

    DW = VIEW + 'DuplicateWidget.'

    def setUp(self):
        self.conf = {'size': 200,
                     'size_format': 1,
                     'show_similarity': False,
                     'show_size': False,
                     'show_path': False}
        self.mock_image = mock.Mock()

        with mock.patch(self.DW+'_setThumbnailWidget'):
            self.w = imageviewwidget.DuplicateWidget(self.mock_image, self.conf)


class TestDuplicateWidgetMethodInit(TestDuplicateWidget):

    def test_init_values(self):
        self.assertEqual(self.w.image, self.mock_image)
        self.assertEqual(self.w.conf, self.conf)
        self.assertFalse(self.w.selected)
        self.assertIsInstance(self.w.signals, signals.Signals)

        self.assertEqual(self.w.minimumWidth(), self.conf['size'])
        self.assertEqual(self.w.maximumWidth(), self.conf['size'])

    def test_layout(self):
        margins = self.w.layout.contentsMargins()
        self.assertEqual(margins.top(), 0)
        self.assertEqual(margins.right(), 0)
        self.assertEqual(margins.bottom(), 0)
        self.assertEqual(margins.left(), 0)

        self.assertIsInstance(self.w.layout, QtWidgets.QVBoxLayout)
        self.assertEqual(self.w.layout.alignment(), QtCore.Qt.AlignTop)

    def test_setThumbnailWidget_called(self):
        with mock.patch(self.DW+'_setThumbnailWidget') as mock_widget_call:
            self.w = imageviewwidget.DuplicateWidget(self.mock_image, self.conf)

        mock_widget_call.assert_called_once_with()

    def test_setSimilarityLabel_called_if_show_similarity_True(self):
        self.conf['show_similarity'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setSimilarityLabel') as mock_label_call:
                self.w = imageviewwidget.DuplicateWidget(self.mock_image,
                                                         self.conf)

        mock_label_call.assert_called_once_with()

    def test_setImageSizeLabel_called_if_show_size_True(self):
        self.conf['show_size'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setImageSizeLabel') as mock_label_call:
                self.w = imageviewwidget.DuplicateWidget(self.mock_image,
                                                         self.conf)

        mock_label_call.assert_called_once_with()

    def test_setImagePathLabel_called_if_show_path_True(self):
        self.conf['show_path'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setImagePathLabel') as mock_label_call:
                self.w = imageviewwidget.DuplicateWidget(self.mock_image,
                                                         self.conf)

        mock_label_call.assert_called_once_with()


class TestMethodSetThumbnailWidget(TestDuplicateWidget):

    ADD = 'PyQt5.QtWidgets.QVBoxLayout.addWidget'
    ThW = VIEW + 'ThumbnailWidget'

    def test_args_ThumbnailWidget_called_with(self):
        with mock.patch(self.ThW) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setThumbnailWidget()

        mock_widget_call.assert_called_once_with(self.mock_image.thumb,
                                                 self.conf['size'])

    def test_addWidget_called_with_ThumbnailWidget_result(self):
        ThW_obj = 'widget'
        with mock.patch(self.ThW, return_value=ThW_obj):
            with mock.patch(self.ADD) as mock_add_call:
                self.w._setThumbnailWidget()

        mock_add_call.assert_called_once_with(ThW_obj)

    def test_return_ThumbnailWidget_result(self):
        ThW_obj = 'widget'
        with mock.patch(self.ThW, return_value=ThW_obj):
            with mock.patch(self.ADD):
                res = self.w._setThumbnailWidget()

        self.assertEqual(res, ThW_obj)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.ThW):
            with mock.patch(self.ADD):
                with mock.patch(updateGem) as mock_upd_call:
                    self.w._setThumbnailWidget()

        mock_upd_call.assert_called_once_with()


class TestMethodSetSimilarityLabel(TestDuplicateWidget):

    ADD = 'PyQt5.QtWidgets.QVBoxLayout.addWidget'
    SL = VIEW + 'SimilarityLabel'

    def test_args_SimilarityLabel_called_with(self):
        self.mock_image.similarity.return_value = 13
        with mock.patch(self.SL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setSimilarityLabel()

        mock_widget_call.assert_called_once_with('13%', self.conf['size'])

    def test_addWidget_called_with_SimilarityLabel_result(self):
        SL_obj = 'label'
        with mock.patch(self.SL, return_value=SL_obj):
            with mock.patch(self.ADD) as mock_add_call:
                self.w._setSimilarityLabel()

        mock_add_call.assert_called_once_with(SL_obj)

    def test_return_SimilarityLabel_result(self):
        SL_obj = 'label'
        with mock.patch(self.SL, return_value=SL_obj):
            with mock.patch(self.ADD):
                res = self.w._setSimilarityLabel()

        self.assertEqual(res, SL_obj)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.SL):
            with mock.patch(self.ADD):
                with mock.patch(updateGem) as mock_upd_call:
                    self.w._setSimilarityLabel()

        mock_upd_call.assert_called_once_with()


class TestMethodSetImageSizeLabel(TestDuplicateWidget):

    ADD = 'PyQt5.QtWidgets.QVBoxLayout.addWidget'
    ISL = VIEW + 'ImageSizeLabel'

    def setUp(self):
        super().setUp()

        self.conf['size_format'] = 0 # Bytes

        type(self.mock_image).width = mock.PropertyMock(return_value=33)
        type(self.mock_image).height = mock.PropertyMock(return_value=55)

    def test_args_ImageSizeLabel_called_with(self):
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        mock_widget_call.assert_called_once_with(33, 55, 5000,
                                                 SizeFormat.B, 200)

    def test_filesize_called_with_SizeFormat_B(self):
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        self.mock_image.filesize.assert_called_once_with(SizeFormat.B)

    def test_args_ImageSizeLabel_called_with_if_width_raise_OSError(self):
        type(self.mock_image).width = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        mock_widget_call.assert_called_once_with(0, 0, 5000,
                                                 SizeFormat.B, 200)

    def test_logging_if_width_raise_OSError(self):
        type(self.mock_image).width = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                with self.assertLogs('main', 'ERROR'):
                    self.w._setImageSizeLabel()

    def test_args_ImageSizeLabel_called_with_if_height_raise_OSError(self):
        type(self.mock_image).height = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        mock_widget_call.assert_called_once_with(0, 0, 5000,
                                                 SizeFormat.B, 200)

    def test_logging_if_height_raise_OSError(self):
        type(self.mock_image).height = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                with self.assertLogs('main', 'ERROR'):
                    self.w._setImageSizeLabel()

    def test_args_ImageSizeLabel_called_with_if_filesize_raise_OSError(self):
        self.mock_image.filesize.side_effect = OSError
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        mock_widget_call.assert_called_once_with(33, 55, 0,
                                                 SizeFormat.B, 200)

    def test_logging_if_filesize_raise_OSError(self):
        self.mock_image.filesize.side_effect = OSError
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                with self.assertLogs('main', 'ERROR'):
                    self.w._setImageSizeLabel()

    def test_addWidget_called_with_ImageSizeLabel_result(self):
        ISL_obj = 'label'
        with mock.patch(self.ISL, return_value=ISL_obj):
            with mock.patch(self.ADD) as mock_add_call:
                self.w._setImageSizeLabel()

        mock_add_call.assert_called_once_with(ISL_obj)

    def test_return_ImageSizeLabel_result(self):
        ISL_obj = 'label'
        with mock.patch(self.ISL, return_value=ISL_obj):
            with mock.patch(self.ADD):
                res = self.w._setImageSizeLabel()

        self.assertEqual(res, ISL_obj)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                with mock.patch(updateGem) as mock_upd_call:
                    self.w._setImageSizeLabel()

        mock_upd_call.assert_called_once_with()


class TestMethodSetImagePathLabel(TestDuplicateWidget):

    ADD = 'PyQt5.QtWidgets.QVBoxLayout.addWidget'
    IPL = VIEW + 'ImagePathLabel'

    def test_args_ImagePathLabel_called_with(self):
        self.mock_image.similarity.return_value = 13
        with mock.patch(self.IPL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImagePathLabel()

        mock_widget_call.assert_called_once_with(self.mock_image.path,
                                                 self.conf['size'])

    def test_addWidget_called_with_ImagePathLabel_result(self):
        IPL_obj = 'label'
        with mock.patch(self.IPL, return_value=IPL_obj):
            with mock.patch(self.ADD) as mock_add_call:
                self.w._setImagePathLabel()

        mock_add_call.assert_called_once_with(IPL_obj)

    def test_return_ImagePathLabel_result(self):
        IPL_obj = 'label'
        with mock.patch(self.IPL, return_value=IPL_obj):
            with mock.patch(self.ADD):
                res = self.w._setImagePathLabel()

        self.assertEqual(res, IPL_obj)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.IPL):
            with mock.patch(self.ADD):
                with mock.patch(updateGem) as mock_upd_call:
                    self.w._setImagePathLabel()

        mock_upd_call.assert_called_once_with()


class TestDuplicateWidgetMethodOpenImage(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.mock_msg_box = mock.Mock()

    @mock.patch('sys.platform')
    def test_subprocess_run_called(self, mock_platform):
        with mock.patch('subprocess.run') as mock_run:
            self.w.openImage()

        mock_run.assert_called_once_with(['Unknown platform',
                                          self.mock_image.path],
                                         check=True)

    @mock.patch('sys.platform')
    def test_log_error_if_run_raise_exception(self, mock_platform):
        with mock.patch('subprocess.run', side_effect=FileNotFoundError):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=self.mock_msg_box):
                with self.assertLogs('main.widgets', 'ERROR'):
                    self.w.openImage()

    @mock.patch('sys.platform')
    def test_show_msg_box_if_run_raise_exception(self, mock_platform):
        with mock.patch('subprocess.run', side_effect=FileNotFoundError):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=self.mock_msg_box):
                self.w.openImage()

        self.mock_msg_box.exec.assert_called_once_with()


class TestDuplicateWidgetMethodRenameImage(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.INPUT = 'PyQt5.QtWidgets.QInputDialog.getText'
        self.mock_image.path = 'path'
        self.w.infoLabel = mock.Mock()

    def test_nothing_happens_if_QInputDialog_not_return_ok(self):
        with mock.patch(self.INPUT, return_value=('new_name', False)):
            self.w.renameImage()

        self.mock_image.rename.assert_not_called()

    def test_image_rename_called_with_new_name_arg(self):
        with mock.patch(self.INPUT, return_value=('new_name', True)):
            self.w.renameImage()

        self.mock_image.rename.assert_called_once_with('new_name')

    def test_ImagePathLabel_text_changed_if_image_name_is_changed(self):
        with mock.patch(self.INPUT, return_value=('new_name', True)):
            self.w.renameImage()

        label = self.w.infoLabel.imagePathLabel
        label.setText.assert_called_once_with(self.mock_image.path)

    def test_log_error_if_image_rename_raise_FileExistsError(self):
        self.mock_image.rename.side_effect = FileExistsError
        mock_msg_box = mock.Mock()
        with mock.patch(self.INPUT, return_value=('new_name', True)):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=mock_msg_box):
                with self.assertLogs('main.widgets', 'ERROR'):
                    self.w.renameImage()

    def test_show_msg_box_if_image_rename_raise_FileExistsError(self):
        self.mock_image.rename.side_effect = FileExistsError
        mock_msg_box = mock.Mock()
        with mock.patch(self.INPUT, return_value=('new_name', True)):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=mock_msg_box):
                self.w.renameImage()

        mock_msg_box.exec.assert_called_once_with()


class TestDuplicateWidgetMethodContextMenuEvent(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.mock_menu = mock.Mock()
        self.mock_event = mock.Mock()

    @mock.patch(VIEW+'DuplicateWidget.mapToGlobal')
    @mock.patch(VIEW+'DuplicateWidget.openImage')
    def test_openImage_called(self, mock_open, mock_map):
        openAction = 'open'
        self.mock_menu.addAction.side_effect = ['open', 'Rename']
        self.mock_menu.exec_.return_value = openAction
        with mock.patch('PyQt5.QtWidgets.QMenu', return_value=self.mock_menu):
            self.w.contextMenuEvent(self.mock_event)

        mock_open.assert_called_once_with()

    @mock.patch(VIEW+'DuplicateWidget.mapToGlobal')
    @mock.patch(VIEW+'DuplicateWidget.renameImage')
    def test_renameImage_called(self, mock_rename, mock_map):
        openAction = 'Rename'
        self.mock_menu.addAction.side_effect = ['open', 'Rename']
        self.mock_menu.exec_.return_value = openAction
        with mock.patch('PyQt5.QtWidgets.QMenu', return_value=self.mock_menu):
            self.w.contextMenuEvent(self.mock_event)

        mock_rename.assert_called_once_with()


class TestDuplicateWidgetMethodClick(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.imageLabel = mock.Mock()
        self.w.imageLabel = self.imageLabel

    def test_unselect_widget_if_selected(self):
        self.w.selected = True
        self.w.click()

        self.assertFalse(self.w.selected)

    def test_imageLabel_unmark_called_if_selected(self):
        self.w.selected = True
        self.w.click()

        self.imageLabel.unmark.assert_called_once_with()

    def test_select_widget_if_unselected(self):
        self.w.selected = False
        self.w.click()

        self.assertTrue(self.w.selected)

    def test_imageLabel_mark_called_if_unselected(self):
        self.w.selected = False
        self.w.click()

        self.imageLabel.mark.assert_called_once_with()

    def test_emit_signal_clicked(self):
        spy = QtTest.QSignalSpy(self.w.signals.clicked)
        self.w.click()

        self.assertEqual(len(spy), 1)


class TestDuplicateWidgetMethodMouseReleaseEvent(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.mock_event = mock.Mock()

    @mock.patch(VIEW+'DuplicateWidget.click')
    def test_click_called(self, mock_click):
        self.w.mouseReleaseEvent(self.mock_event)

        mock_click.assert_called_once_with()


class TestDuplicateWidgetMethodDelete(TestDuplicateWidget):

    def test_image_delete_called(self):
        self.w.delete()

        self.mock_image.delete.assert_called_once_with()

    def test_unselect_widget_if_image_delete_is_ok(self):
        self.w.delete()

        self.assertFalse(self.w.selected)

    @mock.patch(VIEW+'DuplicateWidget.hide')
    def test_widget_hide_called_if_image_delete_is_ok(self, mock_hide):
        self.w.delete()

        mock_hide.assert_called_once_with()

    def test_raise_OSError_if_image_delete_raise_OSError(self):
        self.mock_image.delete.side_effect = OSError
        with self.assertRaises(OSError):
            self.w.delete()


class TestDuplicateWidgetMethodMove(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.dst = 'new_folder'

    def test_image_move_called(self):
        self.w.move(self.dst)

        self.mock_image.move.assert_called_once_with(self.dst)

    def test_unselect_widget_if_image_move_is_ok(self):
        self.w.move(self.dst)

        self.assertFalse(self.w.selected)

    @mock.patch(VIEW+'DuplicateWidget.hide')
    def test_widget_hide_called_if_image_move_is_ok(self, mock_hide):
        self.w.move(self.dst)

        mock_hide.assert_called_once_with()

    def test_raise_OSError_if_image_move_raise_OSError(self):
        self.mock_image.move.side_effect = OSError
        with self.assertRaises(OSError):
            self.w.move(self.dst)


class TestImageGroupWidget(TestCase):

    IGW = VIEW + 'ImageGroupWidget'

    def setUp(self):
        self.conf = {}
        self.mock_image = mock.Mock()
        self.image_group = [self.mock_image]
        with mock.patch(self.IGW+'._setDuplicateWidgets'):
            self.w = imageviewwidget.ImageGroupWidget(self.image_group,
                                                      self.conf)


class TestImageGroupWidgetMethodInit(TestImageGroupWidget):

    def test_initial_value(self):
        self.assertDictEqual(self.w.conf, self.conf)
        self.assertListEqual(self.w.widgets, [])
        self.assertListEqual(self.w.image_group, self.image_group)

    def test_widget_layout(self):
        self.assertEqual(self.w.layout.spacing(), 10)
        self.assertIsInstance(self.w.layout, QtWidgets.QHBoxLayout)
        self.assertEqual(self.w.layout.alignment(),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def test_setDuplicateWidgets_called(self):
        with mock.patch(self.IGW+'._setDuplicateWidgets') as mock_dupl_call:
            imageviewwidget.ImageGroupWidget(self.image_group, self.conf)

        mock_dupl_call.assert_called_once_with()


class TestImageGroupWidgetMethodSetDuplicateWidgets(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.mock_dupl_w = mock.Mock()

    @mock.patch('PyQt5.QtWidgets.QHBoxLayout.addWidget')
    def test_args_DuplicateWidget_called_with(self, mock_add):
        with mock.patch(VIEW+'DuplicateWidget',
                        return_value=self.mock_dupl_w) as mock_widg_call:
            self.w._setDuplicateWidgets()

        mock_widg_call.assert_called_once_with(self.image_group[0],
                                               self.conf)

    @mock.patch('PyQt5.QtWidgets.QHBoxLayout.addWidget')
    def test_DuplicateWidget_added_to_widgets_attr(self, mock_add):
        with mock.patch(VIEW+'DuplicateWidget', return_value=self.mock_dupl_w):
            self.w._setDuplicateWidgets()

        self.assertListEqual(self.w.widgets, [self.mock_dupl_w])

    @mock.patch('PyQt5.QtWidgets.QHBoxLayout.addWidget')
    def test_DuplicateWidget_added_to_layout(self, mock_add):
        with mock.patch(VIEW+'DuplicateWidget', return_value=self.mock_dupl_w):
            self.w._setDuplicateWidgets()

        mock_add.assert_called_once_with(self.mock_dupl_w)

    @mock.patch('PyQt5.QtWidgets.QHBoxLayout.addWidget')
    def test_updateGeometry_called(self, mock_add):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(VIEW+'DuplicateWidget', return_value=self.mock_dupl_w):
            with mock.patch(updateGem) as mock_upd_call:
                self.w._setDuplicateWidgets()

        mock_upd_call.assert_called_once_with()


class TestImageGroupWidgetMethodSelectedWidgets(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.w.widgets = [mock.Mock()]

    def test_selected_widget_in_result_list(self):
        self.w.widgets[0].selected = True
        res = self.w.selectedWidgets()

        self.assertIn(self.w.widgets[0], res)
        self.assertEqual(len(res), 1)

    def test_not_selected_widgets_not_in_result_list(self):
        self.w.widgets[0].selected = False
        res = self.w.selectedWidgets()

        self.assertNotIn(self.w.widgets[0], res)
        self.assertEqual(len(res), 0)


class TestImageGroupWidgetMethodvisibleWidgets(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.w.widgets = [mock.Mock()]

    def test_isVisible_called(self):
        self.w.visibleWidgets()

        self.w.widgets[0].isVisible.assert_called_once_with()


class TestImageGroupWidgetMethodHasSelectedWidgets(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.mock_dupl_w = mock.Mock()
        self.w.widgets = [self.mock_dupl_w]

    def test_return_True_if_hasSelectedWidgets_return_True(self):
        self.mock_dupl_w.selected = True
        res = self.w.hasSelectedWidgets()

        self.assertTrue(res)

    def test_return_False_if_hasSelectedWidgets_not_return_True(self):
        self.mock_dupl_w.selected = False
        res = self.w.hasSelectedWidgets()

        self.assertFalse(res)


class TestImageGroupWidgetMethodAutoSelect(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.w.widgets = [mock.Mock(), mock.Mock()]

    def test_click_called_if_widget_is_not_selected(self):
        self.w.widgets[1].selected = False
        self.w.autoSelect()

        self.w.widgets[1].click.assert_called_once_with()

    def test_click_not_called_if_widget_selected(self):
        self.w.widgets[1].selected = True
        self.w.autoSelect()

        self.w.widgets[1].click.assert_not_called()


class TestImageViewWidget(TestCase):

    def setUp(self):
        self.conf = {'delete_dirs': False}
        self.w = imageviewwidget.ImageViewWidget(self.conf)


class TestImageViewWidgetMethodInit(TestImageViewWidget):

    def test_conf_attr_initial_value(self):
        self.assertDictEqual(self.w.conf, self.conf)

    def test_widgets_attr_initial_value(self):
        self.assertListEqual(self.w.widgets, [])

    def test_widget_layout(self):
        margins = self.w.contentsMargins()

        self.assertIsInstance(self.w.layout, QtWidgets.QVBoxLayout)
        self.assertEqual(margins.left(), 0)
        self.assertEqual(margins.top(), 0)
        self.assertEqual(margins.right(), 0)
        self.assertEqual(margins.bottom(), 0)
        self.assertEqual(self.w.layout.spacing(), 0)
        self.assertEqual(self.w.layout.alignment(),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)


class TestImageViewWidgetMethodRender(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.image_group = ['image']
        self.mock_group_w = mock.Mock()

    @mock.patch('PyQt5.QtWidgets.QVBoxLayout.addWidget')
    def test_args_ImageGroupWidget_called_with(self, mock_add):
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w) as mock_widg:
            self.w.render(self.image_group)

        mock_widg.assert_called_once_with(self.image_group, self.conf)

    @mock.patch('PyQt5.QtWidgets.QVBoxLayout.addWidget')
    def test_ImageGroupWidget_added_to_widgets_attr(self, mock_add):
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w):
            self.w.render(self.image_group)

        self.assertListEqual(self.w.widgets, [self.mock_group_w])

    @mock.patch('PyQt5.QtWidgets.QVBoxLayout.addWidget')
    def test_ImageGroupWidget_added_to_layout(self, mock_add):
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w):
            self.w.render(self.image_group)

        mock_add.assert_called_once_with(self.mock_group_w)

    @mock.patch('PyQt5.QtWidgets.QVBoxLayout.addWidget')
    def test_updateGeometry_called(self, mock_add):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w):
            with mock.patch(updateGem) as mock_upd_call:
                self.w.render(self.image_group)

        mock_upd_call.assert_called_once_with()


class TestImageViewWidgetMethodHasSelectedWidgets(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_group_w = mock.Mock()
        self.w.widgets = [self.mock_group_w]

    def test_return_True_if_hasSelectedWidgets_return_True(self):
        self.mock_group_w.hasSelectedWidgets.return_value = True
        res = self.w.hasSelectedWidgets()

        self.assertTrue(res)

    def test_return_False_if_hasSelectedWidgets_not_return_True(self):
        self.mock_group_w.hasSelectedWidgets.return_value = False
        res = self.w.hasSelectedWidgets()

        self.assertFalse(res)


class TestImageViewWidgetMethodClear(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_group_w = mock.Mock()
        self.w.widgets = [self.mock_group_w]

    def test_deleteLater_called(self):
        self.w.clear()

        self.mock_group_w.deleteLater.assert_called_once_with()

    def test_clear_widgets_attr(self):
        self.w.clear()

        self.assertListEqual(self.w.widgets, [])


class TestImageViewWidgetMethodDelete(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.CALL_ON = VIEW + 'ImageViewWidget._callOnSelectedWidgets'
        self.mock_msg_box = mock.Mock()

    def test_args_callOnSelectedWidgets_called_with(self):
        with mock.patch(self.CALL_ON) as mock_on:
            self.w.delete()

        mock_on.assert_called_once_with(imageviewwidget.DuplicateWidget.delete)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_log_error_if_callOnSelectedWidgets_raise_OSError(self, mock_box):
        with mock.patch(self.CALL_ON, side_effect=OSError):
            with self.assertLogs('main.widgets', 'ERROR'):
                self.w.delete()

    def test_show_msgbox_if_callOnSelectedWidgets_raise_OSError(self):
        with mock.patch(self.CALL_ON, side_effect=OSError):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=self.mock_msg_box):
                self.w.delete()

        self.mock_msg_box.exec.assert_called_once_with()


class TestImageViewWidgetMethodMove(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.dst = 'new_folder'

        self.CALL_ON = VIEW + 'ImageViewWidget._callOnSelectedWidgets'
        self.mock_msg_box = mock.Mock()

    def test_args_callOnSelectedWidgets_called_with(self):
        with mock.patch(self.CALL_ON) as mock_on:
            self.w.move(self.dst)

        mock_on.assert_called_once_with(imageviewwidget.DuplicateWidget.move,
                                        self.dst)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_log_error_if_callOnSelectedWidgets_raise_OSError(self, mock_box):
        with mock.patch(self.CALL_ON, side_effect=OSError):
            with self.assertLogs('main.widgets', 'ERROR'):
                self.w.move(self.dst)

    def test_show_msgbox_if_callOnSelectedWidgets_raise_OSError(self):
        with mock.patch(self.CALL_ON, side_effect=OSError):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=self.mock_msg_box):
                self.w.move(self.dst)

        self.mock_msg_box.exec.assert_called_once_with()


class TestImageViewWidgetMethodCallOnSelectedWidgets(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_func = mock.Mock()

        self.mock_group_w = mock.MagicMock()
        self.mock_group_w.__len__.return_value = 10
        self.mock_selected_w = mock.Mock()
        self.mock_group_w.selectedWidgets.return_value = [self.mock_selected_w]
        self.w.widgets.append(self.mock_group_w)

    def test_args_func_called_with(self):
        self.w._callOnSelectedWidgets(self.mock_func, 'arg', karg='karg')

        self.mock_func.assert_called_once_with(self.mock_selected_w,
                                               'arg', karg='karg')

    def test_raise_OSError_if_func_raise_OSError(self):
        self.mock_func.side_effect = OSError
        with self.assertRaises(OSError):
            self.w._callOnSelectedWidgets(self.mock_func)

    def test_call_del_parent_dir_if_conf_param_delete_dirs_is_True(self):
        self.conf['delete_dirs'] = True
        self.w._callOnSelectedWidgets(self.mock_func)

        self.mock_selected_w.image.del_parent_dir.assert_called_once_with()

    def test_hide_group_widget_if_less_than_2_visible(self):
        self.mock_group_w.visibleWidgets.return_value = ['widget']
        self.w._callOnSelectedWidgets(self.mock_func)

        self.mock_group_w.hide.assert_called_once_with()

    def test_not_hide_group_widget_if_more_than_2_visible(self):
        self.mock_group_w.visibleWidgets.return_value = ['widget1', 'widget2']
        self.w._callOnSelectedWidgets(self.mock_func)

        self.mock_group_w.hide.assert_not_called()


class TestImageViewWidgetMethodAutoSelect(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_img_grp = mock.Mock()
        self.w.widgets.append(self.mock_img_grp)

    def test_ImageGroupWidget_autoSelect_called(self):
        self.w.autoSelect()

        self.mock_img_grp.autoSelect.assert_called_once_with()


class TestImageViewWidgetMethodUnselect(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_img_grp = mock.Mock()
        self.mock_selected_w = mock.Mock()
        self.mock_img_grp.selectedWidgets.return_value = [self.mock_selected_w]
        self.w.widgets.append(self.mock_img_grp)

    def test_DuplicateWidget_click_called(self):
        self.w.unselect()

        self.mock_selected_w.click.assert_called_once_with()
