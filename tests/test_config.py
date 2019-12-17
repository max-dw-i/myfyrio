'''Copyright 2019 Maxim Shpak <maxim.shpak@posteo.uk>

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


import logging
import pickle
from unittest import TestCase, mock

from PyQt5 import QtWidgets

from doppelganger import config

# Configure a logger for testing purposes
logger = logging.getLogger('main')
logger.setLevel(logging.WARNING)
if not logger.handlers:
    nh = logging.NullHandler()
    logger.addHandler(nh)

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=unused-argument,missing-class-docstring


class TestConfig(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.DEFAULT_CONFIG_DATA = config.Config.DEFAULT_CONFIG_DATA.copy()

    def setUp(self):
        self.c = config.Config()

    def test_init_with_data_arg(self):
        data = {'test_par': 'test_val'}
        c = config.Config(data)

        self.assertDictEqual(data, c.data)

    def test_init_default_data_arg(self):
        self.assertDictEqual(self.DEFAULT_CONFIG_DATA, self.c.data)

    @mock.patch('doppelganger.config.pickle.dump')
    @mock.patch('doppelganger.config.open')
    def test_save(self, mock_open, mock_dump):
        self.c.save()

        mock_dump.assert_called_once()

    @mock.patch('doppelganger.config.pickle.dump')
    @mock.patch('doppelganger.config.open', side_effect=OSError)
    def test_save_if_OSError(self, mock_open, mock_dump):
        with self.assertRaises(OSError):
            with self.assertLogs('main.config', 'ERROR'):
                self.c.save()

    @mock.patch('doppelganger.config.pickle.load', return_value='test')
    @mock.patch('doppelganger.config.open')
    def test_load(self, mock_open, mock_dump):
        self.c.load()

        self.assertEqual('test', self.c.data)

    @mock.patch('doppelganger.config.pickle.load')
    @mock.patch('doppelganger.config.open', side_effect=FileNotFoundError)
    def test_load_if_FileNotFoundError(self, mock_open, mock_dump):
        self.c.load()

        self.assertEqual(self.c.DEFAULT_CONFIG_DATA, self.c.data)

    @mock.patch('doppelganger.config.pickle.load')
    @mock.patch('doppelganger.config.open', side_effect=EOFError)
    def test_load_if_EOFError(self, mock_open, mock_dump):
        with self.assertRaises(OSError):
            with self.assertLogs('main.config', 'ERROR'):
                self.c.load()

        self.assertEqual(self.DEFAULT_CONFIG_DATA, self.c.data)

    @mock.patch('doppelganger.config.pickle.load')
    @mock.patch('doppelganger.config.open', side_effect=OSError)
    def test_load_if_OSError(self, mock_open, mock_dump):
        with self.assertRaises(OSError):
            with self.assertLogs('main.config', 'ERROR'):
                self.c.load()

        self.assertEqual(self.DEFAULT_CONFIG_DATA, self.c.data)

    @mock.patch('doppelganger.config.pickle.load', side_effect=pickle.UnpicklingError)
    @mock.patch('doppelganger.config.open')
    def test_load_if_UnpicklingError(self, mock_open, mock_dump):
        with self.assertRaises(OSError):
            with self.assertLogs('main.config', 'ERROR'):
                self.c.load()

        self.assertEqual(self.DEFAULT_CONFIG_DATA, self.c.data)
