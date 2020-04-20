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

from doppelganger import cache


# pylint: disable=unused-argument,missing-class-docstring


class TestClassCache(TestCase):

    def setUp(self):
        self.c = cache.Cache()


class TestInitMethod(TestClassCache):

    def test_assign_empty_dict_to_attr_data(self):
        self.assertDictEqual(self.c._data, {})


class TestMethodLoad(TestClassCache):

    CACHE_FILE = 'cache_file'

    @mock.patch('pickle.load')
    def test_args_open_called_with(self, mock_load):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            self.c.load(self.CACHE_FILE)

        mock_open.assert_called_once_with(self.CACHE_FILE, 'rb')

    @mock.patch('pickle.load', return_value='hashes')
    def test_assign_loaded_hashes_to_attr_data(self, mock_load):
        with mock.patch('builtins.open', mock.mock_open()):
            self.c.load(self.CACHE_FILE)

        self.assertEqual(self.c._data, 'hashes')

    @mock.patch('builtins.open', side_effect=FileNotFoundError)
    def test_raise_FileNotFoundError_if_FileNotFoundError(self, mock_open):
        with self.assertRaises(FileNotFoundError):
            self.c.load(self.CACHE_FILE)

    @mock.patch('builtins.open', side_effect=EOFError)
    def test_raise_EOFError_if_open_raise_EOFError(self, mock_open):
        with self.assertRaises(EOFError):
            self.c.load(self.CACHE_FILE)

    @mock.patch('builtins.open', side_effect=OSError)
    def test_raise_OSError_if_open_raise_OSError(self, mock_open):
        with self.assertRaises(OSError):
            self.c.load(self.CACHE_FILE)


class TestMethodSave(TestClassCache):
    '''!!! BE AWARE WHEN CHANGE THESE TESTS. IF THERE'S
    ALREADY POPULATED CACHE FILE AND YOU DON'T PATCH OPEN()
    AND DUMP(), YOU'LL REWRITE THE FILE
    '''

    CACHE_FILE = 'cache_file'

    def setUp(self):
        super().setUp()

        self.cache = {'path1': 'hash1'}
        self.c._data = self.cache

    @mock.patch('pickle.dump')
    def test_args_open_called_with(self, mock_dump):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            self.c.save(self.CACHE_FILE)

        mock_open.assert_called_once_with(self.CACHE_FILE, 'wb')

    @mock.patch('pickle.dump')
    def test_dump_called_with_cache_arg(self, mock_dump):
        with mock.patch('builtins.open', mock.mock_open()):
            self.c.save(self.CACHE_FILE)

        self.assertEqual(mock_dump.call_args[0][0], self.cache)

    @mock.patch('builtins.open', side_effect=OSError)
    def test_raise_OSError_if_open_raise_OSError(self, mock_open):
        with self.assertRaises(OSError):
            self.c.save(self.CACHE_FILE)
