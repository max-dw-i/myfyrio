'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

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


import logging
from unittest import TestCase, mock

from PyQt5 import QtCore, QtTest, QtWidgets

from myfyrio import config
from myfyrio.gui import duplicatewidget, imagegroupwidget, imageviewwidget

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

VIEW_MODULE = 'myfyrio.gui.imageviewwidget.'

# pylint: disable=missing-class-docstring


class TestImageViewWidget(TestCase):

    IVW = VIEW_MODULE + 'ImageViewWidget.'

    def setUp(self):
        self.w = imageviewwidget.ImageViewWidget()


class TestImageViewWidgetMethodInit(TestImageViewWidget):

    def test_default_values(self):
        self.assertIsNone(self.w.conf)
        self.assertListEqual(self.w.widgets, [])
        self.assertListEqual(self.w._errors, [])

    def test_layout(self):
        margins = self.w._layout.contentsMargins()
        self.assertEqual(margins.top(), 9)
        self.assertEqual(margins.right(), 9)
        self.assertEqual(margins.bottom(), 9)
        self.assertEqual(margins.left(), 9)

        self.assertEqual(self.w._layout.spacing(), 10)
        self.assertIsInstance(self.w._layout, QtWidgets.QVBoxLayout)
        self.assertEqual(self.w._layout.sizeConstraint(),
                         QtWidgets.QLayout.SetFixedSize)


class TestImageViewWidgetMethodAddGroup(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.w.widgets = ['image_group']

        self.image_group = (0, ['image'])
        self.empty_image_group = (0, [])

    def test_render_called_if_image_groups_found(self):
        with mock.patch(self.IVW+'_render') as mock_render_call:
            self.w.addGroup(self.image_group)

        mock_render_call.assert_called_once_with(self.image_group)

    def test_logging_if_render_raise_Exception(self):
        with mock.patch(self.IVW+'_render', side_effect=Exception):
            with self.assertLogs('main.imageviewwidget', 'ERROR'):
                self.w.addGroup(self.image_group)

    def test_emit_error_signal_with_err_msg_if_render_raise_Exception(self):
        spy = QtTest.QSignalSpy(self.w.error)
        with mock.patch(self.IVW+'_render', side_effect=Exception('Error')):
            self.w.addGroup(self.image_group)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 'Error')

    def test_emit_interrupted_signal_if_render_raise_Exception(self):
        spy = QtTest.QSignalSpy(self.w.interrupted)
        with mock.patch(self.IVW+'_render', side_effect=Exception):
            self.w.addGroup(self.image_group)

        self.assertEqual(len(spy), 1)

    def test_render_not_called_if_empty_image_groups(self):
        with mock.patch(self.IVW+'_render') as mock_render_call:
            self.w.addGroup(self.empty_image_group)

        mock_render_call.assert_not_called()

    def test_finished_signal_emitted_ifempty__image_group(self):
        spy = QtTest.QSignalSpy(self.w.finished)
        self.w.addGroup(self.empty_image_group)

        self.assertEqual(len(spy), 1)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_QMessageBox_not_called_if_empty_image_group__no_widgets(self,
                                                                     mock_box):
        self.w.widgets = []
        self.w.addGroup(self.empty_image_group)

        mock_box.assert_called_once()

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_QMessageBox_called_if_empty_image_group__widgets_found(self,
                                                                    mock_box):

        self.w.addGroup(self.empty_image_group)

        mock_box.assert_not_called()


class TestImageViewWidgetMethodRender(TestImageViewWidget):

    IGW = 'myfyrio.gui.imagegroupwidget.ImageGroupWidget'

    def setUp(self):
        super().setUp()

        self.mock_conf = mock.Mock(spec=config.Config)
        self.w.conf = self.mock_conf

        self.w._layout = mock.Mock(spec=QtWidgets.QVBoxLayout)

        self.image_group = (0, ['image1', 'image2'])
        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.mock_groupW.widgets = []

    def test_raise_ValueError_if_attr_conf_is_None(self):
        self.w.conf = None
        with self.assertRaises(ValueError):
            self.w._render(self.image_group)

    def test_call_ImageGroupWidget_with_conf_arg_if_new_group(self):
        with mock.patch(self.IGW, return_value=self.mock_groupW) as mock_widg:
            self.w._render(self.image_group)

        mock_widg.assert_called_once_with(self.mock_conf)

    def test_ImageGroupWidget_error_connect_to_attr_errors_append_if_new(self):
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_group)

        self.mock_groupW.error.connect(self.w._errors.append)

    def test_ImageGroupWidget_added_to_layout_if_new_group(self):
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_group)

        self.w._layout.addWidget.assert_called_once_with(self.mock_groupW)

    def test_ImageGroupWidget_added_to_attr_widgets_if_new_group(self):
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_group)

        self.assertListEqual(self.w.widgets, [self.mock_groupW])

    def test_new_DuplicateWidgets_added_if_new_group(self):
        mock_duplW1 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        mock_duplW2 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_groupW.addDuplicateWidget.side_effect = [mock_duplW1,
                                                           mock_duplW2]
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_group)

        calls = [mock.call('image1'), mock.call('image2')]
        self.mock_groupW.addDuplicateWidget.assert_has_calls(calls)

    def test_new_DuplicateWidgets_connected_to_hasSelected_if_new_group(self):
        mock_duplW1 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        mock_duplW2 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_groupW.addDuplicateWidget.side_effect = [mock_duplW1,
                                                           mock_duplW2]
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_group)

        mock_duplW1.clicked.connect.assert_called_once_with(
            self.w._hasSelected
        )
        mock_duplW2.clicked.connect.assert_called_once_with(
            self.w._hasSelected
        )

    def test_new_DuplicateWidget_added_to_existing_group(self):
        self.w.widgets = [self.mock_groupW]
        self.image_group[1].append('image3')
        self.w._render(self.image_group)

        self.mock_groupW.addDuplicateWidget.assert_called_once_with('image3')

    def test_new_DuplicateWidget_connected_to_hasSelected_if_existing(self):
        self.w.widgets = [self.mock_groupW]
        self.image_group[1].append('image3')
        mock_duplW = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_groupW.addDuplicateWidget.return_value = mock_duplW
        self.w._render(self.image_group)

        mock_duplW.clicked.connect.assert_called_once_with(
            self.w._hasSelected
        )


class TestImageViewWidgetMethodHasSelected(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w.widgets = [self.mock_groupW]

    def test_selected_signal_with_True_emitted_if_there_are_selected(self):
        self.mock_groupW.hasSelected.return_value = True
        spy = QtTest.QSignalSpy(self.w.selected)
        self.w._hasSelected()

        self.assertEqual(len(spy), 1)
        self.assertTrue(spy[0][0])

    def test_selected_signal_with_False_emitted_if_there_are_no_selected(self):
        self.mock_groupW.hasSelected.return_value = False
        spy = QtTest.QSignalSpy(self.w.selected)
        self.w._hasSelected()

        self.assertEqual(len(spy), 1)
        self.assertFalse(spy[0][0])


class TestImageViewWidgetMethodClear(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock()
        self.w.widgets = [self.mock_groupW]

    def test_threadpool_clear_called(self):
        threadpool = mock.Mock(spec=QtCore.QThreadPool)
        with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance',
                        return_value=threadpool):
            self.w.clear()

        threadpool.clear.assert_called_once_with()

    def test_threadpool_waitForDone_called(self):
        threadpool = mock.Mock(spec=QtCore.QThreadPool)
        with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance',
                        return_value=threadpool):
            self.w.clear()

        threadpool.waitForDone.assert_called_once_with()

    def test_deleteLater_called(self):
        self.w.clear()

        self.mock_groupW.deleteLater.assert_called_once_with()

    def test_clear_widgets_attr(self):
        self.w.clear()

        self.assertListEqual(self.w.widgets, [])


class TestImageViewWidgetMethodCallOnSelected(TestImageViewWidget):

    PATCH_ERRN = 'myfyrio.gui.errornotifier.'

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w.widgets = [self.mock_groupW]

        self.mock_func = mock.Mock()
        self.args = 'arg'
        self.kwargs = 'kwarg'

    def test_passed_func_called_with_ImageGroupWidget__args_and_kwargs(self):
        self.w._callOnSelected(self.mock_func, self.args, kwarg=self.kwargs)

        self.mock_func.assert_called_once_with(
            self.mock_groupW, self.args, kwarg=self.kwargs
        )

    def test_errorMessage_called_with_attr_errors_arg(self):
        self.w._errors = ['Error']
        with mock.patch(self.PATCH_ERRN+'errorMessage') as mock_err_call:
            self.w._callOnSelected(self.mock_func, self.args,
                                   kwarg=self.kwargs)

        mock_err_call.assert_called_once_with(self.w._errors)

    def test_attr_errors_cleared(self):
        self.w._errors = ['Error']
        with mock.patch(self.PATCH_ERRN+'errorMessage'):
            self.w._callOnSelected(self.mock_func, self.args,
                                   kwarg=self.kwargs)

        self.assertListEqual(self.w._errors, [])


class TestImageViewWidgetMethodDelete(TestImageViewWidget):

    def test_callOnSelected_called_if_QMessageBox_return_Yes(self):
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            with mock.patch(self.IVW+'_callOnSelected') as mock_call_call:
                self.w.delete()

        mock_call_call.assert_called_once_with(
            imagegroupwidget.ImageGroupWidget.delete
        )

    def test_callOnSelected_not_called_if_QMessageBox_return_Cancel(self):
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            with mock.patch(self.IVW+'_callOnSelected') as mock_call_call:
                self.w.delete()

        mock_call_call.assert_not_called()


class TestImageViewWidgetMethodMove(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_dialog = mock.Mock(spec=QtWidgets.QFileDialog)

    def test_callOnSelected_not_called_if_dialog_not_return_new_folder(self):
        self.mock_dialog.exec.return_value = False
        with mock.patch('PyQt5.QtWidgets.QFileDialog',
                        return_value=self.mock_dialog):
            with mock.patch(self.IVW+'_callOnSelected') as mock_call_call:
                self.w.move()

        mock_call_call.assert_not_called()

    def test_callOnSelected_called_with_new_dst_if_dialog_return_new_dst(self):
        self.mock_dialog.exec.return_value = True
        self.mock_dialog.selectedFiles.return_value = ['new_folder']
        with mock.patch('PyQt5.QtWidgets.QFileDialog',
                        return_value=self.mock_dialog):
            with mock.patch(self.IVW+'_callOnSelected') as mock_call_call:
                self.w.move()

        mock_call_call.assert_called_once_with(
            imagegroupwidget.ImageGroupWidget.move,
            'new_folder'
        )


class TestImageViewWidgetMethodAutoSelect(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w.widgets = [self.mock_groupW]

    def test_ImageGroupWidget_autoSelect_called(self):
        self.w.autoSelect()

        self.mock_groupW.autoSelect.assert_called_once_with()


class TestImageViewWidgetMethodUnselect(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w.widgets = [self.mock_groupW]

    def test_ImageGroupWidget_unselect_called(self):
        self.w.unselect()

        self.mock_groupW.unselect.assert_called_once_with()
