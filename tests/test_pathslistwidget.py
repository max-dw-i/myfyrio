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

from PyQt5 import QtCore, QtTest, QtWidgets

from myfyrio.gui import multiselectionfiledialog, pathslistwidget

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

PLW_MODULE = 'myfyrio.gui.pathslistwidget.'

# pylint: disable=missing-class-docstring


class TestPathsListWidget(TestCase):

    PLW = PLW_MODULE + 'PathsListWidget'

    def setUp(self):
        self.w = pathslistwidget.PathsListWidget()
        self.items = ['path1', 'path2']
        for item in self.items:
            self.w.addItem(item)


class TestPathsListWidgetMethodInit(TestPathsListWidget):

    def test_setSignals_called(self):
        with mock.patch(self.PLW+'._setSignals') as mock_signals_call:
            pathslistwidget.PathsListWidget()

        mock_signals_call.assert_called_once_with()


class TestPathsListWidgetMethodSetSignals(TestPathsListWidget):

    def test_model_rowsInserted_signal_connected_to_hasItems(self):
        mock_model = mock.Mock(spec=QtCore.QAbstractItemModel)
        with mock.patch(self.PLW+'.model', return_value=mock_model):
            self.w._setSignals()

        mock_model.rowsInserted.connect.assert_called_once_with(
            self.w._hasItems
        )

    def test_model_rowsRemoved_signal_connected_to_hasItems(self):
        mock_model = mock.Mock(spec=QtCore.QAbstractItemModel)
        with mock.patch(self.PLW+'.model', return_value=mock_model):
            self.w._setSignals()

        mock_model.rowsRemoved.connect.assert_called_once_with(
            self.w._hasItems
        )

    def test_itemSelectionChanged_signal_connected_to_hasSelectedItems(self):
        self.w.itemSelectionChanged = mock.Mock()
        self.w._setSignals()

        self.w.itemSelectionChanged.connect.assert_called_once_with(
            self.w._hasSelectedItems
        )


class TestPathsListWidgetMethodHasSelectedItems(TestPathsListWidget):

    def test_emit_hasSelection_signal_with_True_if_any_item_selected(self):
        self.w.item(0).setSelected(True)
        spy = QtTest.QSignalSpy(self.w.hasSelection)
        self.w._hasSelectedItems()

        self.assertEqual(len(spy), 1)
        self.assertTrue(spy[0][0])

    def test_emit_hasSelection_signal_with_False_if_no_item_selected(self):
        spy = QtTest.QSignalSpy(self.w.hasSelection)
        self.w._hasSelectedItems()

        self.assertEqual(len(spy), 1)
        self.assertFalse(spy[0][0])


class TestPathsListWidgetMethodHasItems(TestPathsListWidget):

    def test_emit_hasItems_signal_with_True_if_there_are_items(self):
        spy = QtTest.QSignalSpy(self.w.hasItems)
        self.w._hasItems()

        self.assertEqual(len(spy), 1)
        self.assertTrue(spy[0][0])

    def test_emit_hasItems_signal_with_False_if_there_is_no_items(self):
        for _ in range(self.w.count()):
            self.w.takeItem(0)
        spy = QtTest.QSignalSpy(self.w.hasItems)
        self.w._hasItems()

        self.assertEqual(len(spy), 1)
        self.assertFalse(spy[0][0])


class TestPathsListWidgetMethodPaths(TestPathsListWidget):

    def test_paths_return(self):
        res = self.w.paths()

        self.assertListEqual(res, self.items)


class TestPathsListWidgetMethodAddPath(TestPathsListWidget):

    DIALOG = 'myfyrio.gui.multiselectionfiledialog.MultiSelectionFileDialog'

    def setUp(self):
        super().setUp()

        self.mock_dialog = mock.Mock(
            multiselectionfiledialog.MultiSelectionFileDialog
        )

    def _paths(self):
        return [self.w.item(i).text() for i in range(self.w.count())]

    def test_MultiSelectionFileDialog_called(self):
        with mock.patch(self.DIALOG) as mock_dialog_call:
            self.w.addPath()

        mock_dialog_call.assert_called_once_with(self.w, 'Open Folders', '')

    def test_paths_not_changed_if_nothing_selected(self):
        self.mock_dialog.exec.return_value = 0
        with mock.patch(self.DIALOG, return_value=self.mock_dialog):
            self.w.addPath()

        self.assertListEqual(self._paths(), self.items)

    def test_paths_not_changed_if_selected_already_added(self):
        self.mock_dialog.exec.return_value = 1
        self.mock_dialog.selectedFiles.return_value = self.items[:1]
        with mock.patch(self.DIALOG, return_value=self.mock_dialog):
            self.w.addPath()

        self.assertListEqual(self._paths(), self.items)

    def test_paths_changed_if_selected_not_already_added(self):
        self.mock_dialog.exec.return_value = 1
        self.mock_dialog.selectedFiles.return_value = ['path3']
        with mock.patch(self.DIALOG, return_value=self.mock_dialog):
            self.w.addPath()

        self.assertListEqual(self._paths(), self.items + ['path3'])


class TestPathsListWidgetMethodDelPath(TestPathsListWidget):

    def test_selected_folder_deleted(self):
        self.w.item(len(self.items)-1).setSelected(True) # select second item
        self.w.delPath()
        items_after_del = [self.w.item(i).text()
                           for i in range(self.w.count())]

        self.assertListEqual(items_after_del, self.items[:-1])

    def test_nothing_deleted_if_nothing_selected(self):
        self.w.delPath()
        items_after_del_run = [self.w.item(i).text()
                               for i in range(self.w.count())]

        self.assertListEqual(items_after_del_run, self.items)
