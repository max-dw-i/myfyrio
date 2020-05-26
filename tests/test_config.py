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

import os
import pickle
from unittest import TestCase, mock

from doppelganger import config

# pylint: disable=unused-argument,missing-class-docstring


class TestClassConfig(TestCase):

    def setUp(self):
        self.c = config.Config()


class TestMethodInit(TestClassConfig):

    def test_attr_data_is_empty(self):

        self.assertDictEqual(self.c.data, {})


class TestMethodDefault(TestClassConfig):

    def test_default(self):
        DEFAULT_CONFIG = {
            'size': 200,
            'show_similarity': True,
            'show_size': True,
            'show_path': True,
            'sort': 0,
            'delete_dirs': False,
            'size_format': 1,
            'subfolders': True,
            'close_confirmation': False,
            'filter_img_size': False,
            'min_width': 0,
            'max_width': 1000000,
            'min_height': 0,
            'max_height': 1000000,
            'cores': os.cpu_count() or 1,
            'lazy': False
        }
        self.c._default()

        self.assertEqual(self.c.data, DEFAULT_CONFIG)


class TestMethodSave(TestClassConfig):

    def setUp(self):
        super().setUp()

        self.file = 'config_file'

    @mock.patch('pickle.dump')
    def test_save_into_file(self, mock_dump_call):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open_call:
            self.c.save(self.file)

        mock_open_call.assert_called_once_with(self.file, 'wb')

    @mock.patch('pickle.dump')
    def test_save_dump_config_data(self, mock_dump_call):
        with mock.patch('builtins.open', mock.mock_open()):
            self.c.save(self.file)

        data = mock_dump_call.call_args[0][0]
        self.assertDictEqual(data, self.c.data)

    @mock.patch('builtins.open', side_effect=OSError)
    def test_save_raise_OSError_if_open_raise_OSError(self, mock_open_call):
        with self.assertRaises(OSError):
            self.c.save(self.file)


class TestMethodLoad(TestClassConfig):

    def setUp(self):
        super().setUp()

        self.file = 'config_file'

    @mock.patch('pickle.load')
    def test_load_from_file(self, mock_load_call):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open_call:
            self.c.load(self.file)

        mock_open_call.assert_called_once_with(self.file, 'rb')

    @mock.patch('pickle.load', return_value='test')
    @mock.patch('builtins.open')
    def test_load_assign_loaded_conf_to_attr_data(self, mock_open_call,
                                                  mock_load_call):
        self.c.load(self.file)

        self.assertEqual('test', self.c.data)

    @mock.patch('doppelganger.config.Config._default')
    @mock.patch('builtins.open', side_effect=FileNotFoundError)
    def test_default_called_if_FileNotFoundError(self, mock_open_call,
                                                 mock_default_call):
        self.c.load(self.file)

        mock_default_call.assert_called_once_with()

    @mock.patch('doppelganger.config.Config._default')
    @mock.patch('builtins.open', side_effect=EOFError)
    def test_default_called__OSError_raised_if_EOFError(self, mock_open_call,
                                                        mock_default_call):
        with self.assertRaises(OSError):
            self.c.load(self.file)

        mock_default_call.assert_called_once_with()

    @mock.patch('doppelganger.config.Config._default')
    @mock.patch('builtins.open', side_effect=OSError)
    def test_default_called__OSError_raised_if_OSError(self, mock_open_call,
                                                       mock_default_call):
        with self.assertRaises(OSError):
            self.c.load(self.file)

        mock_default_call.assert_called_once_with()

    @mock.patch('doppelganger.config.Config._default')
    @mock.patch('pickle.load', side_effect=pickle.UnpicklingError)
    @mock.patch('builtins.open')
    def test_default_called__OSError_raised_if_UnpicklingError(
            self, mock_open_call, mock_load_call, mock_default_call
    ):
        with self.assertRaises(OSError):
            self.c.load(self.file)

        mock_default_call.assert_called_once_with()
