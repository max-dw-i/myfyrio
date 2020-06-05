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

from PyQt5 import QtCore, QtWidgets

from doppelganger.gui import infolabel

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


IL_MODULE = 'doppelganger.gui.infolabel.'


# pylint: disable=unused-argument,missing-class-docstring


class TestInfoLabel(TestCase):

    def setUp(self):
        self.text = 'text'
        self.width = 200
        self.w = infolabel.InfoLabel(self.text, self.width)


class TestInfoLabelMethodInit(TestInfoLabel):

    def test_init_values(self):
        self.assertEqual(self.w.widget_width, self.width)

    def test_alignment_is_AlignHCenter(self):
        self.assertEqual(self.w.alignment(), QtCore.Qt.AlignHCenter)

    def test_text_is_set(self):
        self.assertEqual(self.w.text(), self.text)


class TestInfoLabelMethodSetText(TestInfoLabel):

    def test_wordWrap_called(self):
        with mock.patch(IL_MODULE+'InfoLabel._wordWrap') as mock_wrap_call:
            with mock.patch('PyQt5.QtWidgets.QLabel.setText'):
                self.w.setText(self.text)

        mock_wrap_call.assert_called_once_with(self.text)

    def test_parent_setText_called(self):
        wrapped = 'wrapped\ntext'
        with mock.patch(IL_MODULE+'InfoLabel._wordWrap', return_value=wrapped):
            with mock.patch('PyQt5.QtWidgets.QLabel.setText') as mock_set_call:
                self.w.setText(self.text)

        mock_set_call.assert_called_once_with(wrapped)

    def test_updateGeometry_called(self):
        PATCH_QLabel = 'PyQt5.QtWidgets.QLabel.'
        with mock.patch(PATCH_QLabel+'setText'):
            with mock.patch(PATCH_QLabel+'updateGeometry') as mock_upd_call:
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

    @mock.patch(IL_MODULE+'InfoLabel.__init__')
    def test_parent_init_called_with_image_size__widget_width(self, mock_init):
        infolabel.ImageSizeLabel(100, 200, 222, 'MB', 55)

        mock_init.assert_called_once_with('100x200, 222 MB', 55, None)

class ImagePathLabel(TestCase):

    @mock.patch(IL_MODULE+'InfoLabel.__init__')
    def test_parent_init_called_with_image_path__widget_width(self, mock_init):
        mock_qfile = mock.Mock(spec=QtCore.QFileInfo)
        mock_qfile.canonicalFilePath.return_value = 'canonical_path'
        with mock.patch('PyQt5.QtCore.QFileInfo',
                        return_value=mock_qfile) as mock_qfile_call:
            infolabel.ImagePathLabel('path', 200)

        mock_qfile_call.assert_called_once_with('path')
        mock_qfile.canonicalFilePath.assert_called_once_with()
        mock_init.assert_called_once_with('canonical_path', 200, None)
