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

import pathlib

from PyQt5 import QtWidgets, uic

from doppelganger import config, core


class PreferencesWindow(QtWidgets.QMainWindow):
    """'Options' -> 'Preferences...' form"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        pref_ui_path = 'doppelganger/resources/ui/preferenceswindow.ui'
        PREFERENCES_UI = pathlib.Path(pref_ui_path)
        uic.loadUi(str(PREFERENCES_UI), self)
        self.sortComboBox.addItems(
            [
                'Similarity rate',  # in 'config.p' - 0
                'Filesize',         # in 'config.p' - 1
                'Width and Height', # in 'config.p' - 2
                'Path'              # in 'config.p' - 3
            ]
        )
        self.sizeFormatComboBox.addItems(
            [
                'Bytes (B)',        # in 'config.p' - 'B'
                'KiloBytes (KB)',   # in 'config.p' - 'KB'
                'MegaBytes (MB)',   # in 'config.p' - 'MB'
            ]
        )
        self.sizeSpinBox.setMinimum(100)
        self.sizeSpinBox.setMaximum(4000)

        self._update_form(parent.conf)

        self._setWidgetEvents()

    def closeEvent(self, event) -> None:
        '''Function called on close event'''

        super().closeEvent(event)
        self.deleteLater()

    def _setWidgetEvents(self) -> None:
        '''Link events and functions called on the events'''

        self.saveBtn.clicked.connect(self.saveBtn_click)
        self.cancelBtn.clicked.connect(self.cancelBtn_click)

    def _encode_size_format(self, size_format: core.SizeFormat) -> int:
        sf = {'B': 0,
              'KB': 1,
              'MB': 2}
        return sf[size_format]

    def _decode_size_format(self, index: int) -> core.SizeFormat:
        sf = {0: 'B',
              1: 'KB',
              2: 'MB'}
        return sf[index]

    def _update_form(self, data: config.ConfigData) -> None:
        '''Update the form with new preferences

        :param data: new preferences data
        '''

        self.sizeSpinBox.setValue(data['size'])
        self.sortComboBox.setCurrentIndex(data['sort'])
        self.sizeFormatComboBox.setCurrentIndex(
            self._encode_size_format(data['size_format'])
        )

        if data['show_similarity']:
            self.similarityBox.setChecked(True)
        if data['show_size']:
            self.sizeBox.setChecked(True)
        if data['show_path']:
            self.pathBox.setChecked(True)
        if data['delete_dirs']:
            self.deldirsBox.setChecked(True)
        if data['subfolders']:
            self.subfoldersBox.setChecked(True)
        if data['close_confirmation']:
            self.closeBox.setChecked(True)

    def _gather_prefs(self) -> config.ConfigData:
        '''Gather checked/unchecked/filled by a user options
        and form a config dictionary

        :return: dictionary with programme's preferences
        '''

        data = {
            'size': self.sizeSpinBox.value(),
            'show_similarity': self.similarityBox.isChecked(),
            'show_size': self.sizeBox.isChecked(),
            'show_path': self.pathBox.isChecked(),
            'sort': self.sortComboBox.currentIndex(),
            'delete_dirs': self.deldirsBox.isChecked(),
            'size_format': self._decode_size_format(
                self.sizeFormatComboBox.currentIndex()
            ),
            'subfolders': self.subfoldersBox.isChecked(),
            'close_confirmation': self.closeBox.isChecked(),
        }
        return data

    def saveBtn_click(self) -> None:
        '''Function called on pressing button "Save"'''

        data = self._gather_prefs()
        try:
            config.Config(data).save()
        except OSError:
            msg_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Error',
                ("Cannot save preferences into file 'config.p'. "
                 "For more details, see 'errors.log'")
            )
            msg_box.exec()
        else:
            self.parent().conf = data
            self.deleteLater()

    def cancelBtn_click(self) -> None:
        '''Function called on pressing button "Cancel"'''

        self.deleteLater()
