'''Copyright 2020 Maxim Shpak <maxim.shpak@posteo.uk>

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

from PyQt5 import QtCore, QtTest, QtWidgets

from doppelganger import preferenceswindow

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=unused-argument,missing-class-docstring,protected-access


class TestPreferencesForm(TestCase):

    class P(QtWidgets.QWidget):
        conf = {'delete_dirs': True,
                'show_path': True,
                'show_similarity': True,
                'show_size': True,
                'size_format': 'MB',
                'size': 666,
                'sort': 1,
                'subfolders': True,
                'close_confirmation': True}

    def setUp(self):
        self.p = self.P()
        self.form = preferenceswindow.PreferencesWindow(parent=self.p)

    def clear_form(self):
        self.form.sizeSpinBox.setValue(333)
        self.form.sortComboBox.setCurrentIndex(0)
        self.form.similarityBox.setChecked(False)
        self.form.sizeBox.setChecked(False)
        self.form.pathBox.setChecked(False)
        self.form.deldirsBox.setChecked(False)
        self.form.sizeFormatComboBox.setCurrentIndex(0)
        self.form.subfoldersBox.setChecked(False)
        self.form.closeBox.setChecked(False)

    @mock.patch('doppelganger.preferenceswindow.PreferencesWindow._setWidgetEvents')
    @mock.patch('doppelganger.preferenceswindow.PreferencesWindow._update_form')
    @mock.patch('PyQt5.QtWidgets.QComboBox.addItems')
    def test_init(self, mock_combobox, mock_update, mock_events):
        f = preferenceswindow.PreferencesWindow(self.p)

        sort = ['Similarity rate',
                'Filesize',
                'Width and Height',
                'Path']

        size_format = ['Bytes (B)',
                       'KiloBytes (KB)',
                       'MegaBytes (MB)']

        mock_combobox.assert_any_call(sort)
        mock_combobox.assert_any_call(size_format)
        self.assertEqual(f.sizeSpinBox.minimum(), 100)
        self.assertEqual(f.sizeSpinBox.maximum(), 4000)
        mock_update.assert_called_once()
        mock_events.assert_called_once()

    @mock.patch('doppelganger.preferenceswindow.PreferencesWindow.deleteLater')
    @mock.patch('PyQt5.QtWidgets.QMainWindow.closeEvent')
    def test_closeEvent(self, mock_close, mock_delete):
        self.form.close()

        self.assertTrue(mock_close.called)
        self.assertTrue(mock_delete.called)

    def test_update_form(self):
        self.clear_form()
        data = self.p.conf

        self.form._update_form(data)

        self.assertEqual(data['size'], self.form.sizeSpinBox.value())
        self.assertEqual(data['sort'], self.form.sortComboBox.currentIndex())
        self.assertEqual(data['show_similarity'], self.form.similarityBox.isChecked())
        self.assertEqual(data['show_size'], self.form.sizeBox.isChecked())
        self.assertEqual(data['show_path'], self.form.pathBox.isChecked())
        self.assertEqual(data['delete_dirs'], self.form.deldirsBox.isChecked())
        self.assertEqual(data['subfolders'], self.form.subfoldersBox.isChecked())
        self.assertEqual(data['close_confirmation'], self.form.closeBox.isChecked())

    def test_gather_prefs(self):
        self.clear_form()
        data = {'delete_dirs': False,
                'show_path': False,
                'show_similarity': False,
                'show_size': False,
                'size': 333,
                'sort': 0,
                'size_format': 'B',
                'subfolders': False,
                'close_confirmation': False}

        gathered_data = self.form._gather_prefs()

        self.assertDictEqual(data, gathered_data)

    @mock.patch('PyQt5.QtWidgets.QMainWindow.deleteLater')
    @mock.patch('doppelganger.config.Config.save')
    @mock.patch('doppelganger.preferenceswindow.PreferencesWindow._gather_prefs', return_value={})
    def test_saveBtn_click(self, mock_prefs, mock_save, mock_del):
        QtTest.QTest.mouseClick(self.form.saveBtn, QtCore.Qt.LeftButton)

        mock_prefs.assert_called_once()
        mock_save.assert_called_once()
        mock_del.assert_called_once()
        self.assertDictEqual(self.p.conf, {})

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.config.Config.save', side_effect=OSError)
    @mock.patch('doppelganger.preferenceswindow.PreferencesWindow._gather_prefs', return_value={})
    def test_saveBtn_click_if_raise_OSError(self, mock_prefs, mock_save, mock_exec):
        QtTest.QTest.mouseClick(self.form.saveBtn, QtCore.Qt.LeftButton)

        mock_prefs.assert_called_once()
        mock_save.assert_called_once()
        mock_exec.assert_called_once()

    @mock.patch('PyQt5.QtWidgets.QMainWindow.deleteLater')
    def test_cancelBtn_click(self, mock_del):
        QtTest.QTest.mouseClick(self.form.cancelBtn, QtCore.Qt.LeftButton)

        mock_del.assert_called_once()
