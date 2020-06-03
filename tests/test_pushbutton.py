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

from PyQt5 import QtWidgets

from doppelganger.gui import pushbutton

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


PB_MODULE = 'doppelganger.gui.pushbutton.'


# pylint: disable=missing-class-docstring


class TestClassPushButton(TestCase):

    PB = PB_MODULE + 'PushButton.'

    def setUp(self):
        self.w = pushbutton.PushButton()


class TestClassPushButtonMethodEnable(TestClassPushButton):

    def test_setEnabled_called_with_True_arg(self):
        with mock.patch(self.PB+'setEnabled') as mock_setEnabled_call:
            self.w.enable()

        mock_setEnabled_call.assert_called_once_with(True)


class TestClassPushButtonMethodDisable(TestClassPushButton):

    def test_setEnabled_called_with_False_arg(self):
        with mock.patch(self.PB+'setEnabled') as mock_setEnabled_call:
            self.w.disable()

        mock_setEnabled_call.assert_called_once_with(False)


class TestClassStartButton(TestCase):

    def setUp(self):
        self.w = pushbutton.StartButton()


class TestClassStartButtonMethodInit(TestClassStartButton):

    def test_attr_run_is_False_by_default(self):
        self.assertFalse(self.w._run)

    def test_attr_paths_is_False_by_default(self):
        self.assertFalse(self.w._paths)


class TestClassStartButtonMethodStarted(TestClassStartButton):

    def test_parent_disable_called(self):
        with mock.patch(PB_MODULE+'PushButton.disable') as mock_disable_call:
            self.w.started()

        mock_disable_call.assert_called_once_with()

    def test_attr_run_set_to_True(self):
        self.w.started()

        self.assertTrue(self.w._run)


class TestClassStartButtonMethodFinished(TestClassStartButton):

    def test_parent_enable_called_if_attr_paths_is_True(self):
        self.w._paths = True
        with mock.patch(PB_MODULE+'PushButton.enable') as mock_enable_call:
            self.w.finished()

        mock_enable_call.assert_called_once_with()

    def test_parent_enable_not_called_if_attr_paths_is_False(self):
        self.w._paths = False
        with mock.patch(PB_MODULE+'PushButton.enable') as mock_enable_call:
            self.w.finished()

        mock_enable_call.assert_not_called()

    def test_attr_run_set_to_False(self):
        self.w.finished()

        self.assertFalse(self.w._run)


class TestClassStartButtonMethodSwitch(TestClassStartButton):

    def test_paths_arg_assigned_to_attr_paths(self):
        self.w._paths = False
        self.w.switch(True)

        self.assertTrue(self.w._paths)

    def test_parents_enable_called_if_run_is_False_and_paths_is_True(self):
        self.w._run = False
        with mock.patch(PB_MODULE+'PushButton.enable') as mock_enable_call:
            self.w.switch(True)

        mock_enable_call.assert_called_once_with()

    def test_parents_disable_called_if_run_is_False_and_paths_is_False(self):
        self.w._run = False
        with mock.patch(PB_MODULE+'PushButton.disable') as mock_disable_call:
            self.w.switch(False)

        mock_disable_call.assert_called_once_with()

    def test_parents_enable_not_called_if_run_is_True_and_paths_is_True(self):
        self.w._run = True
        with mock.patch(PB_MODULE+'PushButton.enable') as mock_enable_call:
            self.w.switch(True)

        mock_enable_call.assert_not_called()

    def test_parents_disable_not_called_if_run_is_True_and_paths_is_False(self):
        self.w._run = True
        with mock.patch(PB_MODULE+'PushButton.disable') as mock_disable_call:
            self.w.switch(False)

        mock_disable_call.assert_not_called()
