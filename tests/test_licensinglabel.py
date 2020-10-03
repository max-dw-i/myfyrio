'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

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

import logging
import pathlib
import sys
from subprocess import CalledProcessError
from unittest import TestCase, mock

from myfyrio.gui import licensinglabel

# Configure a logger for testing purposes
logger = logging.getLogger('main')
logger.setLevel(logging.WARNING)
if not logger.handlers:
    nh = logging.NullHandler()
    logger.addHandler(nh)


# pylint: disable=missing-class-docstring


class TestLicensingLabel(TestCase):

    def setUp(self):
        self.w = licensinglabel.LicensingLabel()


class TestLicensingLabelMethodOpenLicensesDir(TestLicensingLabel):

    PATCH_ERRM = 'myfyrio.gui.errornotifier.errorMessage'
    PATCH_LICENSE_GET = 'myfyrio.resources.License.LICENSE.get'
    PATCH_OPENFILE = 'myfyrio.gui.utils.openFile'

    def setUp(self):
        super().setUp()

        self.real_platform = sys.platform

    def tearDown(self):
        sys.platform = self.real_platform

    def test_openFile_called_with_license_dir_arg(self):
        mock_Path = mock.Mock(spec=pathlib.Path)
        mock_Path.parent = 'license_dir'
        with mock.patch(self.PATCH_LICENSE_GET, return_value='license_file'):
            with mock.patch('pathlib.Path',
                            return_value=mock_Path) as mock_Path_call:
                with mock.patch(self.PATCH_OPENFILE) as mock_openFile_call:
                    self.w._openLicensesDir()

        mock_Path_call.assert_called_once_with('license_file')
        mock_openFile_call.assert_called_once_with('license_dir')

    def test_log_error_if_subprocess_run_raise_CalledProcessError(self):
        with mock.patch(self.PATCH_OPENFILE,
                        side_effect=CalledProcessError(0, 'cmd')):
            with mock.patch(self.PATCH_ERRM):
                with self.assertLogs('main.licensinglabel', 'ERROR'):
                    self.w._openLicensesDir()

    def test_call_errorMessage_if_raise_CalledProcessError_and_not_Win(self):
        with mock.patch(self.PATCH_OPENFILE,
                        side_effect=CalledProcessError(0, 'cmd')):
            with mock.patch(self.PATCH_ERRM) as mock_msg_call:
                self.w._openLicensesDir()

        mock_msg_call.assert_called_once()

    def test_not_call_errorMessage_if_raise_CalledProcessError_and_Win(self):
        sys.platform = 'win32'
        with mock.patch(self.PATCH_OPENFILE,
                        side_effect=CalledProcessError(0, 'cmd')):
            with mock.patch(self.PATCH_ERRM) as mock_msg_call:
                self.w._openLicensesDir()

        mock_msg_call.assert_not_called()
