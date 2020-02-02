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

import sys
from unittest import TestCase, mock

from doppelganger.resources import manager


# pylint: disable=missing-class-docstring,unused-argument


class TestFuncResource(TestCase):

    def setUp(self):
        self.mock_Path = mock.Mock()
        self.mock_Path.parent = mock.MagicMock()

        self.mock_resource = mock.Mock(spec=manager.Image)
        self.mock_resource.value = 'resource'

        self.mock_Path.parent.__truediv__.return_value = 'absolute_path'

    def test_absolute_path_formed_properly(self):
        with mock.patch('pathlib.Path', return_value=self.mock_Path):
            manager.resource(self.mock_resource)

        self.mock_Path.parent.__truediv__.assert_called_once_with(
            self.mock_resource.value
        )

    def test_return_resource_absolute_path_if_not_bundled(self):
        sys.frozen = False
        with mock.patch('pathlib.Path', return_value=self.mock_Path):
            res = manager.resource(self.mock_resource)

        self.assertEqual(res, 'absolute_path')

    def test_return_resource_absolute_path_if_bundled_but_not_ui_file(self):
        sys.frozen = True
        with mock.patch('pathlib.Path', return_value=self.mock_Path):
            res = manager.resource(self.mock_resource)

        self.assertEqual(res, 'absolute_path')

    def test_return_ui_file_obj_if_bundled_and_ui_file(self):
        mock_resource = mock.Mock(spec=manager.UI)
        mock_resource.value = 'resource'
        sys.frozen = True
        with mock.patch('pathlib.Path', return_value=self.mock_Path):
            with mock.patch('doppelganger.resources.manager._ui_file_obj',
                            return_value='file_obj') as mock_call_ui:
                res = manager.resource(mock_resource)

        mock_call_ui.assert_called_once_with('absolute_path')
        self.assertEqual(res, 'file_obj')


class TestFuncUIFileObj(TestCase):

    def setUp(self):
        self.mock_QFile = mock.Mock()

    def test_QFile_called_with_resource_absolute_path(self):
        path = 'resource_absolute_path'
        with mock.patch('PyQt5.QtCore.QFile') as mock_QFile_call:
            manager._ui_file_obj(path)

        mock_QFile_call.assert_called_once_with(path)

    @mock.patch('doppelganger.resources.manager.BytesIO')
    @mock.patch('builtins.bytes')
    def test_QFile_opened(self, mock_bytes_call, mock_BytesIO_call):
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            manager._ui_file_obj('path')

        self.mock_QFile.open.assert_called_once()

    @mock.patch('doppelganger.resources.manager.BytesIO')
    @mock.patch('builtins.bytes')
    def test_QFile_content_read(self, mock_bytes_call, mock_BytesIO_call):
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            manager._ui_file_obj('path')

        self.mock_QFile.readAll.assert_called_once()

    @mock.patch('doppelganger.resources.manager.BytesIO')
    @mock.patch('builtins.bytes')
    def test_QFile_closed(self, mock_bytes_call, mock_BytesIO_call):
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            manager._ui_file_obj('path')

        self.mock_QFile.close.assert_called_once()

    @mock.patch('doppelganger.resources.manager.BytesIO')
    @mock.patch('builtins.bytes')
    def test_QFile_content_converted_to_bytes(self, mock_bytes_call,
                                              mock_BytesIO_call):
        resource_file_content = 'resource_data'
        self.mock_QFile.readAll.return_value = resource_file_content
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            manager._ui_file_obj('path')

        mock_bytes_call.assert_called_once_with(resource_file_content)

    @mock.patch('doppelganger.resources.manager.BytesIO')
    @mock.patch('builtins.bytes', return_value='bytes')
    def test_BytesIO_called_with_bytes(self, mock_bytes_call,
                                       mock_BytesIO_call):
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            manager._ui_file_obj('path')

        mock_BytesIO_call.assert_called_once_with('bytes')

    @mock.patch('doppelganger.resources.manager.BytesIO', return_value='Bytes')
    @mock.patch('builtins.bytes')
    def test_return_BytesIO_obj(self, mock_bytes_call, mock_BytesIO_call):
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            res = manager._ui_file_obj('path')

        self.assertEqual(res, 'Bytes')
