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

import pathlib
import sys
from unittest import TestCase, mock

from PyQt5 import QtCore

from myfyrio import resources

RESOURCES = 'myfyrio.resources.'

# pylint: disable=missing-class-docstring,no-member


class TestUI(TestCase):

    def setUp(self):
        self.resource = resources.UI.ABOUT


class TestUIValues(TestUI):

    def test_ABOUT_value(self):
        self.assertEqual(resources.UI.ABOUT.value,
                         'myfyrio/static/ui/aboutwindow.ui')

    def test_MAIN_value(self):
        self.assertEqual(resources.UI.MAIN.value,
                         'myfyrio/static/ui/mainwindow.ui')

    def test_PREFERENCES_value(self):
        self.assertEqual(resources.UI.PREFERENCES.value,
                         'myfyrio/static/ui/preferenceswindow.ui')


class TestUIMethodNonfrozen(TestUI):

    def setUp(self):
        super().setUp()

        self.real_file = resources.__file__
        resources.__file__ = '/project_folder/myfyrio/resources.py'

    def tearDown(self):
        resources.__file__ = self.real_file

    def test_return_correct_nonfrozen_path(self):
        res = self.resource.nonfrozen()

        self.assertEqual(
            res, '/project_folder/' + self.resource.value
        )


class TestUIMethodFrozen(TestUI):

    def setUp(self):
        super().setUp()

        self.mock_QFile = mock.Mock(spec=QtCore.QFile)
        self.mock_QFile.readAll.return_value = 1

    def test_QFile_called_with_proper_arg(self):
        with mock.patch('PyQt5.QtCore.QFile') as mock_QFile_call:
            self.resource.frozen()

        mock_QFile_call.assert_called_once_with(':/' + self.resource.value)

    def test_QFile_opened_for_reading(self):
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            self.resource.frozen()

        self.mock_QFile.open.assert_called_once_with(QtCore.QIODevice.ReadOnly)

    def test_return_data_read_from_QFile_as_BytesIO_obj(self):
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            res = self.resource.frozen()

        self.assertEqual(res.getvalue(), bytes(1))

    def test_QFile_closed(self):
        with mock.patch('PyQt5.QtCore.QFile', return_value=self.mock_QFile):
            self.resource.frozen()

        self.mock_QFile.close.assert_called_once_with()


class TestUIMethodGet(TestUI):

    def test_frozen_called_if_app_is_frozen(self):
        setattr(sys, 'frozen', True)
        with mock.patch(RESOURCES+'UI.frozen') as mock_frozen_call:
            self.resource.get()
        delattr(sys, 'frozen') # clean our garbage

        mock_frozen_call.assert_called_once_with()

    def test_nonfrozen_called_if_app_is_not_frozen(self):
        with mock.patch(RESOURCES+'UI.nonfrozen') as mock_nonfrozen_call:
            self.resource.get()

        mock_nonfrozen_call.assert_called_once_with()


class TestImage(TestCase):

    def setUp(self):
        self.resource = resources.Image.ICON


class TestImageValues(TestImage):

    def test_ICON_value(self):
        self.assertEqual(resources.Image.ICON.value,
                         'myfyrio/static/images/icon.png')

    def test_ERR_IMG_value(self):
        self.assertEqual(resources.Image.ERR_IMG.value,
                         'myfyrio/static/images/error.png')


class TestImageMethodNonfrozen(TestImage):

    def setUp(self):
        super().setUp()

        self.real_file = resources.__file__
        resources.__file__ = '/project_folder/myfyrio/resources.py'

    def tearDown(self):
        resources.__file__ = self.real_file

    def test_return_correct_nonfrozen_path(self):
        res = self.resource.nonfrozen()

        self.assertEqual(
            res, '/project_folder/' + self.resource.value
        )


class TestImageMethodFrozen(TestImage):

    def test_return_proper_path_in_Qt_resource_system_format(self):
        res = self.resource.frozen()

        self.assertEqual(res, ':/' + self.resource.value)


class TestImageMethodGet(TestImage):

    def test_frozen_called_if_app_is_frozen(self):
        setattr(sys, 'frozen', True)
        with mock.patch(RESOURCES+'Image.frozen') as mock_frozen_call:
            self.resource.get()
        delattr(sys, 'frozen') # clean our garbage

        mock_frozen_call.assert_called_once_with()

    def test_nonfrozen_called_if_app_is_not_frozen(self):
        with mock.patch(RESOURCES+'Image.nonfrozen') as mock_nonfrozen_call:
            self.resource.get()

        mock_nonfrozen_call.assert_called_once_with()


class TestConfig(TestCase):

    def setUp(self):
        self.resource = resources.Config.CONFIG


class TestConfigValues(TestConfig):

    def test_CONFIG_value(self):
        self.assertEqual(resources.Config.CONFIG.value, 'config.p')


class TestConfigMethodNonfrozen(TestConfig):

    def setUp(self):
        super().setUp()

        self.real_file = resources.__file__
        resources.__file__ = '/project_folder/myfyrio/resources.py'

    def tearDown(self):
        resources.__file__ = self.real_file

    def test_return_correct_nonfrozen_path(self):
        res = self.resource.nonfrozen()

        self.assertEqual(
            res, '/project_folder/' + self.resource.value
        )


class TestConfigMethodFrozen(TestConfig):

    def setUp(self):
        super().setUp()

        self.real_file = sys.executable
        self.real_platform = sys.platform

    def tearDown(self):
        sys.executable = self.real_file
        sys.platform = self.real_platform
        resources.USER = False

    def test_return_super_path_if_not_USER(self):
        resources.USER = False
        with mock.patch(RESOURCES+'Resource.frozen', return_value='superpath'):
            res = self.resource.frozen()

        self.assertEqual(res, 'superpath')

    def test_return_AppData_path_if_USER_and_Win(self):
        resources.USER = True
        sys.platform = 'win32'
        res = self.resource.frozen()

        expected = str(pathlib.Path.home().joinpath(
            'AppData', 'Local', 'Myfyrio', resources.Config.CONFIG.value
        ))
        self.assertEqual(res, expected)

    def test_home_path_if_USER_and_Linux(self):
        resources.USER = True
        sys.platform = 'linux'
        res = self.resource.frozen()

        expected = str(pathlib.Path.home().joinpath(
            '.myfyrio', resources.Config.CONFIG.value
        ))
        self.assertEqual(res, expected)


class TestConfigMethodGet(TestConfig):

    def test_frozen_called_if_app_is_frozen(self):
        setattr(sys, 'frozen', True)
        with mock.patch(RESOURCES+'Config.frozen') as mock_frozen_call:
            self.resource.get()
        delattr(sys, 'frozen') # clean our garbage

        mock_frozen_call.assert_called_once_with()

    def test_nonfrozen_called_if_app_is_not_frozen(self):
        with mock.patch(RESOURCES+'Config.nonfrozen') as mock_nonfrozen_call:
            self.resource.get()

        mock_nonfrozen_call.assert_called_once_with()


class TestCache(TestCase):

    def setUp(self):
        self.resource = resources.Cache.CACHE


class TestCacheValues(TestCache):

    def test_CACHE_value(self):
        self.assertEqual(resources.Cache.CACHE.value, 'cache.p')


class TestCacheMethodNonfrozen(TestCache):

    def setUp(self):
        super().setUp()

        self.real_file = resources.__file__
        resources.__file__ = '/project_folder/myfyrio/resources.py'

    def tearDown(self):
        resources.__file__ = self.real_file

    def test_return_correct_nonfrozen_path(self):
        res = self.resource.nonfrozen()

        self.assertEqual(
            res, '/project_folder/' + self.resource.value
        )


class TestCacheMethodFrozen(TestCache):

    def setUp(self):
        super().setUp()

        self.real_file = sys.executable
        self.real_platform = sys.platform

    def tearDown(self):
        sys.executable = self.real_file
        sys.platform = self.real_platform
        resources.USER = False

    def test_return_super_path_if_not_USER(self):
        resources.USER = False
        with mock.patch(RESOURCES+'Resource.frozen', return_value='superpath'):
            res = self.resource.frozen()

        self.assertEqual(res, 'superpath')

    def test_return_AppData_path_if_USER_and_Win(self):
        resources.USER = True
        sys.platform = 'win32'
        res = self.resource.frozen()

        expected = str(pathlib.Path.home().joinpath(
            'AppData', 'Local', 'Myfyrio', resources.Cache.CACHE.value
        ))
        self.assertEqual(res, expected)

    def test_home_path_if_USER_and_Linux(self):
        resources.USER = True
        sys.platform = 'linux'
        res = self.resource.frozen()

        expected = str(pathlib.Path.home().joinpath(
            '.myfyrio', resources.Cache.CACHE.value
        ))
        self.assertEqual(res, expected)


class TestCacheMethodGet(TestCache):

    def test_frozen_called_if_app_is_frozen(self):
        setattr(sys, 'frozen', True)
        with mock.patch(RESOURCES+'Cache.frozen') as mock_frozen_call:
            self.resource.get()
        delattr(sys, 'frozen') # clean our garbage

        mock_frozen_call.assert_called_once_with()

    def test_nonfrozen_called_if_app_is_not_frozen(self):
        with mock.patch(RESOURCES+'Cache.nonfrozen') as mock_nonfrozen_call:
            self.resource.get()

        mock_nonfrozen_call.assert_called_once_with()


class TestLog(TestCase):

    def setUp(self):
        self.resource = resources.Log.ERROR


class TestLogValues(TestLog):

    def test_ERROR_value(self):
        self.assertEqual(resources.Log.ERROR.value, 'errors.log')


class TestLogMethodNonfrozen(TestConfig):

    def setUp(self):
        super().setUp()

        self.real_file = resources.__file__
        resources.__file__ = '/project_folder/myfyrio/resources.py'

    def tearDown(self):
        resources.__file__ = self.real_file

    def test_return_correct_nonfrozen_path(self):
        res = self.resource.nonfrozen()

        self.assertEqual(
            res, '/project_folder/' + self.resource.value
        )


class TestLogMethodFrozen(TestLog):

    def setUp(self):
        super().setUp()

        self.real_file = sys.executable
        self.real_platform = sys.platform

    def tearDown(self):
        sys.executable = self.real_file
        sys.platform = self.real_platform
        resources.USER = False

    def test_return_super_path_if_not_USER(self):
        resources.USER = False
        with mock.patch(RESOURCES+'Resource.frozen', return_value='superpath'):
            res = self.resource.frozen()

        self.assertEqual(res, 'superpath')

    def test_return_AppData_path_if_USER_and_Win(self):
        resources.USER = True
        sys.platform = 'win32'
        res = self.resource.frozen()

        expected = str(pathlib.Path.home().joinpath(
            'AppData', 'Local', 'Myfyrio', resources.Log.ERROR.value
        ))
        self.assertEqual(res, expected)

    def test_home_path_if_USER_and_Linux(self):
        resources.USER = True
        sys.platform = 'linux'
        res = self.resource.frozen()

        expected = str(pathlib.Path.home().joinpath(
            '.myfyrio', resources.Log.ERROR.value
        ))
        self.assertEqual(res, expected)


class TestLogMethodGet(TestLog):

    def test_frozen_called_if_app_is_frozen(self):
        setattr(sys, 'frozen', True)
        with mock.patch(RESOURCES+'Log.frozen') as mock_frozen_call:
            self.resource.get()
        delattr(sys, 'frozen') # clean our garbage

        mock_frozen_call.assert_called_once_with()

    def test_nonfrozen_called_if_app_is_not_frozen(self):
        with mock.patch(RESOURCES+'Log.nonfrozen') as mock_nonfrozen_call:
            self.resource.get()

        mock_nonfrozen_call.assert_called_once_with()
