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

from PyQt5 import QtCore, QtWidgets

from doppelganger.gui import pathsgroupbox

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


PGB = 'doppelganger.gui.pathsgroupbox.'


# pylint: disable=missing-class-docstring


class TestMousePressFilter(TestCase):

    def setUp(self):
        self.mock_dialog = mock.Mock()
        self.mock_dialog.listView = mock.Mock()
        self.mock_dialog.treeView = mock.Mock()

        with mock.patch('PyQt5.QtCore.QObject.__init__'):
            self.mock_filter = pathsgroupbox.MousePressFilter(self.mock_dialog)


class TestMousePressFilterMethodEventFilter(TestMousePressFilter):

    def setUp(self):
        super().setUp()

        self.obj = mock.Mock()
        self.event = mock.Mock()

    def test_return_False_if_not_MouseButtonPress_event(self):
        self.event.type.return_value = 'Not_MouseButtonPress_event'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_False_if_MouseButtonPress_event__not_LeftButton(self):
        self.event.type.return_value = QtCore.QEvent.MouseButtonPress
        self.event.button.return_value = 'Not_LeftButton'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_False_if_MouseButtonPress_ev__LeftButton__not_ctrl(self):
        self.event.type.return_value = QtCore.QEvent.MouseButtonPress
        self.event.button.return_value = QtCore.Qt.LeftButton
        self.mock_dialog.ctrl_pressed = True
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_False_if_MouseButtonPress_ev__LeftButton__ctrl(self):
        self.event.type.return_value = QtCore.QEvent.MouseButtonPress
        self.event.button.return_value = QtCore.Qt.LeftButton
        self.mock_dialog.ctrl_pressed = False
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_list_clearSelection_called_if_LeftButton_pressed__ctrl(self):
        self.event.type.return_value = QtCore.QEvent.MouseButtonPress
        self.event.button.return_value = QtCore.Qt.LeftButton
        self.mock_dialog.ctrl_pressed = False
        self.mock_filter.eventFilter(self.obj, self.event)

        self.mock_dialog.listView.clearSelection.assert_called_once_with()


class TestCtrlPressFilter(TestCase):

    def setUp(self):
        self.mock_dialog = mock.Mock()

        with mock.patch('PyQt5.QtCore.QObject.__init__'):
            self.mock_filter = pathsgroupbox.CtrlPressFilter(self.mock_dialog)


class TestCtrlPressFilterMethodEventFilter(TestCtrlPressFilter):

    def setUp(self):
        super().setUp()

        self.obj = mock.Mock()
        self.event = mock.Mock()

    def test_return_False_if_not_KeyPress_event(self):
        self.event.type.return_value = 'Not_KeyPress_event'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_False_if_KeyPress_event__not_Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyPress
        self.event.key.return_value = 'Not_Ctrl_key'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_True_if_KeyPress_event__Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyPress
        self.event.key.return_value = QtCore.Qt.Key_Control
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertTrue(res)

    def test_assign_to_attr_ctrl_pressed_True_if_KeyPress_event__Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyPress
        self.event.key.return_value = QtCore.Qt.Key_Control
        self.mock_filter.eventFilter(self.obj, self.event)

        self.assertTrue(self.mock_dialog.ctrl_pressed)

    def test_return_False_if_KeyRelease_event__not_Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyRelease
        self.event.key.return_value = 'Not_Ctrl_key'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_True_if_KeyRelease_event__Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyRelease
        self.event.key.return_value = QtCore.Qt.Key_Control
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertTrue(res)

    def test_assign_to_attr_ctrl_pressed_False_if_KeyRelease_event__Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyRelease
        self.event.key.return_value = QtCore.Qt.Key_Control
        self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(self.mock_dialog.ctrl_pressed)


class TestMultiSelectDialog(TestCase):

    MFD = PGB + 'MultiSelectionFileDialog.'

    def setUp(self):
        self.dialog = pathsgroupbox.MultiSelectionFileDialog()

#@skip('Slow test case')
class TestMultiSelectDialogMethodInit(TestMultiSelectDialog):

    def test_attr_ctrl_pressed_is_False(self):
        self.assertFalse(self.dialog.ctrl_pressed)

    def test_filemode_is_set_to_Directory(self):
        self.assertEqual(self.dialog.fileMode(),
                         QtWidgets.QFileDialog.Directory)

    def test_options(self):
        opt1 = QtWidgets.QFileDialog.DontUseNativeDialog
        opt2 = QtWidgets.QFileDialog.ReadOnly
        opts = opt1 | opt2
        self.assertEqual(self.dialog.options(), opts)

    def test_setViewModes_called(self):
        with mock.patch(self.MFD+'_setViewModes') as mock_modes_call:
            pathsgroupbox.MultiSelectionFileDialog()

        mock_modes_call.assert_called_once_with()

#@skip('Slow test case')
class TestMultiSelectDialogMethodSetViewModes(TestMultiSelectDialog):

    DIALOG = PGB + 'MultiSelectionFileDialog.'

    def setUp(self):
        super().setUp()

        self.mock_listView = mock.Mock()
        self.mock_treeView = mock.Mock()
        self.views = [self.mock_listView, self.mock_treeView]

    def test_findChild_called_with_proper_args(self):
        with mock.patch(self.DIALOG+'findChild') as mock_find_call:
            self.dialog._setViewModes()

        calls = [mock.call(QtWidgets.QListView, 'listView'),
                 mock.call(QtWidgets.QTreeView)]
        mock_find_call.assert_has_calls(calls)

    def test_setSelectionMode_called_for_both_views_with_multi_arg(self):
        with mock.patch(self.DIALOG+'findChild', side_effect=self.views):
            self.dialog._setViewModes()

        self.mock_listView.setSelectionMode.assert_called_once_with(
            QtWidgets.QAbstractItemView.MultiSelection
        )
        self.mock_treeView.setSelectionMode.assert_called_once_with(
            QtWidgets.QAbstractItemView.MultiSelection
        )

    def test_mouseFilter_installed_for_both_views(self):
        filters = 'listFilter', 'treeFilter'
        listViewport, treeViewport = mock.Mock(), mock.Mock()
        self.mock_listView.viewport.return_value = listViewport
        self.mock_treeView.viewport.return_value = treeViewport

        with mock.patch(self.DIALOG+'findChild', side_effect=self.views):
            with mock.patch(PGB+'MousePressFilter',
                            side_effect=filters) as mock_filter_call:
                self.dialog._setViewModes()

        filter_calls = [mock.call(self.dialog), mock.call(self.dialog)]
        mock_filter_call.assert_has_calls(filter_calls)

        listViewport.installEventFilter.assert_called_once_with('listFilter')
        treeViewport.installEventFilter.assert_called_once_with('treeFilter')

    def test_ctrlFilter_installed_for_both_views(self):
        filters = 'listFilter', 'treeFilter'
        with mock.patch(self.DIALOG+'findChild', side_effect=self.views):
            with mock.patch(PGB+'CtrlPressFilter',
                            side_effect=filters) as mock_filter_call:
                self.dialog._setViewModes()

        filter_calls = [mock.call(self.dialog), mock.call(self.dialog)]
        mock_filter_call.assert_has_calls(filter_calls)

        self.mock_listView.installEventFilter.assert_called_once_with(
            'listFilter'
        )
        self.mock_treeView.installEventFilter.assert_called_once_with(
            'treeFilter'
        )


class TestPathsGroupBox(TestCase):

    def setUp(self):
        self.w = pathsgroupbox.PathsGroupBox()
        self.items = ['path1', 'path2', 'path3']
        for item in self.items:
            self.w.pathsList.addItem(item)


class TestPathsGroupBoxMethodInit(TestPathsGroupBox):

    def test_addFolderBtn_initially_enabled(self):
        self.assertTrue(self.w.addFolderBtn.isEnabled())

    def test_delFolderBtn_initially_disabled(self):
        self.assertFalse(self.w.delFolderBtn.isEnabled())


class TestPathsGroupBoxMethodPaths(TestPathsGroupBox):

    def test_paths_return(self):
        res = self.w.paths()

        self.assertListEqual(res, self.items)


class TestPathsGroupBoxMethodEnableDelFolderBtn(TestPathsGroupBox):

    def test_delFolderBtn_enabled_if_select_item(self):
        self.w.pathsList.item(0).setSelected(True)
        self.assertTrue(self.w.delFolderBtn.isEnabled())

    def test_delFolderBtn_disabled_if_unselect_item(self):
        self.w.pathsList.item(0).setSelected(False)
        self.assertFalse(self.w.delFolderBtn.isEnabled())


class TestPathsGroupBoxMethodAddPath(TestPathsGroupBox):

    PATCH_DIALOG = PGB + 'MultiSelectionFileDialog'

    def setUp(self):
        super().setUp()

        self.mock_dialog = mock.Mock()

    def _paths(self):
        return [self.w.pathsList.item(i).text()
                for i in range(self.w.pathsList.count())]

    def test_MultiSelectionFileDialog_called(self):
        with mock.patch(self.PATCH_DIALOG) as mock_dialog_call:
            self.w.addPath()

        mock_dialog_call.assert_called_once_with(self.w, 'Open Folders', '')

    def test_paths_not_changed_if_nothing_selected(self):
        self.mock_dialog.exec.return_value = 0
        with mock.patch(self.PATCH_DIALOG, return_value=self.mock_dialog):
            self.w.addPath()

        self.assertListEqual(self._paths(), self.items)

    def test_paths_not_changed_if_selected_already_added(self):
        self.mock_dialog.exec.return_value = 1
        self.mock_dialog.selectedFiles.return_value = self.items[:1]
        with mock.patch(self.PATCH_DIALOG, return_value=self.mock_dialog):
            self.w.addPath()

        self.assertListEqual(self._paths(), self.items)

    def test_paths_changed_if_selected_not_already_added(self):
        self.mock_dialog.exec.return_value = 1
        self.mock_dialog.selectedFiles.return_value = ['path4']
        with mock.patch(self.PATCH_DIALOG, return_value=self.mock_dialog):
            self.w.addPath()

        self.assertListEqual(self._paths(), self.items + ['path4'])


class TestPathsGroupBoxMethodDelPath(TestPathsGroupBox):

    def test_selected_folder_deleted(self):
        self.w.pathsList.item(len(self.items)-1).setSelected(True)
        self.w.delPath()
        items_after_del = [self.w.pathsList.item(i).text()
                           for i in range(self.w.pathsList.count())]

        self.assertEqual(self.w.pathsList.count(), len(self.items)-1)
        self.assertListEqual(items_after_del, self.items[:-1])
