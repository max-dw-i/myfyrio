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

from PyQt5 import QtWidgets

from doppelganger.gui.errornotifier import errorMessage


ERR_NOTE_MODULE = 'doppelganger.gui.errornotifier.'


# pylint: disable=missing-class-docstring


class TestFuncErrorMessage(TestCase):

    def setUp(self):
        super().setUp()

        self.mock_msgBox = mock.Mock(spec=QtWidgets.QMessageBox)

    def test_QMessageBox_exec_not_called_if_no_errors(self):
        with mock.patch(ERR_NOTE_MODULE+'QMessageBox',
                        return_value=self.mock_msgBox):
            errorMessage([])

        self.mock_msgBox.exec.assert_not_called()

    def test_QMessageBox_exec_called_if_errors(self):
        errors = ['Error']
        with mock.patch(ERR_NOTE_MODULE+'QMessageBox',
                        return_value=self.mock_msgBox):
            errorMessage(errors)

        self.mock_msgBox.exec.assert_called_once_with()
