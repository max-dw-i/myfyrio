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

import logging
from unittest import TestCase, mock

from PyQt5 import QtWidgets

from doppelganger import config, preferenceswindow

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


class TestLoadConfigFunc(TestCase):

    NAME = 'doppelganger.config.Config'

    def setUp(self):
        self.mock_Config = mock.create_autospec(config.Config)
        self.mock_Config.data = 'conf'

    def test_Config_called_with_no_arg(self):
        with mock.patch(self.NAME, return_value=self.mock_Config) as m:
            preferenceswindow.load_config()

        m.assert_called_once_with()

    def test_load_is_ok(self):
        with mock.patch(self.NAME, return_value=self.mock_Config):
            data = preferenceswindow.load_config()

        self.mock_Config.load.assert_called_once_with()
        self.assertEqual(data, self.mock_Config.data)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_show_msg_if_load_raise_OSError(self, mock_exec):
        self.mock_Config.load.side_effect = OSError
        with mock.patch(self.NAME, return_value=self.mock_Config):
            preferenceswindow.load_config()

        mock_exec.assert_called_once_with()

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_log_error_if_load_raise_OSError(self, mock_exec):
        self.mock_Config.load.side_effect = OSError
        with mock.patch(self.NAME, return_value=self.mock_Config):
            with self.assertLogs('main.preferences', 'ERROR'):
                preferenceswindow.load_config()

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_load_default_conf_if_load_raise_OSError(self, mock_exec):
        self.mock_Config.load.side_effect = OSError
        with mock.patch(self.NAME, return_value=self.mock_Config):
            data = preferenceswindow.load_config()

        self.mock_Config.default.assert_called_once_with()
        self.assertEqual(data, self.mock_Config.data)


class TestSaveConfigFunc(TestCase):

    NAME = 'doppelganger.config.Config'
    CONF = {'test_param': 'test_val'}

    def setUp(self):
        self.mock_Config = mock.create_autospec(config.Config)

    def test_Config_called_with_conf_arg(self):
        with mock.patch(self.NAME, return_value=self.mock_Config) as m:
            preferenceswindow.save_config(self.CONF)

        m.assert_called_once_with(self.CONF)

    def test_save_is_ok(self):
        with mock.patch(self.NAME, return_value=self.mock_Config):
            preferenceswindow.save_config(self.CONF)

        self.mock_Config.save.assert_called_once_with()

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_show_msg_if_save_raise_OSError(self, mock_exec):
        self.mock_Config.save.side_effect = OSError
        with mock.patch(self.NAME, return_value=self.mock_Config):
            preferenceswindow.save_config(self.CONF)

        mock_exec.assert_called_once_with()

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_log_error_if_save_raise_OSError(self, mock_exec):
        self.mock_Config.save.side_effect = OSError
        with mock.patch(self.NAME, return_value=self.mock_Config):
            with self.assertLogs('main.preferences', 'ERROR'):
                preferenceswindow.save_config(self.CONF)


class TestSetValFunc(TestCase):

    def test_QComboBox(self):
        w = QtWidgets.QComboBox()
        w.addItems(['0', '1'])
        w.setCurrentIndex(0)
        val = 1
        preferenceswindow.setVal(w, val)

        self.assertEqual(w.currentIndex(), val)

    def test_QSpinBox(self):
        w = QtWidgets.QSpinBox()
        val = 66
        w.setValue(13)
        preferenceswindow.setVal(w, val)

        self.assertEqual(w.value(), val)

    def test_QCheckBox(self):
        w = QtWidgets.QCheckBox()
        w.setChecked(False)
        val = True
        preferenceswindow.setVal(w, val)

        self.assertEqual(w.isChecked(), val)


class TestValFunc(TestCase):

    def test_QComboBox(self):
        w = QtWidgets.QComboBox()
        w.addItems(['0', '1'])
        val = 1
        w.setCurrentIndex(val)
        res = preferenceswindow.val(w)

        self.assertEqual(res, val)

    def test_QSpinBox(self):
        w = QtWidgets.QSpinBox()
        val = 66
        w.setValue(val)
        res = preferenceswindow.val(w)

        self.assertEqual(res, val)

    def test_QCheckBox(self):
        w = QtWidgets.QCheckBox()
        val = True
        w.setChecked(val)
        res = preferenceswindow.val(w)

        self.assertEqual(res, val)


class TestPreferencesForm(TestCase):

    def setUp(self):
        self.w = preferenceswindow.PreferencesWindow()
        self.clear_widgets()

    def clear_widgets(self):
        for w in self.w.widgets:
            if isinstance(w, QtWidgets.QCheckBox):
                w.setChecked(False)
            if isinstance(w, QtWidgets.QSpinBox):
                w.setValue(100)
            if isinstance(w, QtWidgets.QComboBox):
                w.setCurrentIndex(0)

    def test_update_prefs(self):
        conf = {
            'delete_dirs': True,
            'show_path': True,
            'show_similarity': True,
            'show_size': True,
            'size_format': 2,
            'size': 666,
            'sort': 3,
            'subfolders': True,
            'close_confirmation': True
        }
        self.w.update_prefs(conf)

        for w in self.w.widgets:
            self.assertEqual(preferenceswindow.val(w),
                             conf[w.property('conf_param')])

    def test_gather_prefs(self):
        data = {'delete_dirs': False,
                'show_path': False,
                'show_similarity': False,
                'show_size': False,
                'size': 100,
                'sort': 0,
                'size_format': 0,
                'subfolders': False,
                'close_confirmation': False}

        gathered_data = self.w.gather_prefs()

        self.assertDictEqual(data, gathered_data)

    @mock.patch('doppelganger.preferenceswindow.save_config')
    def test_saveBtn_click_save_config_in_attr(self, mock_save):
        NAME = 'doppelganger.preferenceswindow.PreferencesWindow.gather_prefs'
        conf = {'param': 'val'}
        with mock.patch(NAME, return_value=conf):
            self.w.saveBtn_click()

        self.assertDictEqual(self.w.conf, conf)

    @mock.patch('doppelganger.preferenceswindow.save_config')
    def test_saveBtn_click_call_save_config(self, mock_save):
        NAME = 'doppelganger.preferenceswindow.PreferencesWindow.gather_prefs'
        conf = {'param': 'val'}
        with mock.patch(NAME, return_value=conf):
            self.w.saveBtn_click()

        mock_save.assert_called_once_with(conf)

    @mock.patch('PyQt5.QtWidgets.QMainWindow.close')
    @mock.patch('doppelganger.config.Config.save')
    def test_saveBtn_click_call_close(self, mock_save, mock_close):
        NAME = 'doppelganger.preferenceswindow.PreferencesWindow.gather_prefs'
        with mock.patch(NAME):
            self.w.saveBtn_click()

        mock_close.assert_called_once()


    @mock.patch('PyQt5.QtWidgets.QMainWindow.close')
    def test_cancelBtn_click(self, mock_close):
        self.w.cancelBtn_click()

        mock_close.assert_called_once()