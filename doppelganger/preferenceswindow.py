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

Module implementing window "Preferences"
'''

from __future__ import annotations

import logging
import pathlib
from typing import List, Union

from PyQt5 import QtWidgets, uic

from doppelganger import config

pref_logger = logging.getLogger('main.preferences')


def load_config() -> config.ConfigData:
    '''Load and return config with the preferences

    :return: dict with the loaded preferences
    '''

    c = config.Config()
    try:
        c.load()
    except OSError as e:
        msg_box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            'Errors',
            ('Cannot load preferences from file "config.p". Default '
             'preferences will be loaded. For more details, '
             'see "errors.log"')
        )
        msg_box.exec()

        pref_logger.error(e)

        c.default()

    return c.data

def save_config(conf: config.ConfigData) -> None:
    '''Save config with the preferences

    :param conf: dict with config data
    '''

    c = config.Config(conf)
    try:
        c.save()
    except OSError as e:
        msg_box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            'Error',
            ("Cannot save preferences into file 'config.p'. "
             "For more details, see 'errors.log'")
        )
        msg_box.exec()

        pref_logger.error(e)

def setVal(widget: Widget, val: Value) -> None:
    '''Set value of widget

    :param widget: widget to set,
    :param val: value to set
    '''

    if isinstance(widget, QtWidgets.QSpinBox):
        widget.setValue(val)
    if isinstance(widget, QtWidgets.QComboBox):
        widget.setCurrentIndex(val)
    if isinstance(widget, QtWidgets.QCheckBox):
        widget.setChecked(val)

def val(widget: Widget) -> Value:
    '''Get value of widget

    :param widget: widget whose value to get,
    :return: value of widget
    '''

    if isinstance(widget, QtWidgets.QSpinBox):
        v = widget.value()
    if isinstance(widget, QtWidgets.QComboBox):
        v = widget.currentIndex()
    if isinstance(widget, QtWidgets.QCheckBox):
        v = widget.isChecked()

    return v


class PreferencesWindow(QtWidgets.QMainWindow):
    '''Implementing window "Preferences"'''

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        pref_ui_path = 'doppelganger/resources/ui/preferenceswindow.ui'
        PREFERENCES_UI = pathlib.Path(pref_ui_path)
        uic.loadUi(str(PREFERENCES_UI), self)

        self.widgets = self._gather_widgets()

        self.conf = load_config()
        self.update_prefs(self.conf)

        self.saveBtn.clicked.connect(self.saveBtn_click)
        self.cancelBtn.clicked.connect(self.cancelBtn_click)

        sizeHint = self.sizeHint()
        self.setMaximumSize(sizeHint)
        self.resize(sizeHint)

    def _gather_widgets(self) -> List[Widget]:
        widgets = []
        widget_types = [QtWidgets.QComboBox, QtWidgets.QCheckBox,
                        QtWidgets.QSpinBox]

        for w_type in widget_types:
            w_found = self.findChildren(w_type)
            for w in w_found: # rewrite when every is enabled
                if w.isEnabled():
                    widgets.append(w)
        return widgets

    def update_prefs(self, conf: config.ConfigData) -> None:
        '''Update the form with new preferences

        :param conf: new preferences
        '''

        for w in self.widgets:
            setVal(w, conf[w.property('conf_param')])

    def gather_prefs(self) -> config.ConfigData:
        '''Gather checked/unchecked/filled by a user options
        and form a config dictionary

        :return: dict with preferences of the programme
        '''

        return {w.property('conf_param'): val(w) for w in self.widgets}

    def saveBtn_click(self) -> None:
        self.conf = self.gather_prefs()
        save_config(self.conf)
        self.close()

    def cancelBtn_click(self) -> None:
        self.close()


#################################Types##################################
Widget = Union[QtWidgets.QSpinBox, QtWidgets.QComboBox,
               QtWidgets.QCheckBox] # widget changing preferences
Value = Union[int, str]             # value of widget
########################################################################
