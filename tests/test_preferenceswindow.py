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

from PyQt5 import QtCore, QtWidgets

from doppelganger import config, resources
from doppelganger.gui import preferenceswindow

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


PW_MODULE = 'doppelganger.gui.preferenceswindow.'


# pylint: disable=missing-class-docstring


class TestPreferencesWindow(TestCase):

    PW = PW_MODULE + 'PreferencesWindow.'

    def setUp(self):
        self.w = preferenceswindow.PreferencesWindow()
        self.clear_widgets()

    def clear_widgets(self):
        for w in self.w._widgets:
            if isinstance(w, QtWidgets.QCheckBox):
                w.setChecked(False)
            if isinstance(w, QtWidgets.QSpinBox):
                w.setMaximum(200)
                w.setValue(100)
            if isinstance(w, QtWidgets.QComboBox):
                w.setCurrentIndex(0)


class TestMethodGatherWidgets(TestPreferencesWindow):

    def test_all_widgets_of_proper_classes(self):
        classes = (QtWidgets.QComboBox, QtWidgets.QCheckBox,
                   QtWidgets.QSpinBox, QtWidgets.QGroupBox)
        widgets = self.w._gather_widgets()

        for w in widgets:
            self.assertIsInstance(w, classes)

    def test_all_widgets_have_property_conf_param(self):
        widgets = self.w._gather_widgets()

        for w in widgets:
            self.assertIsNotNone(w.property('conf_param'))


class TestMethodInitWidgets(TestPreferencesWindow):

    def test_cores_spinbox_max_value_equal_number_of_cores_or_1(self):
        spinbox = QtWidgets.QSpinBox()
        spinbox.setProperty('conf_param', 'cores')
        spinbox.setMaximum(5000)
        self.w._widgets = [spinbox]
        self.w._init_widgets()

        self.assertEqual(spinbox.maximum(),
                         QtCore.QThread.idealThreadCount() or 1)

    def test_not_cores_spinbox_max_value_not_changed(self):
        spinbox = QtWidgets.QSpinBox()
        spinbox.setProperty('conf_param', 'not_cores')
        spinbox.setMaximum(5000)
        self.w._widgets = [spinbox]
        self.w._init_widgets()

        self.assertEqual(spinbox.maximum(), 5000)


class TestMethodLoadConfig(TestPreferencesWindow):

    PATCH_CONFIG = 'doppelganger.config.Config'

    def setUp(self):
        super().setUp()

        self.mock_Config = mock.Mock(spec=config.Config)
        self.mock_Config.data = 'conf'

    def test_Config_called_with_no_arg(self):
        with mock.patch(self.PATCH_CONFIG, return_value=self.mock_Config) as m:
            self.w._load_config()

        m.assert_called_once_with()

    def test_load_is_ok(self):
        with mock.patch(self.PATCH_CONFIG, return_value=self.mock_Config):
            res = self.w._load_config()

        self.mock_Config.load.assert_called_once_with(
            resources.Config.CONFIG.abs_path #pylint: disable=no-member
        )
        self.assertEqual(res, self.mock_Config)

    def test_log_error_if_load_raise_OSError(self):
        self.mock_Config.load.side_effect = OSError
        with mock.patch(self.PATCH_CONFIG, return_value=self.mock_Config):
            with self.assertLogs('main.preferences', 'ERROR'):
                self.w._load_config()


class TestMethodSaveConfig(TestPreferencesWindow):

    def setUp(self):
        super().setUp()

        self.mock_Config = mock.Mock(spec=config.Config)
        self.w.conf = self.mock_Config

    def test_save_is_ok(self):
        self.w._save_config()

        self.mock_Config.save.assert_called_once_with(
            resources.Config.CONFIG.abs_path # pylint: disable=no-member
        )

    def test_log_error_if_save_raise_OSError(self):
        self.mock_Config.save.side_effect = OSError
        with self.assertLogs('main.preferences', 'ERROR'):
            self.w._save_config()


class TestMethodSetVal(TestPreferencesWindow):

    def test_QComboBox(self):
        w = QtWidgets.QComboBox()
        w.addItems(['0', '1'])
        w.setCurrentIndex(0)
        val = 1
        self.w._setVal(w, val)

        self.assertEqual(w.currentIndex(), val)

    def test_QSpinBox(self):
        w = QtWidgets.QSpinBox()
        val = 66
        w.setValue(13)
        self.w._setVal(w, val)

        self.assertEqual(w.value(), val)

    def test_QCheckBox(self):
        w = QtWidgets.QCheckBox()
        w.setChecked(False)
        val = True
        self.w._setVal(w, val)

        self.assertEqual(w.isChecked(), val)

    def test_QGroupBox(self):
        w = QtWidgets.QGroupBox()
        w.setCheckable(True)
        w.setChecked(False)
        val = True
        self.w._setVal(w, val)

        self.assertEqual(w.isChecked(), val)


class TestMethodVal(TestPreferencesWindow):

    def test_QComboBox(self):
        w = QtWidgets.QComboBox()
        w.addItems(['0', '1'])
        val = 1
        w.setCurrentIndex(val)
        res = self.w._val(w)

        self.assertEqual(res, val)

    def test_QSpinBox(self):
        w = QtWidgets.QSpinBox()
        val = 66
        w.setValue(val)
        res = self.w._val(w)

        self.assertEqual(res, val)

    def test_QCheckBox(self):
        w = QtWidgets.QCheckBox()
        val = True
        w.setChecked(val)
        res = self.w._val(w)

        self.assertEqual(res, val)

    def test_QGroupBox(self):
        w = QtWidgets.QGroupBox()
        w.setCheckable(True)
        val = True
        w.setChecked(val)
        res = self.w._val(w)

        self.assertEqual(res, val)


class TestMethodUpdatePrefs(TestPreferencesWindow):

    def test_setVal_called_with_widget_and_config_value_args(self):
        widget = QtWidgets.QWidget()
        widget.setProperty('conf_param', 'hair')
        self.w._widgets = [widget]
        self.w.conf['hair'] = 'blonde'
        with mock.patch(self.PW+'_setVal') as mock_setVal_call:
            self.w._update_prefs()

        mock_setVal_call.assert_called_once_with(widget, 'blonde')


class TestMethodGatherPrefs(TestPreferencesWindow):

    def test_config_value_set_to_widget_value(self):
        widget = QtWidgets.QWidget()
        widget.setProperty('conf_param', 'hair')
        self.w._widgets = [widget]
        with mock.patch(self.PW+'_val',
                        return_value='blonde') as mock_val_call:
            self.w._gather_prefs()

        mock_val_call.assert_called_once_with(widget)
        self.assertEqual(self.w.conf['hair'], 'blonde')


class TestMethodSetSensitivity(TestPreferencesWindow):

    def test_passed_arg_assigned_to_config_parameter_sensitivity(self):
        self.w.conf['sensitivity'] = 5000
        self.w.setSensitivity(96)

        self.assertEqual(self.w.conf['sensitivity'], 96)


class TestMethodSetMaxCores(TestPreferencesWindow):

    def setUp(self):
        super().setUp()

        self.ideal_cores = QtCore.QThread.idealThreadCount()
        self.threadPool = QtCore.QThreadPool.globalInstance()

    def test_maxThreadCount_not_changed_if_more_cores_set_than_ideal(self):
        old_max_cores = self.threadPool.maxThreadCount()
        self.w.conf['cores'] = self.ideal_cores + 1
        self.w._setMaxCores()

        self.assertEqual(self.threadPool.maxThreadCount(), old_max_cores)

    def test_maxThreadCount_changed_if_less_or_eq_cores_set_than_ideal(self):
        self.threadPool.setMaxThreadCount(self.ideal_cores + 1)
        self.w.conf['cores'] = self.ideal_cores
        self.w._setMaxCores()

        self.assertEqual(self.threadPool.maxThreadCount(), self.ideal_cores)


class TestMethodSavePreferences(TestPreferencesWindow):

    def test_gather_prefs_called(self):
        with mock.patch(self.PW+'_gather_prefs') as mock_gather:
            with mock.patch(self.PW+'_save_config'):
                self.w._savePreferences()

        mock_gather.assert_called_once_with()

    def test_save_config_called(self):
        with mock.patch(self.PW+'_gather_prefs'):
            with mock.patch(self.PW+'_save_config') as mock_save_call:
                self.w._savePreferences()

        mock_save_call.assert_called_once_with()

    def test_setMaxCores_called(self):
        with mock.patch(self.PW+'_gather_prefs'):
            with mock.patch(self.PW+'_save_config'):
                with mock.patch(self.PW+'_setMaxCores') as mock_cores_call:
                    self.w._savePreferences()

        mock_cores_call.assert_called_once_with()

    @mock.patch('PyQt5.QtWidgets.QMainWindow.close')
    def test_close_called(self, mock_close_call):
        with mock.patch(self.PW+'_gather_prefs'):
            with mock.patch(self.PW+'_save_config'):
                self.w._savePreferences()

        mock_close_call.assert_called_once()
