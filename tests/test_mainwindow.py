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

from doppelganger import config, core, mainwindow, preferenceswindow, widgets

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


# pylint: disable=unused-argument,missing-class-docstring,protected-access


class TestMainForm(TestCase):

    def setUp(self):
        self.conf = {
            'size': 200,
            'show_similarity': True,
            'show_size': True,
            'show_path': True,
            'sort': 0,
            'delete_dirs': False,
            'size_format': 1,
            'subfolders': True,
            'close_confirmation': False,
        }
        self.form = mainwindow.MainWindow()

    @mock.patch('doppelganger.mainwindow.MainWindow._setMenubar')
    def test_init(self, mock_menubar):
        form = mainwindow.MainWindow()
        scroll_area_align = form.scrollAreaLayout.layout().alignment()
        self.assertEqual(scroll_area_align, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.assertIsInstance(form.threadpool, QtCore.QThreadPool)
        self.assertTrue(mock_menubar.called)

    """@mock.patch('doppelganger.aboutwindow.AboutWindow')
    @mock.patch('doppelganger.mainwindow.MainWindow.findChildren', return_value=[])
    def test_help_menu_calls_openAboutForm(self, mock_form, mock_init):
        aboutAction = self.form.findChild(QtWidgets.QAction, 'aboutAction')
        aboutAction.trigger()

        self.assertTrue(mock_init.called)

    @mock.patch('doppelganger.preferenceswindow.PreferencesWindow')
    @mock.patch('doppelganger.mainwindow.MainWindow.findChildren', return_value=[])
    def test_options_menu_calls_openPreferencesForm(self, mock_form, mock_init):
        preferencesAction = self.form.findChild(QtWidgets.QAction, 'preferencesAction')
        preferencesAction.trigger()

        self.assertTrue(mock_init.called)"""

    def test_add_folder_menu_calls_add_folder_func(self):
        pass

    def test_remove_folder_menu_calls_del_folder_func(self):
        pass

    def test_exit_menu_calls_close_func(self):
        pass

    def test_delete_images_menu_calls_close_func(self):
        pass

    def test_move_images_menu_calls_close_func(self):
        pass

    def test_documentation_menu_calls_openDocs_func(self):
        pass

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.widgets.DuplicateWidget.move', side_effect=OSError)
    def test_call_on_selected_widgets_move_raises_OSError(self, mock_move, mock_box):
        image_group = [core.Image('img1.png')]
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget(image_group, self.form.preferencesWindow.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True
        dst = 'new_dst'
        self.form._call_on_selected_widgets(dst)

        mock_move.assert_called_once_with(dst)
        self.assertTrue(mock_box.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.widgets.DuplicateWidget.delete', side_effect=OSError)
    def test_call_on_selected_widgets_delete_raises_OSError(self, mock_delete, mock_box):
        image_group = [core.Image('img1.png')]
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget(image_group, self.form.preferencesWindow.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True
        with self.assertLogs('main.mainwindow', 'ERROR'):
            self.form._call_on_selected_widgets()

        mock_delete.assert_called_once()
        self.assertTrue(mock_box.called)

    @mock.patch('doppelganger.core.Image.del_parent_dir')
    @mock.patch('doppelganger.widgets.DuplicateWidget.delete')
    def test_call_on_selected_widgets_delete_empty_dir(self, mock_delete, mock_dir):
        image_group = [core.Image('img1.png')]
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget(image_group, self.form.preferencesWindow.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True
        self.form.preferencesWindow.conf['delete_dirs'] = True

        self.form._call_on_selected_widgets()

        self.assertTrue(mock_dir.called)

    @mock.patch('doppelganger.core.Image.del_parent_dir')
    @mock.patch('doppelganger.widgets.DuplicateWidget.delete')
    def test_call_on_selected_widgets_not_delete_empty_dir(self, mock_delete, mock_dir):
        image_group = [core.Image('img1.png')]
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget(image_group, self.form.preferencesWindow.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True
        self.form.preferencesWindow.conf['delete_dirs'] = False

        self.form._call_on_selected_widgets()

        self.assertFalse(mock_dir.called)

    @mock.patch('doppelganger.widgets.ImageGroupWidget.deleteLater')
    def test_call_on_selected_widgets_deleteLater_on_ImageGroupWidget(self, mock_later):
        image_group = [core.Image('img1.png')]
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget(image_group, self.form.preferencesWindow.conf)
        )
        self.form._call_on_selected_widgets()

        mock_later.assert_called_once()

    @mock.patch('PyQt5.QtCore.QEvent.ignore')
    @mock.patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QtWidgets.QMessageBox.Cancel)
    def test_closeEvent(self, mock_q, mock_ign):
        self.form.preferencesWindow.conf['close_confirmation'] = True
        self.form.close()

        mock_ign.assert_called_once()

    @mock.patch('PyQt5.QtWidgets.QWidget.show')
    @mock.patch('PyQt5.QtWidgets.QWidget.isVisible', return_value=False)
    def test_openAboutWindow_show_it_if_not_visible(self, mock_vis, mock_show):
        self.form.openAboutWindow()

        mock_show.assert_called_once_with()

    @mock.patch('PyQt5.QtWidgets.QMainWindow.activateWindow')
    @mock.patch('PyQt5.QtWidgets.QWidget.isVisible', return_value=True)
    def test_openAboutWindow_activated_if_visible(self, mock_vis, mock_activ):
        self.form.openAboutWindow()

        mock_activ.assert_called_once_with()

    """@mock.patch('doppelganger.preferenceswindow.PreferencesWindow')
    @mock.patch('doppelganger.mainwindow.MainWindow.findChildren', return_value=[])
    def test_openPreferencesWindow_init_PreferencesWindow(self, mock_form, mock_init):
        self.form.openPreferencesWindow()

        self.assertTrue(mock_init.called)"""

    @mock.patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory')
    def test_openFolderNameDialog(self, mock_dialog):
        self.form.openFolderNameDialog()

        self.assertTrue(mock_dialog.called)

    @mock.patch('doppelganger.mainwindow.webbrowser.open')
    def test_openDocs(self, mock_open):
        self.form.openDocs()

        mock_open.assert_called_once_with(
            'https://github.com/oratosquilla-oratoria/doppelganger'
        )

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_showErrMsg_calls_message_box(self, mock_msgbox):
        self.form.showErrMsg('test')

        self.assertTrue(mock_msgbox.called)

    def test_clearMainForm_no_group_widgets(self):
        self.form.clearMainForm()
        group_widgets = self.form.findChildren(widgets.ImageGroupWidget)

        self.assertFalse(group_widgets)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_render_empty_image_groups(self, mock_msgbox):
        self.form.render([])

        self.assertTrue(mock_msgbox.called)

    def test_render(self):
        image_groups = [[core.Image('image.jpg')]]
        self.form.render(image_groups)
        rendered_widgets = self.form.findChildren(widgets.ImageGroupWidget)

        self.assertEqual(len(rendered_widgets), len(image_groups))
        self.assertIsInstance(rendered_widgets[0], widgets.ImageGroupWidget)

    def test_hasSelectedWidgets_False(self):
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget([core.Image('image.png')], self.form.preferencesWindow.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)

        self.assertFalse(w.selected)

    def test_hasSelectedWidgets_True(self):
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget([core.Image('image.png')], self.form.preferencesWindow.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True

        self.assertTrue(w.selected)

    @mock.patch('doppelganger.mainwindow.MainWindow.hasSelectedWidgets', return_value=True)
    def test_switchButtons_called_when_signal_emitted(self, mock_has):
        self.form.moveBtn.setEnabled(False)
        self.form.deleteBtn.setEnabled(False)
        self.form.unselectBtn.setEnabled(False)
        self.form.render([[core.Image('image.png', 0)]])
        dw = self.form.findChild(widgets.DuplicateWidget)
        dw.signals.clicked.emit()

        self.assertTrue(self.form.moveBtn.isEnabled())
        self.assertTrue(self.form.deleteBtn.isEnabled())
        self.assertTrue(self.form.unselectBtn.isEnabled())

    @mock.patch('doppelganger.mainwindow.MainWindow.hasSelectedWidgets', return_value=True)
    def test_switchButtons_if_hasSelectedWidgets_True(self, mock_has):
        self.form.moveBtn.setEnabled(False)
        self.form.deleteBtn.setEnabled(False)
        self.form.unselectBtn.setEnabled(False)
        self.form.switchButtons()

        self.assertTrue(self.form.moveBtn.isEnabled())
        self.assertTrue(self.form.deleteBtn.isEnabled())
        self.assertTrue(self.form.unselectBtn.isEnabled())

    @mock.patch('doppelganger.mainwindow.MainWindow.hasSelectedWidgets', return_value=False)
    def test_switch_buttons_if_hasSelectedWidgets_False(self, mock_has):
        self.form.moveBtn.setEnabled(True)
        self.form.deleteBtn.setEnabled(True)
        self.form.unselectBtn.setEnabled(True)
        self.form.switchButtons()

        self.assertFalse(self.form.moveBtn.isEnabled())
        self.assertFalse(self.form.deleteBtn.isEnabled())
        self.assertFalse(self.form.unselectBtn.isEnabled())

    @mock.patch('doppelganger.mainwindow.MainWindow.switchButtons')
    @mock.patch('doppelganger.mainwindow.MainWindow._call_on_selected_widgets')
    def test_delete_images(self, mock_call, mock_switch):
        self.form.delete_images()

        self.assertTrue(mock_call.called)
        self.assertTrue(mock_switch.called)

    @mock.patch('doppelganger.mainwindow.MainWindow.switchButtons')
    @mock.patch('doppelganger.mainwindow.MainWindow._call_on_selected_widgets')
    @mock.patch('doppelganger.mainwindow.MainWindow.openFolderNameDialog', return_value='new_dst')
    def test_move_images(self, mock_dialog, mock_call, mock_switch):
        self.form.move_images()

        mock_call.assert_called_once_with('new_dst')
        self.assertTrue(mock_switch.called)

    @mock.patch('doppelganger.mainwindow.MainWindow.switchButtons')
    @mock.patch('doppelganger.mainwindow.MainWindow._call_on_selected_widgets')
    @mock.patch('doppelganger.mainwindow.MainWindow.openFolderNameDialog', return_value='')
    def test_move_images_doesnt_call_if_new_dest_empty(self, mock_dialog, mock_call, mock_switch):
        self.form.move_images()

        self.assertFalse(mock_call.called)
        self.assertFalse(mock_switch.called)

    def test_processing_finished(self):
        self.form.processingGrp.processProg.setValue(0)
        self.form.startBtn.setEnabled(False)
        self.form.stopBtn.setEnabled(True)
        self.form.autoSelectBtn.setEnabled(False)
        self.form.processing_finished()

        self.assertEqual(self.form.processingGrp.processProg.value(), 100)
        self.assertTrue(self.form.startBtn.isEnabled())
        self.assertFalse(self.form.stopBtn.isEnabled())
        self.assertTrue(self.form.autoSelectBtn.isEnabled())

    @mock.patch('doppelganger.processing.ImageProcessing')
    def test_start_processing_calls_ImageProcessing(self, mock_processing):
        self.form.start_processing([])

        self.assertTrue(mock_processing.called)

    @mock.patch('PyQt5.QtCore.QThreadPool.start')
    @mock.patch('doppelganger.processing.Worker')
    def test_start_processing_creates_Worker_n_thread(self, mock_worker, mock_thread):
        self.form.start_processing([])

        self.assertTrue(mock_worker.called)
        self.assertTrue(mock_thread.called)

    @mock.patch('doppelganger.mainwindow.MainWindow.clearMainForm')
    @mock.patch('doppelganger.mainwindow.MainWindow.start_processing')
    def test_startBtn_click_calls_clearMainForm(self, mock_processing, mock_clear):
        self.form.startBtn.setEnabled(True)
        self.form.stopBtn.setEnabled(False)
        self.form.autoSelectBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.startBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_clear.called)
        self.assertFalse(self.form.startBtn.isEnabled())
        self.assertTrue(self.form.stopBtn.isEnabled())
        self.assertFalse(self.form.autoSelectBtn.isEnabled())

    @mock.patch('doppelganger.mainwindow.MainWindow.start_processing')
    @mock.patch('doppelganger.pathsgroupbox.PathsGroupBox.paths', return_value=[])
    def test_startBtn_click_calls_start_processing(self, mock_folders, mock_processing):
        self.form.startBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.startBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_folders.called)
        self.assertTrue(mock_processing.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_stopBtn_click_emits_interrupt_signal(self, mock_msgbox):
        self.form.stopBtn.setEnabled(True)
        spy = QtTest.QSignalSpy(self.form.signals.interrupted)
        QtTest.QTest.mouseClick(self.form.stopBtn, QtCore.Qt.LeftButton)

        self.assertEqual(len(spy), 1)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_stopBtn_click_calls_message_box(self, mock_msgbox):
        self.form.stopBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.stopBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_msgbox.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_stopBtn_click_disables_stopBtn(self, mock_msgbox):
        self.form.stopBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.stopBtn, QtCore.Qt.LeftButton)

        self.assertFalse(self.form.delFolderBtn.isEnabled())

    @mock.patch('doppelganger.mainwindow.MainWindow.move_images')
    def test_moveBtn_click_calls_move_images(self, mock_move):
        self.form.moveBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.moveBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_move.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_deleteBtn_click_calls_message_box(self, mock_msgbox):
        self.form.deleteBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.deleteBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_msgbox.called)

    @mock.patch('doppelganger.mainwindow.MainWindow.delete_images')
    @mock.patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QtWidgets.QMessageBox.Yes)
    def test_deleteBtn_click_calls_delete_images(self, mock_msgbox, mock_del):
        self.form.deleteBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.deleteBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_del.called)

    @mock.patch('doppelganger.mainwindow.MainWindow.auto_select')
    def test_autoSelectBtn_click_calls_auto_select(self, mock_auto):
        self.form.autoSelectBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.autoSelectBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_auto.called)

    @mock.patch('doppelganger.mainwindow.MainWindow.unselect')
    def test_unselectBtn_click_calls_unselect(self, mock_un):
        self.form.unselectBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.unselectBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_un.called)
