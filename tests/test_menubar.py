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

from doppelganger.gui import menubar

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


MBAR = 'doppelganger.gui.menubar.MenuBar.'


# pylint: disable=missing-class-docstring


class TestClassMenuBar(TestCase):

    def setUp(self):
        self.w = menubar.MenuBar()


class TestClassMenuBarMethodInit(TestClassMenuBar):

    def test_QMenuBar_subclassed(self):
        self.assertIsInstance(self.w, QtWidgets.QMenuBar)


class TestClassMenuBarMethodOpenWindow(TestClassMenuBar):

    def setUp(self):
        super().setUp()

        self.mock_sender = mock.Mock(spec=QtWidgets.QAction)
        self.mock_window = mock.Mock(spec=QtWidgets.QMainWindow)
        self.mock_sender.data.return_value = self.mock_window

    def test_activate_window_if_it_is_open(self):
        self.mock_window.isVisible.return_value = True
        with mock.patch(MBAR+'sender', return_value=self.mock_sender):
            self.w.openWindow()

        self.mock_window.activateWindow.assert_called_once_with()

    def test_show_window_if_it_is_not_open(self):
        self.mock_window.isVisible.return_value = False
        with mock.patch(MBAR+'sender', return_value=self.mock_sender):
            self.w.openWindow()

        self.mock_window.show.assert_called_once_with()


class TestClassMenuBarMethodOpenDocs(TestClassMenuBar):

    def test_webbrowser_open_called(self):
        URL = 'https://github.com/oratosquilla-oratoria/doppelganger'
        with mock.patch('webbrowser.open') as mock_open_call:
            self.w.openDocs()

        mock_open_call.assert_called_once_with(URL)
