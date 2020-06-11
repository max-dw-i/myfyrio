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

from doppelganger.gui import errornotifier


ERR_NOTE_MODULE = 'doppelganger.gui.errornotifier.'


# pylint: disable=missing-class-docstring


class TestErrorNotifier(TestCase):

    EN = ERR_NOTE_MODULE + 'ErrorNotifier.'

    def setUp(self):
        self.err_note = errornotifier.ErrorNotifier()


class TestErrorNotifierMethodInit(TestErrorNotifier):

    def test_init_values(self):
        self.assertListEqual(self.err_note._errors, [])


class TestErrorNotifierMethodAddError(TestErrorNotifier):

    def test_add_passed_error_message_to_attr_errors(self):
        self.err_note.addError('Error')

        self.assertListEqual(self.err_note._errors, ['Error'])


class TestErrorNotifierMethodReset(TestErrorNotifier):

    def test_assign_empty_list_to_attr_errors(self):
        self.err_note._errors = ['Error']
        self.err_note.reset()

        self.assertListEqual(self.err_note._errors, [])


class TestErrorNotifierMethodErrorMessage(TestErrorNotifier):

    def setUp(self):
        super().setUp()

        self.mock_msgBox = mock.Mock(spec=QtWidgets.QMessageBox)

    def test_QMessageBox_exec_not_called_if_no_errors(self):
        self.err_note._errors = []
        with mock.patch(ERR_NOTE_MODULE+'QMessageBox',
                        return_value=self.mock_msgBox):
            self.err_note.errorMessage()

        self.mock_msgBox.exec.assert_not_called()

    def test_QMessageBox_exec_called_if_errors(self):
        self.err_note._errors = ['Error']
        with mock.patch(ERR_NOTE_MODULE+'QMessageBox',
                        return_value=self.mock_msgBox):
            self.err_note.errorMessage()

        self.mock_msgBox.exec.assert_called_once_with()
