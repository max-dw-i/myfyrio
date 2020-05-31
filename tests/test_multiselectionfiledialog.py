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

from PyQt5 import QtCore, QtWidgets, QtGui

from doppelganger.gui import multiselectionfiledialog

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


MS = 'doppelganger.gui.multiselectionfiledialog.'


# pylint: disable=missing-class-docstring


class TestMousePressFilter(TestCase):

    def setUp(self):
        self.mock_dialog = mock.Mock(
            spec=multiselectionfiledialog.MultiSelectionFileDialog
        )
        self.mock_dialog.listView = mock.Mock(spec=QtWidgets.QListView)
        self.mock_dialog.treeView = mock.Mock(spec=QtWidgets.QTreeView)

        with mock.patch('PyQt5.QtCore.QObject.__init__'):
            self.mock_filter = multiselectionfiledialog.MousePressFilter(
                self.mock_dialog
            )


class TestMousePressFilterMethodEventFilter(TestMousePressFilter):

    def setUp(self):
        super().setUp()

        self.obj = mock.Mock()
        self.event = mock.Mock(spec=QtGui.QMouseEvent)

    def test_return_False_if_not_MouseButtonPress_event(self):
        self.event.type.return_value = 'Not_MouseButtonPress_event'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_False_if_MouseButtonPress_event_and_not_LeftButton(self):
        self.event.type.return_value = QtCore.QEvent.MouseButtonPress
        self.event.button.return_value = 'Not_LeftButton'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_False_if_MouseButtonPress_ev__LeftButton__not_ctrl(self):
        self.event.type.return_value = QtCore.QEvent.MouseButtonPress
        self.event.button.return_value = QtCore.Qt.LeftButton
        self.mock_dialog._ctrl_pressed = True
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_False_if_MouseButtonPress_ev_and_LeftButton_and_ctrl(self):
        self.event.type.return_value = QtCore.QEvent.MouseButtonPress
        self.event.button.return_value = QtCore.Qt.LeftButton
        self.mock_dialog._ctrl_pressed = False
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_list_clearSelection_called_if_LeftButton_pressed_and_ctrl(self):
        self.event.type.return_value = QtCore.QEvent.MouseButtonPress
        self.event.button.return_value = QtCore.Qt.LeftButton
        self.mock_dialog._ctrl_pressed = False
        self.mock_filter.eventFilter(self.obj, self.event)

        self.mock_dialog.listView.clearSelection.assert_called_once_with()


class TestCtrlPressFilter(TestCase):

    def setUp(self):
        self.mock_dialog = mock.Mock(
            spec=multiselectionfiledialog.MultiSelectionFileDialog
        )

        with mock.patch('PyQt5.QtCore.QObject.__init__'):
            self.mock_filter = multiselectionfiledialog.CtrlPressFilter(
                self.mock_dialog
            )


class TestCtrlPressFilterMethodEventFilter(TestCtrlPressFilter):

    def setUp(self):
        super().setUp()

        self.obj = mock.Mock()
        self.event = mock.Mock(spec=QtGui.QKeyEvent)

    def test_return_False_if_not_KeyPress_event(self):
        self.event.type.return_value = 'Not_KeyPress_event'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_False_if_KeyPress_event_and_not_Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyPress
        self.event.key.return_value = 'Not_Ctrl_key'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_True_if_KeyPress_event_and_Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyPress
        self.event.key.return_value = QtCore.Qt.Key_Control
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertTrue(res)

    def test_assign_to_attr_ctrl_pressed_True_if_KeyPress_event_and_Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyPress
        self.event.key.return_value = QtCore.Qt.Key_Control
        self.mock_filter.eventFilter(self.obj, self.event)

        self.assertTrue(self.mock_dialog._ctrl_pressed)

    def test_return_False_if_KeyRelease_event_and_not_Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyRelease
        self.event.key.return_value = 'Not_Ctrl_key'
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(res)

    def test_return_True_if_KeyRelease_event_and_Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyRelease
        self.event.key.return_value = QtCore.Qt.Key_Control
        res = self.mock_filter.eventFilter(self.obj, self.event)

        self.assertTrue(res)

    def test_assign_to_attr_ctrl_pressed_False_if_KeyRelease_event__Ctrl(self):
        self.event.type.return_value = QtCore.QEvent.KeyRelease
        self.event.key.return_value = QtCore.Qt.Key_Control
        self.mock_filter.eventFilter(self.obj, self.event)

        self.assertFalse(self.mock_dialog._ctrl_pressed)


class TestMultiSelectDialog(TestCase):

    DIALOG = MS + 'MultiSelectionFileDialog.'

    def setUp(self):
        self.dialog = multiselectionfiledialog.MultiSelectionFileDialog()

#@skip('Slow test case')
class TestMultiSelectDialogMethodInit(TestMultiSelectDialog):

    def test_attr_ctrl_pressed_is_False(self):
        self.assertFalse(self.dialog._ctrl_pressed)

    def test_filemode_is_set_to_Directory(self):
        self.assertEqual(self.dialog.fileMode(),
                         QtWidgets.QFileDialog.Directory)

    def test_options(self):
        opt1 = QtWidgets.QFileDialog.DontUseNativeDialog
        opt2 = QtWidgets.QFileDialog.ReadOnly
        opts = opt1 | opt2
        self.assertEqual(self.dialog.options(), opts)

    def test_setViewModes_called(self):
        with mock.patch(self.DIALOG+'_setViewModes') as mock_modes_call:
            multiselectionfiledialog.MultiSelectionFileDialog()

        mock_modes_call.assert_called_once_with()

#@skip('Slow test case')
class TestMultiSelectDialogMethodSetViewModes(TestMultiSelectDialog):

    def setUp(self):
        super().setUp()

        self.mock_listView = mock.Mock(spec=QtWidgets.QListView)
        self.mock_treeView = mock.Mock(spec=QtWidgets.QTreeView)
        self.views = [self.mock_listView, self.mock_treeView]

    def test_findChild_called_with_qlistview_and_qtreeview_args(self):
        with mock.patch(self.DIALOG+'findChild') as mock_find_call:
            self.dialog._setViewModes()

        calls = [mock.call(QtWidgets.QListView, 'listView'),
                 mock.call(QtWidgets.QTreeView)]
        mock_find_call.assert_has_calls(calls)

    def test_setSelectionMode_called_for_both_views_with_multiselect_arg(self):
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
        listViewport = mock.Mock(spec=QtWidgets.QListView)
        treeViewport = mock.Mock(spec=QtWidgets.QTreeView)
        self.mock_listView.viewport.return_value = listViewport
        self.mock_treeView.viewport.return_value = treeViewport

        with mock.patch(self.DIALOG+'findChild', side_effect=self.views):
            with mock.patch(MS+'MousePressFilter',
                            side_effect=filters) as mock_filter_call:
                self.dialog._setViewModes()

        filter_calls = [mock.call(self.dialog), mock.call(self.dialog)]
        mock_filter_call.assert_has_calls(filter_calls)

        listViewport.installEventFilter.assert_called_once_with('listFilter')
        treeViewport.installEventFilter.assert_called_once_with('treeFilter')

    def test_ctrlFilter_installed_for_both_views(self):
        filters = 'listFilter', 'treeFilter'
        with mock.patch(self.DIALOG+'findChild', side_effect=self.views):
            with mock.patch(MS+'CtrlPressFilter',
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
