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
import sys

from myfyrio.gui import utils

# pylint: disable=missing-class-docstring


class TestFuncOpenFile(TestCase):

    def setUp(self):
        self.real_platform = sys.platform

        self.path = '/path/to/FileOrDirectory'

    def tearDown(self):
        sys.platform = self.real_platform

    def test_subprocess_run_called_with_linux_img_viewer_cmd(self):
        sys.platform = 'linux'
        with mock.patch('subprocess.run') as mock_run:
            utils.openFile(self.path)

        mock_run.assert_called_once_with(['xdg-open', self.path], check=True)

    def test_subprocess_run_called_with_win_img_viewer_cmd(self):
        sys.platform = 'win32'
        with mock.patch('subprocess.run') as mock_run:
            utils.openFile(self.path)

        mock_run.assert_called_once_with(['explorer', self.path], check=True)

    def test_subprocess_run_called_with_mac_img_viewer_cmd(self):
        sys.platform = 'darwin'
        with mock.patch('subprocess.run') as mock_run:
            utils.openFile(self.path)

        mock_run.assert_called_once_with(['open', self.path], check=True)

    def test_subprocess_run_called_with_unknown_paltform(self):
        sys.platform = 'whatever_platform'
        with mock.patch('subprocess.run') as mock_run:
            utils.openFile(self.path)

        mock_run.assert_called_once_with(
            ['Unknown platform', self.path], check=True
        )
