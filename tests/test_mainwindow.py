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

from unittest import TestCase, mock

from PyQt5 import QtCore, QtTest, QtWidgets

from myfyrio import workers
from myfyrio.gui import (aboutwindow, imageviewwidget, mainwindow,
                         pathslistwidget, preferenceswindow, pushbutton,
                         sensitivityradiobutton)

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

# pylint: disable=missing-class-docstring


class TestMainWindow(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mw = mainwindow.MainWindow()


class TestMainWindowMethodInit(TestMainWindow):

    def test_init_values(self):
        self.assertIsInstance(self.mw.aboutWindow, aboutwindow.AboutWindow)
        self.assertIsInstance(self.mw.preferencesWindow,
                              preferenceswindow.PreferencesWindow)
        self.assertListEqual(self.mw._errors, [])
        self.assertIsInstance(self.mw.threadpool, QtCore.QThreadPool)
        self.assertEqual(self.mw.verticalLayout.contentsMargins().top(), 9)
        self.assertEqual(self.mw.verticalLayout.contentsMargins().bottom(), 9)
        self.assertEqual(self.mw.verticalLayout.contentsMargins().right(), 9)
        self.assertEqual(self.mw.verticalLayout.contentsMargins().left(), 9)

    def test_enabled_by_default_actions(self):
        self.assertTrue(self.mw.addFolderAction.isEnabled())

    def test_enabled_by_default_buttons(self):
        self.assertTrue(self.mw.addFolderBtn.isEnabled())

    def test_disabled_by_default_actions(self):
        self.assertFalse(self.mw.delFolderAction.isEnabled())
        self.assertFalse(self.mw.moveAction.isEnabled())
        self.assertFalse(self.mw.deleteAction.isEnabled())
        self.assertFalse(self.mw.autoSelectAction.isEnabled())
        self.assertFalse(self.mw.unselectAction.isEnabled())

    def test_disabled_by_default_buttons(self):
        self.assertFalse(self.mw.delFolderBtn.isEnabled())
        self.assertFalse(self.mw.moveBtn.isEnabled())
        self.assertFalse(self.mw.deleteBtn.isEnabled())
        self.assertFalse(self.mw.autoSelectBtn.isEnabled())
        self.assertFalse(self.mw.unselectBtn.isEnabled())
        self.assertFalse(self.mw.startBtn.isEnabled())
        self.assertFalse(self.mw.stopBtn.isEnabled())

    def test_sensitivity_radio_buttons_check_and_not_checked_by_default(self):
        self.assertTrue(self.mw.veryHighRbtn.isChecked())
        self.assertFalse(self.mw.highRbtn.isChecked())
        self.assertFalse(self.mw.mediumRbtn.isChecked())
        self.assertFalse(self.mw.lowRbtn.isChecked())
        self.assertFalse(self.mw.veryLowRbtn.isChecked())

    def test_pathsList_is_empty_by_default(self):
        self.assertListEqual(self.mw.pathsList.paths(), [])

    def test_processProg_set_to_0_by_default(self):
        self.assertEqual(self.mw.processProg.value(), 0)

    def test_processing_labels_numbers_are_0_by_default(self):
        self.assertEqual(self.mw.loadedPicLbl.text()[-2:], ' 0')
        self.assertEqual(self.mw.foundInCacheLbl.text()[-2:], ' 0')
        self.assertEqual(self.mw.calculatedLbl.text()[-2:], ' 0')
        self.assertEqual(self.mw.duplicatesLbl.text()[-2:], ' 0')
        self.assertEqual(self.mw.groupsLbl.text()[-2:], ' 0')


class TestMainWindowMethodSetImageViewWidget(TestMainWindow):

    PATCH_ERRN = 'myfyrio.gui.errornotifier.'

    def setUp(self):
        self.mock_IVW = mock.Mock(spec=imageviewwidget.ImageViewWidget)
        self.mw.imageViewWidget = self.mock_IVW

    def test_preferences_conf_assigned_to_attr_conf(self):
        self.mw._setImageViewWidget()

        self.assertEqual(self.mw.imageViewWidget.conf,
                         self.mw.preferencesWindow.conf)

    def test_updateProgressBar_signal_connected_to_processProg_setValue(self):
        self.mw._setImageViewWidget()

        self.mock_IVW.updateProgressBar.connect.assert_called_once_with(
            self.mw.processProg.setValue
        )

    def test_finished_signal_connected_to_6_slots(self):
        self.mw._setImageViewWidget()

        self.assertEqual(len(self.mock_IVW.finished.connect.call_args_list), 6)

    def test_finished_signal_connected_to_processProg_setMaxValue(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.processProg.setMaxValue)]
        self.mock_IVW.finished.connect.assert_has_calls(calls)

    def test_finished_signal_connected_to_stopBtn_disable(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.stopBtn.disable)]
        self.mock_IVW.finished.connect.assert_has_calls(calls)

    def test_finished_signal_connected_to_startBtn_finished(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.startBtn.finished)]
        self.mock_IVW.finished.connect.assert_has_calls(calls)

    def test_finished_signal_connected_to_autoSelectBtn_enable(self):
        self.mw.imageViewWidget.widgets = ['widget']
        self.mw.autoSelectBtn.setEnabled(False)
        self.mw._setImageViewWidget()

        call_args_list = self.mock_IVW.finished.connect.call_args_list
        f = call_args_list[3][0][0]
        f()

        self.assertTrue(self.mw.autoSelectBtn.isEnabled())

    def test_finished_signal_connected_to_autoSelectBtn_disable(self):
        self.mw.imageViewWidget.widgets = []
        self.mw.autoSelectBtn.setEnabled(True)
        self.mw._setImageViewWidget()

        call_args_list = self.mock_IVW.finished.connect.call_args_list
        f = call_args_list[3][0][0]
        f()

        self.assertFalse(self.mw.autoSelectBtn.isEnabled())

    def test_finished_connected_to_menubar_disableAutoSelectAction(self):
        self.mw.imageViewWidget.widgets = ['widget']
        self.mw.autoSelectAction.setEnabled(False)
        self.mw._setImageViewWidget()

        call_args_list = self.mock_IVW.finished.connect.call_args_list
        f = call_args_list[4][0][0]
        f()

        self.assertTrue(self.mw.autoSelectAction.isEnabled())

    def test_finished_signal_connected_to_menubar_enableAutoSelectAction(self):
        self.mw.imageViewWidget.widgets = []
        self.mw.autoSelectAction.setEnabled(True)
        self.mw._setImageViewWidget()

        call_args_list = self.mock_IVW.finished.connect.call_args_list
        f = call_args_list[4][0][0]
        f()

        self.assertFalse(self.mw.autoSelectAction.isEnabled())

    def test_finished_signal_connected_to_errorMessage(self):
        self.mw._errors = ['error']
        self.mw._setImageViewWidget()

        call_args_list = self.mock_IVW.finished.connect.call_args_list
        f = call_args_list[5][0][0]
        with mock.patch(self.PATCH_ERRN+'errorMessage') as mock_err_call:
            f()

        mock_err_call.assert_called_once_with(['error'])

    def test_error_signal_connected_to_attr_errors_append_method(self):
        self.mw._setImageViewWidget()

        self.mock_IVW.error.connect.assert_called_once_with(
            self.mw._errors.append
        )

    def test_test_selected_signal_connected_to_6_slots(self):
        self.mw._setImageViewWidget()

        self.assertEqual(
            len(self.mock_IVW.selected.connect.call_args_list), 6
        )

    def test_selected_signal_connected_to_moveBtn_setEnabled(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.moveBtn.setEnabled)]
        self.mock_IVW.selected.connect.assert_has_calls(calls)

    def test_selected_signal_connected_to_deleteBtn_setEnabled(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.deleteBtn.setEnabled)]
        self.mock_IVW.selected.connect.assert_has_calls(calls)

    def test_selected_signal_connected_to_unselectBtn_setEnabled(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.unselectBtn.setEnabled)]
        self.mock_IVW.selected.connect.assert_has_calls(calls)

    def test_selected_signal_connected_to_moveAction_setEnabled(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.moveAction.setEnabled)]
        self.mock_IVW.selected.connect.assert_has_calls(calls)

    def test_selected_signal_connected_to_deleteAction_setEnabled(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.deleteAction.setEnabled)]
        self.mock_IVW.selected.connect.assert_has_calls(calls)

    def test_selected_signal_connected_to_unselectAction_setEnabled(self):
        self.mw._setImageViewWidget()

        calls = [mock.call(self.mw.unselectAction.setEnabled)]
        self.mock_IVW.selected.connect.assert_has_calls(calls)


class TestMainWindowMethodSetFolderPathsGroupBox(TestMainWindow):

    def setUp(self):
        self.mock_paths = mock.Mock(spec=pathslistwidget.PathsListWidget)
        self.mock_addBtn = mock.Mock(spec=QtWidgets.QPushButton)
        self.mock_delBtn = mock.Mock(spec=QtWidgets.QPushButton)

        self.mw.pathsList = self.mock_paths
        self.mw.addFolderBtn = self.mock_addBtn
        self.mw.delFolderBtn = self.mock_delBtn

    def test_pathsList_hasSelection_signal_connected_to_2_slots(self):
        self.mw._setFolderPathsGroupBox()

        self.assertEqual(
            len(self.mock_paths.hasSelection.connect.call_args_list), 2
        )

    def test_pathsList_hasSelection_connected_to_delFolderBtn_setEnabled(self):
        self.mw._setFolderPathsGroupBox()

        calls = [mock.call(self.mw.delFolderBtn.setEnabled)]
        self.mock_paths.hasSelection.connect.assert_has_calls(calls)

    def test_pathsList_hasSelection_connected_to_delFolderA_setEnabled(self):
        self.mw._setFolderPathsGroupBox()

        calls = [mock.call(self.mw.delFolderAction.setEnabled)]
        self.mock_paths.hasSelection.connect.assert_has_calls(calls)

    def test_pathsList_hasItems_signal_connected_to_startBtn_switch(self):
        self.mw._setFolderPathsGroupBox()

        self.mock_paths.hasItems.connect.assert_called_once_with(
            self.mw.startBtn.switch
        )

    def test_addFolderBtn_clicked_signal_connected_to_pathsList_addPath(self):
        self.mw._setFolderPathsGroupBox()

        calls = [mock.call(self.mw.pathsList.addPath)]
        self.mock_addBtn.clicked.connect.assert_has_calls(calls)

    def test_delFolderBtn_clicked_signal_connected_to_pathsList_delPath(self):
        self.mw._setFolderPathsGroupBox()

        calls = [mock.call(self.mw.pathsList.delPath)]
        self.mock_delBtn.clicked.connect.assert_has_calls(calls)


class TestMainWindowMethodSetImageProcessingGroupBox(TestMainWindow):

    def setUp(self):
        self.mock_startBtn = mock.Mock(spec=pushbutton.StartButton)
        self.mock_stopBtn = mock.Mock(spec=pushbutton.PushButton)

        self.mw.startBtn = self.mock_startBtn
        self.mw.stopBtn = self.mock_stopBtn

    def test_processProg_minimum_set_to_ImageProcessing_PROG_MIN(self):
        self.mw._setImageProcessingGroupBox()

        self.assertEqual(self.mw.processProg.minimum(),
                         workers.ImageProcessing.PROG_MIN)

    def test_processProg_maximum_set_to_ImageProcessing_PROG_MAX(self):
        self.mw._setImageProcessingGroupBox()

        self.assertEqual(self.mw.processProg.maximum(),
                         workers.ImageProcessing.PROG_MAX)

    def test_startBtn_clicked_signal_connected_to_13_slots(self):
        self.mw._setImageProcessingGroupBox()

        self.assertEqual(
            len(self.mock_startBtn.clicked.connect.call_args_list), 13
        )

    def test_startBtn_clicked_signal_connected_to_attr_errors_clear(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw._errors.clear)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_imageViewWidget_clear(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.imageViewWidget.clear)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_connected_to_processProg_setMinValue(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.processProg.setMinValue)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_loadedPicLbl_clear(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.loadedPicLbl.clear)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_foundInCacheLbl_clear(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.foundInCacheLbl.clear)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_calculatedLbl_clear(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.calculatedLbl.clear)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_duplicatesLbl_clear(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.duplicatesLbl.clear)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_groupsLbl_clear(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.groupsLbl.clear)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_startBtn_started(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.startBtn.started)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_stopBtn_enable(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.stopBtn.enable)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_autoSelectBtn_disable(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.autoSelectBtn.disable)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_connected_to_menub_disableAutoSelectAction(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.menubar.disableAutoSelectAction)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_startBtn_clicked_signal_connected_to_startProcessing(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw._startProcessing)]
        self.mock_startBtn.clicked.connect.assert_has_calls(calls)

    def test_stopBtn_clicked_signal_connected_to_1_slots(self):
        self.mw._setImageProcessingGroupBox()

        self.assertEqual(
            len(self.mock_stopBtn.clicked.connect.call_args_list), 1
        )

    def test_stopBtn_clicked_signal_connected_to_stopBtn_disable(self):
        self.mw._setImageProcessingGroupBox()

        calls = [mock.call(self.mw.stopBtn.disable)]
        self.mock_stopBtn.clicked.connect.assert_has_calls(calls)


class TestMainWindowMethodSetSensitivityGroupBox(TestMainWindow):

    PATCH_SRB = 'myfyrio.gui.sensitivityradiobutton.'

    def setUp(self):
        self.mw.preferencesWindow = mock.Mock(
            spec=preferenceswindow.PreferencesWindow
        )

    def test_pW_setSensitivity_called_with_checkedRadioButton_res(self):
        mock_btn = mock.Mock(sensitivityradiobutton.SensitivityRadioButton)
        mock_btn.sensitivity = '69'
        with mock.patch(self.PATCH_SRB+'checkedRadioButton',
                        return_value=mock_btn) as mock_checked_call:
            self.mw._setSensitivityGroupBox()

        mock_checked_call.assert_called_once_with(self.mw)
        self.mw.preferencesWindow.setSensitivity.assert_called_once_with(
            mock_btn.sensitivity
        )

    def test_vHighRbtn_sensitivityChanged_connected_to_pW_setSensitivity(self):
        mock_btn = mock.Mock(spec=sensitivityradiobutton.VeryHighRadioButton)
        self.mw.veryHighRbtn = mock_btn
        self.mw._setSensitivityGroupBox()

        mock_btn.sensitivityChanged.connect.assert_called_once_with(
            self.mw.preferencesWindow.setSensitivity
        )

    def test_highRbtn_sensitivityChanged_connected_to_pW_setSensitivity(self):
        mock_btn = mock.Mock(spec=sensitivityradiobutton.HighRadioButton)
        self.mw.highRbtn = mock_btn
        self.mw._setSensitivityGroupBox()

        mock_btn.sensitivityChanged.connect.assert_called_once_with(
            self.mw.preferencesWindow.setSensitivity
        )

    def test_medRbtn_sensitivityChanged_connected_to_pW_setSensitivity(self):
        mock_btn = mock.Mock(spec=sensitivityradiobutton.MediumRadioButton)
        self.mw.mediumRbtn = mock_btn
        self.mw._setSensitivityGroupBox()

        mock_btn.sensitivityChanged.connect.assert_called_once_with(
            self.mw.preferencesWindow.setSensitivity
        )

    def test_lowRbtn_sensitivityChanged_connected_to_pW_setSensitivity(self):
        mock_btn = mock.Mock(spec=sensitivityradiobutton.LowRadioButton)
        self.mw.lowRbtn = mock_btn
        self.mw._setSensitivityGroupBox()

        mock_btn.sensitivityChanged.connect.assert_called_once_with(
            self.mw.preferencesWindow.setSensitivity
        )

    def test_vLowRbtn_sensitivityChanged_connected_to_pW_setSensitivity(self):
        mock_btn = mock.Mock(spec=sensitivityradiobutton.VeryLowRadioButton)
        self.mw.veryLowRbtn = mock_btn
        self.mw._setSensitivityGroupBox()

        mock_btn.sensitivityChanged.connect.assert_called_once_with(
            self.mw.preferencesWindow.setSensitivity
        )


class TestMainWindowMethodSetActionsGroupBox(TestMainWindow):

    def test_moveBtn_clicked_signal_connected_to_imageViewWidget_move(self):
        self.mw.moveBtn = mock.Mock(spec=QtWidgets.QPushButton)
        self.mw._setActionsGroupBox()

        self.mw.moveBtn.clicked.connect.assert_called_once_with(
            self.mw.imageViewWidget.move
        )

    def test_deleteBtn_clicked_connected_to_imageViewWidget_delete(self):
        self.mw.deleteBtn = mock.Mock(spec=QtWidgets.QPushButton)
        self.mw._setActionsGroupBox()

        self.mw.deleteBtn.clicked.connect.assert_called_once_with(
            self.mw.imageViewWidget.delete
        )

    def test_autoSelectBtn_clicked_connected_to_imageViewW_autoSelect(self):
        self.mw.autoSelectBtn = mock.Mock(spec=pushbutton.PushButton)
        self.mw._setActionsGroupBox()

        self.mw.autoSelectBtn.clicked.connect.assert_called_once_with(
            self.mw.imageViewWidget.autoSelect
        )

    def test_unselectBtn_clicked_connected_to_imageViewWidget_unselect(self):
        self.mw.unselectBtn = mock.Mock(spec=QtWidgets.QPushButton)
        self.mw._setActionsGroupBox()

        self.mw.unselectBtn.clicked.connect.assert_called_once_with(
            self.mw.imageViewWidget.unselect
        )


class TestMainWindowMethodSetMenubar(TestMainWindow):

    def test_addFolderAction_connected_to_pathsList_addPath(self):
        self.mw.addFolderAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.addFolderAction.triggered.connect.assert_called_once_with(
            self.mw.pathsList.addPath
        )

    def test_delFolderAction_connected_to_pathsList_delPath(self):
        self.mw.delFolderAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.delFolderAction.triggered.connect.assert_called_once_with(
            self.mw.pathsList.delPath
        )

    def test_preferencesAction_setData_called_with_QVarian_res(self):
        self.mw.preferencesAction = mock.Mock(spec=QtWidgets.QAction)
        mock_var = mock.Mock(spec=QtCore.QVariant)
        with mock.patch('PyQt5.QtCore.QVariant',
                        return_value=mock_var) as mock_qvar_call:
            self.mw._setMenubar()

        calls = [mock.call(self.mw.preferencesWindow)]
        mock_qvar_call.assert_has_calls(calls)

        self.mw.preferencesAction.setData.assert_called_once_with(mock_var)

    def test_preferencesAction_connected_to_menubar_openWindow(self):
        self.mw.preferencesAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.preferencesAction.triggered.connect.assert_called_once_with(
            self.mw.menubar.openWindow
        )

    def test_exitAction_connected_to_close(self):
        self.mw.exitAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.exitAction.triggered.connect.assert_called_once_with(
            self.mw.close
        )

    def test_moveAction_connected_to_imageViewWidget_move(self):
        self.mw.moveAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.moveAction.triggered.connect.assert_called_once_with(
            self.mw.imageViewWidget.move
        )

    def test_deleteAction_connected_to_imageViewWidget_delete(self):
        self.mw.deleteAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.deleteAction.triggered.connect.assert_called_once_with(
            self.mw.imageViewWidget.delete
        )

    def test_autoSelectAction_connected_to_imageViewWidget_autoSelect(self):
        self.mw.autoSelectAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.autoSelectAction.triggered.connect.assert_called_once_with(
            self.mw.imageViewWidget.autoSelect
        )

    def test_unselectAction_connected_to_imageViewWidget_unselect(self):
        self.mw.unselectAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.unselectAction.triggered.connect.assert_called_once_with(
            self.mw.imageViewWidget.unselect
        )

    def test_docsAction_connected_to_menubar_openDocs(self):
        self.mw.docsAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.docsAction.triggered.connect.assert_called_once_with(
            self.mw.menubar.openDocs
        )

    def test_homePageAction_connected_to_menubar_openDocs(self):
        self.mw.homePageAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.homePageAction.triggered.connect.assert_called_once_with(
            self.mw.menubar.openDocs
        )

    def test_aboutAction_setData_called_with_QVarian_res(self):
        self.mw.aboutAction = mock.Mock(spec=QtWidgets.QAction)
        mock_var = mock.Mock(spec=QtCore.QVariant)
        with mock.patch('PyQt5.QtCore.QVariant',
                        return_value=mock_var) as mock_qvar_call:
            self.mw._setMenubar()

        calls = [mock.call(self.mw.aboutWindow)]
        mock_qvar_call.assert_has_calls(calls)

        self.mw.aboutAction.setData.assert_called_once_with(mock_var)

    def test_aboutAction_connected_to_menubar_openWindow(self):
        self.mw.aboutAction = mock.Mock(spec=QtWidgets.QAction)
        self.mw._setMenubar()

        self.mw.aboutAction.triggered.connect.assert_called_once_with(
            self.mw.menubar.openWindow
        )


class TestMainWindowMethodStartProcessing(TestMainWindow):

    PATCH_PROC = 'myfyrio.workers.ImageProcessing'
    PATCH_WORKERS = 'myfyrio.workers.Worker'
    PATCH_ERRN = 'myfyrio.gui.errornotifier.'

    def setUp(self):
        self.mock_proc = mock.Mock(spec=workers.ImageProcessing)

        self.mock_stopBtn = mock.Mock(spec=pushbutton.PushButton)
        self.mw.stopBtn = self.mock_stopBtn

        self.mock_threadpool = mock.Mock(spec=QtCore.QThreadPool)
        self.mw.threadpool = self.mock_threadpool

    def test_args_ImageProcessing_called_with(self):
        with mock.patch(self.PATCH_PROC,
                        return_value=self.mock_proc) as mock_proc_call:
            self.mw._startProcessing()

        mock_proc_call.assert_called_once_with(
            self.mw.pathsList.paths(),
            self.mw.preferencesWindow.conf
        )

    def test_images_loaded_connected_to_loadedPicLbl_updateNumber(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_proc.images_loaded.connect.assert_called_once_with(
            self.mw.loadedPicLbl.updateNumber
        )

    def test_found_in_cache_connected_to_foundInCacheLbl_updateNumber(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_proc.found_in_cache.connect.assert_called_once_with(
            self.mw.foundInCacheLbl.updateNumber
        )

    def test_hashes_calculated_connected_to_calculatedLbl_updateNumber(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_proc.hashes_calculated.connect.assert_called_once_with(
            self.mw.calculatedLbl.updateNumber
        )

    def test_duplicates_found_connected_to_duplicatesLbl_updateNumber(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_proc.duplicates_found.connect.assert_called_once_with(
            self.mw.duplicatesLbl.updateNumber
        )

    def test_groups_found_connected_to_groupsLbl_updateNumber(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_proc.groups_found.connect.assert_called_once_with(
            self.mw.groupsLbl.updateNumber
        )

    def test_update_progressbar_connected_to_processProg_setValue(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_proc.update_progressbar.connect.assert_called_once_with(
            self.mw.processProg.setValue
        )

    def test_image_group_connected_to_imageViewWidget_render(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_proc.image_group.connect.assert_called_once_with(
            self.mw.imageViewWidget.render, QtCore.Qt.BlockingQueuedConnection
        )

    def test_error_connected_to_attr_errors_append_method(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_proc.error.connect.assert_called_once_with(
            self.mw._errors.append
        )

    def test_interrupted_signal_connected_to_3_slots(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.assertEqual(
            len(self.mock_proc.interrupted.connect.call_args_list), 3
        )

    def test_interrupted_connected_to_startBtn_finished(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        calls = [mock.call(self.mw.startBtn.finished)]
        self.mock_proc.interrupted.connect.assert_has_calls(calls)

    def test_interrupted_connected_to_stopBtn_disable(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        calls = [mock.call(self.mw.stopBtn.disable)]
        self.mock_proc.interrupted.connect.assert_has_calls(calls)

    def test_interrupted_signal_connected_to_errorMessage(self):
        self.mw._errors = ['error']
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        call_args_list = self.mock_proc.interrupted.connect.call_args_list
        f = call_args_list[2][0][0]
        with mock.patch(self.PATCH_ERRN+'errorMessage') as mock_err_call:
            f()

        mock_err_call.assert_called_once_with(['error'])

    def test_imageViewWidget_interrupted__to_ImageProcessing_interrupt(self):
        mock_IVW = mock.Mock(spec=imageviewwidget.ImageViewWidget)
        self.mw.imageViewWidget = mock_IVW
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mw.imageViewWidget.interrupted.connect.assert_called_once_with(
            self.mock_proc.interrupt
        )

    def test_stopBtn_clicked_connected_to_ImageProcessing_interrupt(self):
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            self.mw._startProcessing()

        self.mock_stopBtn.clicked.connect.assert_called_once_with(
            self.mock_proc.interrupt
        )

    def test_worker_obj_called_with_ImageProcessing_run_pushed_to_pool(self):
        mock_worker = mock.Mock(spec=workers.Worker)
        with mock.patch(self.PATCH_PROC, return_value=self.mock_proc):
            with mock.patch(self.PATCH_WORKERS,
                            return_value=mock_worker) as mock_worker_call:
                self.mw._startProcessing()

        mock_worker_call.assert_called_once_with(self.mock_proc.run)
        self.mock_threadpool.start.assert_called_once_with(mock_worker)


class TestMainWindowMethodCloseEvent(TestMainWindow):

    def setUp(self):
        self.mock_event = mock.Mock(spec=QtCore.QEvent)

        self.mock_threadpool = mock.Mock(spec=QtCore.QThreadPool)
        self.mock_threadpool.activeThreadCount.return_value = 0
        self.mw.threadpool = self.mock_threadpool

        self.spy = QtTest.QSignalSpy(self.mw.stopBtn.clicked)

    def test_event_ignore_not_called_if_no_confirmation(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = False

        self.mw.closeEvent(self.mock_event)

        self.mock_event.ignore.assert_not_called()

    def test_stopBtn_clicked_not_emitted_if_no_confirmation_and_disabled(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = False
        self.mw.stopBtn.setEnabled(False)
        spy = QtTest.QSignalSpy(self.mw.stopBtn.clicked)

        self.mw.closeEvent(self.mock_event)

        self.assertEqual(len(spy), 0)

    def test_stopBtn_clicked_emitted_if_no_confirmation_and_enabled(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = False
        self.mw.stopBtn.setEnabled(True)
        spy = QtTest.QSignalSpy(self.mw.stopBtn.clicked)

        self.mw.closeEvent(self.mock_event)

        self.assertEqual(len(spy), 1)

    def test_processEvents_called_if_no_confirmation_and_active_threads(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = False
        self.mock_threadpool.activeThreadCount.side_effect = [1, 0]
        PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
        with mock.patch(PATCH_EVENTS) as mock_proc_call:
            self.mw.closeEvent(self.mock_event)

        mock_proc_call.assert_called_once_with()

    def test_waitForDone_called_if_no_confirmation_and_active_threads(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = False
        self.mock_threadpool.activeThreadCount.side_effect = [1, 0]
        PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
        with mock.patch(PATCH_EVENTS):
            self.mw.closeEvent(self.mock_event)

        self.mock_threadpool.waitForDone.assert_called_once_with(msecs=100)

    def test_processEvents_not_called_if_no_confir_and_no_active_threads(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = False
        self.mock_threadpool.activeThreadCount.return_value = 0
        PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
        with mock.patch(PATCH_EVENTS) as mock_proc_call:
            self.mw.closeEvent(self.mock_event)

        mock_proc_call.assert_not_called()

    def test_waitForDone_not_called_if_no_confir_and_no_active_threads(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = False
        self.mock_threadpool.activeThreadCount.return_value = 0
        PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
        with mock.patch(PATCH_EVENTS):
            self.mw.closeEvent(self.mock_event)

        self.mock_threadpool.waitForDone.assert_not_called()

    def test_threadpool_clear_called_if_no_confirmation(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = False

        self.mw.closeEvent(self.mock_event)

        self.mock_threadpool.clear.assert_called_once_with()

    def test_event_ignore_called_if_confirmation_and_Cancel(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            self.mw.closeEvent(self.mock_event)

        self.mock_event.ignore.assert_called_once_with()

    def test_stopBtn_clicked_not_emitted_if_confirmation__Cancel__disabl(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        self.mw.stopBtn.setEnabled(False)
        spy = QtTest.QSignalSpy(self.mw.stopBtn.clicked)
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            self.mw.closeEvent(self.mock_event)

        self.assertEqual(len(spy), 0)

    def test_stopBtn_clicked_not_emitted_if_confirmation__Cancel__enabl(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        self.mw.stopBtn.setEnabled(True)
        spy = QtTest.QSignalSpy(self.mw.stopBtn.clicked)
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            self.mw.closeEvent(self.mock_event)

        self.assertEqual(len(spy), 0)

    def test_processEvents_not_called_if_confirmation_and_Cancel(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
            with mock.patch(PATCH_EVENTS) as mock_proc_call:
                self.mw.closeEvent(self.mock_event)

        mock_proc_call.assert_not_called()

    def test_waitForDone_not_called_if_confirmation_and_Cancel(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
            with mock.patch(PATCH_EVENTS):
                self.mw.closeEvent(self.mock_event)

        self.mock_threadpool.waitForDone.assert_not_called()

    def test_threadpool_clear_not_called_if_confirmation_and_Cancel(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            self.mw.closeEvent(self.mock_event)

        self.mock_threadpool.clear.assert_not_called()

    def test_event_ignore_not_called_if_confirmation_and_Yes(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            self.mw.closeEvent(self.mock_event)

        self.mock_event.ignore.assert_not_called()

    def test_stopBtn_clicked_not_emitted_if_confirmation__Yes__disabled(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        self.mw.stopBtn.setEnabled(False)
        spy = QtTest.QSignalSpy(self.mw.stopBtn.clicked)
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            self.mw.closeEvent(self.mock_event)

        self.assertEqual(len(spy), 0)

    def test_stopBtn_clicked_emitted_if_confirmation__Yes__enabled(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        self.mw.stopBtn.setEnabled(True)
        spy = QtTest.QSignalSpy(self.mw.stopBtn.clicked)
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            self.mw.closeEvent(self.mock_event)

        self.assertEqual(len(spy), 1)

    def test_processEvents_called_if_confirmation__Yes_and_active_thread(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        self.mock_threadpool.activeThreadCount.side_effect = [1, 0]
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
            with mock.patch(PATCH_EVENTS) as mock_proc_call:
                self.mw.closeEvent(self.mock_event)

        mock_proc_call.assert_called_once_with()

    def test_waitForDone_called_if_confirmation__Yes_and_active_thread(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        self.mock_threadpool.activeThreadCount.side_effect = [1, 0]
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
            with mock.patch(PATCH_EVENTS):
                self.mw.closeEvent(self.mock_event)

        self.mock_threadpool.waitForDone.assert_called_once_with(msecs=100)

    def test_processEvents_not_called_if_confir__Yes__no_active_thread(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        self.mock_threadpool.activeThreadCount.return_value = 0
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
            with mock.patch(PATCH_EVENTS) as mock_proc_call:
                self.mw.closeEvent(self.mock_event)

        mock_proc_call.assert_not_called()

    def test_waitForDone_not_called_if_confir__Yes__no_active_thread(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        self.mock_threadpool.activeThreadCount.return_value = 0
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
            with mock.patch(PATCH_EVENTS):
                self.mw.closeEvent(self.mock_event)

        self.mock_threadpool.waitForDone.assert_not_called()

    def test_threadpool_clear_called_if_confirmation_and_Yes(self):
        self.mw.preferencesWindow.conf['close_confirmation'] = True
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            self.mw.closeEvent(self.mock_event)

        self.mock_threadpool.clear.assert_called_once_with()
