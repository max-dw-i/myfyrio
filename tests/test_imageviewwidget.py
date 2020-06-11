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


import logging
from unittest import TestCase, mock

from PyQt5 import QtCore, QtTest, QtWidgets

from doppelganger import config, core
from doppelganger.gui import duplicatewidget, imagegroupwidget, imageviewwidget

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


VIEW_MODULE = 'doppelganger.gui.imageviewwidget.'


# pylint: disable=unused-argument,missing-class-docstring


class TestImageViewWidget(TestCase):

    IVW = VIEW_MODULE + 'ImageViewWidget.'

    def setUp(self):
        self.w = imageviewwidget.ImageViewWidget()


class TestImageViewWidgetMethodInit(TestImageViewWidget):

    def test_class_constants(self):
        self.assertEqual(imageviewwidget.ImageViewWidget.PROG_MIN, 70)
        self.assertEqual(imageviewwidget.ImageViewWidget.PROG_MAX, 100)

    def test_default_values(self):
        self.assertIsNone(self.w.conf)
        self.assertListEqual(self.w._widgets, [])
        self.assertFalse(self.w._interrupted)
        self.assertEqual(self.w._progressBarValue,
                         imageviewwidget.ImageViewWidget.PROG_MIN)

    def test_layout(self):
        margins = self.w._layout.contentsMargins()
        self.assertEqual(margins.top(), 0)
        self.assertEqual(margins.right(), 0)
        self.assertEqual(margins.bottom(), 0)
        self.assertEqual(margins.left(), 0)
        self.assertEqual(self.w._layout.spacing(), 0)
        self.assertEqual(self.w._layout.alignment(),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.assertIsInstance(self.w._layout, QtWidgets.QVBoxLayout)


class TestImageViewWidgetMethodRender(TestImageViewWidget):

    def test_render_called_if_image_groups_found(self):
        image_groups = [[mock.Mock(spec=core.Image)]]
        with mock.patch(self.IVW+'_render') as mock_render_call:
            self.w.render(image_groups)

        mock_render_call.assert_called_once_with(image_groups)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_render_not_called_if_image_groups_not_found(self, mock_box):
        with mock.patch(self.IVW+'_render') as mock_render_call:
            self.w.render([])

        mock_render_call.assert_not_called()

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_finished_signal_emitted_if_image_group_not_found(self, mock_box):
        spy = QtTest.QSignalSpy(self.w.finished)
        self.w.render([])

        self.assertEqual(len(spy), 1)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_QMessageBox_called(self, mock_box):
        self.w.render([])

        mock_box.assert_called_once()


class TestImageViewWidgetMethodPrivateRender(TestImageViewWidget):

    IGW = VIEW_MODULE + 'ImageGroupWidget'

    def setUp(self):
        super().setUp()

        self.mock_conf = mock.Mock(spec=config.Config)
        self.w.conf = self.mock_conf

        self.w._layout = mock.Mock(spec=QtWidgets.QVBoxLayout)

        mock_image = mock.Mock(spec=core.Image)
        self.image_groups = [[mock_image]]
        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.mock_groupW.widgets = []

    def test_raise_ValueError_if_attr_conf_is_None(self):
        self.w.conf = None
        with self.assertRaises(ValueError):
            self.w._render(self.image_groups)

    def test_nothing_called_if_attr_interrupted_True(self):
        self.w._interrupted = True
        spy = QtTest.QSignalSpy(self.w.finished)

        self.w._render(self.image_groups)

        self.assertEqual(len(spy), 0)

    def test_interrupted_signal_emitted_if_attr_interrupted_True(self):
        self.w._interrupted = True
        spy = QtTest.QSignalSpy(self.w.interrupted)

        self.w._render(self.image_groups)

        self.assertEqual(len(spy), 1)

    def test_ImageGroupWidget_called_with_image_group_and_conf_args(self):
        with mock.patch(self.IGW, return_value=self.mock_groupW) as mock_widg:
            self.w._render(self.image_groups)

        mock_widg.assert_called_once_with(self.image_groups[0], self.mock_conf)

    def test_duplicate_widgets_connected_to_hasSelected(self):
        mock_duplW = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_groupW.widgets = [mock_duplW]
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_groups)

        mock_duplW.clicked.connect.assert_called_once_with(self.w._hasSelected)

    def test_ImageGroupWidget_added_to_layout(self):
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_groups)

        self.w._layout.addWidget.assert_called_once_with(self.mock_groupW)

    def test_ImageGroupWidget_added_to_attr_widgets(self):
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_groups)

        self.assertListEqual(self.w._widgets, [self.mock_groupW])

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            with mock.patch(updateGem) as mock_upd_call:
                self.w._render(self.image_groups)

        mock_upd_call.assert_called_once_with()

    def test_updateProgressBar_called_with_proper_args(self):
        self.w._progressBarValue = 11
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            with mock.patch(self.IVW+'_updateProgressBar') as mock_upd_call:
                self.w._render(self.image_groups)

        mock_upd_call.assert_called_once_with(11+30)

    def test_processEvents_called(self):
        proc_events = 'PyQt5.QtCore.QCoreApplication.processEvents'
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            with mock.patch(proc_events) as mock_proc_call:
                self.w._render(self.image_groups)

        mock_proc_call.assert_called_once_with()

    def test_finished_signal_emitted(self):
        spy = QtTest.QSignalSpy(self.w.finished)
        with mock.patch(self.IGW, return_value=self.mock_groupW):
            self.w._render(self.image_groups)

        self.assertEqual(len(spy), 1)


class TestImageViewWidgetMethodUpdateProgressBar(TestImageViewWidget):

    def test_emit_updateProgressBar_signal_if_whole_part_changed(self):
        self.w._progressBarValue = 10.5
        spy = QtTest.QSignalSpy(self.w.updateProgressBar)
        self.w._updateProgressBar(11.2)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 11)

    def test_not_emit_updateProgressBar_if_whole_part_not_changed(self):
        self.w._progressBarValue = 10.5
        spy = QtTest.QSignalSpy(self.w.updateProgressBar)
        self.w._updateProgressBar(10.7)

        self.assertEqual(len(spy), 0)


class TestImageViewWidgetMethodHasSelected(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w._widgets = [self.mock_groupW]

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
        self.w._widgets = [self.mock_groupW]

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

        self.assertListEqual(self.w._widgets, [])

    def test_assign_False_to_attr_interrupted(self):
        self.w.clear()

        self.assertFalse(self.w._interrupted)

    def test_attr_progressBarValue_set_to_attr_PROG_MIN(self):
        self.w.clear()

        self.assertEqual(self.w._progressBarValue, self.w.PROG_MIN)


class TestImageViewWidgetMethodDelete(TestImageViewWidget):

    def test_delete_called_if_QMessageBox_return_Yes(self):
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            with mock.patch(self.IVW+'_delete') as mock_delete_call:
                self.w.delete()

        mock_delete_call.assert_called_once_with()

    def test_delete_not_called_if_QMessageBox_return_Cancel(self):
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            with mock.patch(self.IVW+'_delete') as mock_delete_call:
                self.w.delete()

        mock_delete_call.assert_not_called()


class TestImageViewWidgetMethodPrivateDelete(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w._widgets = [self.mock_groupW]

        self.mock_box = mock.Mock(spec=QtWidgets.QMessageBox)

    def test_imagegroupwidget_delete_called(self):
        self.w._delete()

        self.mock_groupW.delete.assert_called_once_with()

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_logging_if_imagegroupwidget_delete_raise_OSError(self, mock_box):
        mock_box.return_value = self.mock_box
        self.mock_groupW.delete.side_effect = OSError
        with self.assertLogs('main.imageviewwidget', 'ERROR'):
            self.w._delete()

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_QMessageBox_exec_called_if_delete_raise_OSError(self, mock_box):
        mock_box.return_value = self.mock_box
        self.mock_groupW.delete.side_effect = OSError
        self.w._delete()

        self.mock_box.exec.assert_called_once_with()


class TestImageViewWidgetMethodMove(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_dialog = mock.Mock(spec=QtWidgets.QFileDialog)

    def test_move_not_called_if_dialog_not_return_new_folder(self):
        self.mock_dialog.exec.return_value = False
        with mock.patch('PyQt5.QtWidgets.QFileDialog',
                        return_value=self.mock_dialog):
            with mock.patch(self.IVW+'_move') as mock_move_call:
                self.w.move()

        mock_move_call.assert_not_called()

    def test_move_called_with_new_folder_arg_if_dialog_return_new_folder(self):
        self.mock_dialog.exec.return_value = True
        self.mock_dialog.selectedFiles.return_value = ['new_folder']
        with mock.patch('PyQt5.QtWidgets.QFileDialog',
                        return_value=self.mock_dialog):
            with mock.patch(self.IVW+'_move') as mock_move_call:
                self.w.move()

        mock_move_call.assert_called_once_with('new_folder')


class TestImageViewWidgetMethodPrivateMove(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w._widgets = [self.mock_groupW]

        self.dst = 'new_folder'

        self.mock_box = mock.Mock(spec=QtWidgets.QMessageBox)

    def test_imagegroupwidget_move_called(self):
        self.w._move(self.dst)

        self.mock_groupW.move.assert_called_once_with(self.dst)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_logging_if_imagegroupwidget_move_raise_OSError(self, mock_box):
        mock_box.return_value = self.mock_box
        self.mock_groupW.move.side_effect = OSError
        with self.assertLogs('main.imageviewwidget', 'ERROR'):
            self.w._move(self.dst)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_QMessageBox_exec_called_if_move_raise_OSError(self, mock_box):
        mock_box.return_value = self.mock_box
        self.mock_groupW.move.side_effect = OSError
        self.w._move(self.dst)

        self.mock_box.exec.assert_called_once_with()


class TestImageViewWidgetMethodAutoSelect(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w._widgets = [self.mock_groupW]

    def test_ImageGroupWidget_autoSelect_called(self):
        self.w.autoSelect()

        self.mock_groupW.autoSelect.assert_called_once_with()


class TestImageViewWidgetMethodUnselect(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_groupW = mock.Mock(spec=imagegroupwidget.ImageGroupWidget)
        self.w._widgets = [self.mock_groupW]

    def test_ImageGroupWidget_unselect_called(self):
        self.w.unselect()

        self.mock_groupW.unselect.assert_called_once_with()
