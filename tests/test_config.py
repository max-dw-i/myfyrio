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


import pickle
from unittest import TestCase, mock

from doppelganger import config

# pylint: disable=unused-argument,missing-class-docstring


class TestConfig(TestCase):

    def setUp(self):
        self.c = config.Config()

    def test_init_with_config_data_passed(self):
        conf_data = {'test_param': 'test_value'}
        c = config.Config(conf_data)

        self.assertDictEqual(conf_data, c.data)

    @mock.patch('doppelganger.config.Config.default')
    def test_init_without_config_data_passed(self, mock_def):
        config.Config()

        mock_def.assert_called_once_with()

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
        }

        self.assertEqual(self.c.data, DEFAULT_CONFIG)

    @mock.patch('pickle.dump')
    def test_save_into_config_p(self, mock_dump):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            self.c.save()

        mock_open.assert_called_once_with('config.p', 'wb')

    @mock.patch('pickle.dump')
    def test_save_dump_config_data(self, mock_dump):
        with mock.patch('builtins.open', mock.mock_open()):
            self.c.save()

        data = mock_dump.call_args[0][0]

        mock_dump.assert_called_once()
        self.assertDictEqual(data, self.c.data)

    @mock.patch('builtins.open', side_effect=OSError)
    def test_save_raise_OSError_if_open_raise_OSError(self, mock_open):
        with self.assertRaises(OSError):
            self.c.save()

    @mock.patch('pickle.load')
    def test_load_from_config_p(self, mock_load):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            self.c.load()

        mock_open.assert_called_once_with('config.p', 'rb')

    @mock.patch('pickle.load', return_value='test')
    @mock.patch('builtins.open')
    def test_load_assign_loaded_conf_to_attr_data(self, mock_open, mock_load):
        self.c.load()

        self.assertEqual('test', self.c.data)

    @mock.patch('doppelganger.config.Config.default')
    @mock.patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_assign_default_conf_if_FileNotFoundError(
            self, mock_open, mock_def
        ):
        self.c.load()

        mock_def.assert_called_once_with()

    @mock.patch('pickle.load')
    @mock.patch('builtins.open', side_effect=EOFError)
    def test_load_if_EOFError(self, mock_open, mock_dump):
        with self.assertRaises(OSError):
            self.c.load()

    @mock.patch('pickle.load')
    @mock.patch('builtins.open', side_effect=OSError)
    def test_load_if_OSError(self, mock_open, mock_dump):
        with self.assertRaises(OSError):
            self.c.load()

    @mock.patch('pickle.load', side_effect=pickle.UnpicklingError)
    @mock.patch('builtins.open')
    def test_load_if_UnpicklingError(self, mock_open, mock_dump):
        with self.assertRaises(OSError):
            self.c.load()
