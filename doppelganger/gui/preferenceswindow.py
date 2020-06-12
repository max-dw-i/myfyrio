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

-------------------------------------------------------------------------------

Module implementing the "Preferences" window
'''

import os
from typing import List, Union

from PyQt5 import QtCore, QtWidgets, uic

from doppelganger import config, resources
from doppelganger.logger import Logger

logger = Logger.getLogger('preferences')


###################################Types#######################################
Widget = Union[QtWidgets.QSpinBox, QtWidgets.QComboBox,
               QtWidgets.QCheckBox, QtWidgets.QGroupBox] # preference widgets
Value = Union[int, str] # values of preference widgets
###############################################################################


class PreferencesWindow(QtWidgets.QMainWindow):
    '''Class representing the "Preferences" window

    :param parent: widget's parent (optional)
    '''

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        pref_ui = resources.UI.PREFERENCES.abs_path # pylint: disable=no-member
        uic.loadUi(pref_ui, self)

        self._widgets = self._gather_widgets()
        self._init_widgets()

        self.conf = self._load_config()
        self._update_prefs()

        self.saveBtn.clicked.connect(self._savePreferences)
        self.cancelBtn.clicked.connect(self.close)

        sizeHint = self.sizeHint()
        self.setMaximumSize(sizeHint)
        self.resize(sizeHint)

        self.setWindowModality(QtCore.Qt.ApplicationModal)

    def _gather_widgets(self) -> List[Widget]:
        widget_types = [QtWidgets.QComboBox, QtWidgets.QCheckBox,
                        QtWidgets.QSpinBox, QtWidgets.QGroupBox]
        widgets = []

        for w_type in widget_types:
            for w in self.findChildren(w_type):
                # Every widget that keeps some preference value
                # has a 'conf_param' property
                if w.property('conf_param') is not None:
                    widgets.append(w)
        return widgets

    def _init_widgets(self) -> None:
        for w in self._widgets:
            if w.property('conf_param') == 'cores':
                w.setMaximum(os.cpu_count() or 1)

    @staticmethod
    def _load_config() -> config.Config:
        conf = config.Config()
        try:
            conf.load(resources.Config.CONFIG.abs_path) # pylint: disable=no-member

        except OSError:
            err_msg = 'Config file cannot be read from the disk'
            logger.exception(err_msg)

        return conf

    def _save_config(self) -> None:
        try:
            self.conf.save(resources.Config.CONFIG.abs_path) # pylint: disable=no-member

        except OSError:
            err_msg = 'Config cannot be written on the disk'
            logger.exception(err_msg)

    @staticmethod
    def _setVal(widget: Widget, val: Value) -> None:
        if isinstance(widget, QtWidgets.QSpinBox):
            widget.setValue(val)
        if isinstance(widget, QtWidgets.QComboBox):
            widget.setCurrentIndex(val)
        if isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QGroupBox)):
            widget.setChecked(val)

    @staticmethod
    def _val(widget: Widget) -> Value:
        if isinstance(widget, QtWidgets.QSpinBox):
            v = widget.value()
        if isinstance(widget, QtWidgets.QComboBox):
            v = widget.currentIndex()
        if isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QGroupBox)):
            v = widget.isChecked()

        return v

    def _update_prefs(self) -> None:
        for w in self._widgets:
            conf_param = w.property('conf_param')
            self._setVal(w, self.conf[conf_param])

    def _gather_prefs(self) -> None:
        for w in self._widgets:
            conf_param = w.property('conf_param')
            self.conf[conf_param] = self._val(w)

    def setSensitivity(self, value: Value) -> None:
        self.conf['sensitivity'] = value

    def _savePreferences(self) -> None:
        self._gather_prefs()
        self._save_config()
        self.close()
