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

from doppelganger import pathsgroupbox

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=missing-class-docstring


class TestPathsGroupBox(TestCase):

    def setUp(self):
        self.w = pathsgroupbox.PathsGroupBox()
        self.items = ['path1', 'path2', 'path3']
        for item in self.items:
            self.w.pathsList.addItem(item)

    def test_addFolderBtn_initially_enabled(self):
        self.assertTrue(self.w.addFolderBtn.isEnabled())

    def test_delFolderBtn_initially_disabled(self):
        self.assertFalse(self.w.delFolderBtn.isEnabled())

    def test_paths(self):
        res = self.w.paths()

        self.assertListEqual(res, self.items)

    def test_delFolderBtn_enabled_disabled_if_select_unselect_item(self):
        self.w.pathsList.item(0).setSelected(True)
        self.assertTrue(self.w.delFolderBtn.isEnabled())

        self.w.pathsList.item(0).setSelected(False)
        self.assertFalse(self.w.delFolderBtn.isEnabled())

    def test_folder_from_file_dialog_added(self):
        PATCH_DIR = 'PyQt5.QtWidgets.QFileDialog.getExistingDirectory'
        item = 'path4'
        with mock.patch(PATCH_DIR, return_value=item):
            self.w.addPath()

        self.assertEqual(self.w.pathsList.count(), len(self.items)+1)
        self.assertEqual(self.w.pathsList.item(len(self.items)).text(), item)

    def test_selected_folder_deleted(self):
        self.w.pathsList.item(len(self.items)-1).setSelected(True)
        self.w.delPath()
        items_after_del = [self.w.pathsList.item(i).text()
                           for i in range(self.w.pathsList.count())]

        self.assertEqual(self.w.pathsList.count(), len(self.items)-1)
        self.assertListEqual(items_after_del, self.items[:-1])
