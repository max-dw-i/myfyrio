'''Copyright 2020 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Myfyrio.

Myfyrio is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Myfyrio is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Myfyrio. If not, see <https://www.gnu.org/licenses/>.
'''

from unittest import TestCase, mock

from PyQt5 import QtWidgets

from myfyrio.gui import progresslabel

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

PL = 'myfyrio.gui.progresslabel.ProgressLabel.'

# pylint: disable=missing-class-docstring


class TestClassProgressLabel(TestCase):

    def setUp(self):
        self.w = progresslabel.ProgressLabel()


class TestClassProgressLabelMethodClear(TestClassProgressLabel):

    def test_updateNumber_called_with_0(self):
        with mock.patch(PL+'updateNumber') as mock_update_call:
            self.w.clear()

        mock_update_call.assert_called_once_with(0)


class TestClassProgressLabelMethodUpdateNumber(TestClassProgressLabel):

    def test_label_number_changed(self):
        letter, old_number = 'A', '0'
        self.w.setText(letter + ' ' + old_number)
        new_number = 2020
        self.w.updateNumber(new_number)

        self.assertEqual(self.w.text(), letter + ' ' + str(new_number))
