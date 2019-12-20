'''Copyright 2019 Maxim Shpak <maxim.shpak@posteo.uk>

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

from doppelganger import config, core, gui, widgets

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


class TestAboutForm(TestCase):

    @mock.patch('doppelganger.gui.uic.loadUi')
    def test_init(self, mock_ui):
        form = gui.AboutForm()

        mock_ui.assert_called_once_with(gui.ABOUT_UI, form)

    @mock.patch('doppelganger.gui.AboutForm.deleteLater')
    @mock.patch('PyQt5.QtWidgets.QMainWindow.closeEvent')
    def test_closeEvent(self, mock_close, mock_delete):
        form = gui.AboutForm()
        form.close()

        self.assertTrue(mock_close.called)
        self.assertTrue(mock_delete.called)


class TestPreferencesForm(TestCase):

    class P(QtWidgets.QWidget):
        conf = {'delete_dirs': True,
                'show_path': True,
                'show_similarity': True,
                'show_size': True,
                'size_format': 'MB',
                'size': 666,
                'sort': 1,
                'subfolders': True}

    def setUp(self):
        self.p = self.P()
        self.form = gui.PreferencesForm(parent=self.p)

    def clear_form(self):
        self.form.sizeSpinBox.setValue(333)
        self.form.sortComboBox.setCurrentIndex(0)
        self.form.similarityBox.setChecked(False)
        self.form.sizeBox.setChecked(False)
        self.form.pathBox.setChecked(False)
        self.form.deldirsBox.setChecked(False)
        self.form.sizeFormatComboBox.setCurrentIndex(0)
        self.form.subfoldersBox.setChecked(False)

    @mock.patch('doppelganger.gui.PreferencesForm._setWidgetEvents')
    @mock.patch('doppelganger.gui.PreferencesForm._update_form')
    @mock.patch('PyQt5.QtWidgets.QComboBox.addItems')
    def test_init(self, mock_combobox, mock_update, mock_events):
        f = gui.PreferencesForm(self.p)

        sort = ['Similarity rate',
                'Filesize',
                'Width and Height',
                'Path']

        size_format = ['Bytes (B)',
                       'KiloBytes (KB)',
                       'MegaBytes (MB)']

        mock_combobox.assert_any_call(sort)
        mock_combobox.assert_any_call(size_format)
        self.assertEqual(f.sizeSpinBox.minimum(), 100)
        self.assertEqual(f.sizeSpinBox.maximum(), 4000)
        mock_update.assert_called_once()
        mock_events.assert_called_once()

    @mock.patch('doppelganger.gui.PreferencesForm.deleteLater')
    @mock.patch('PyQt5.QtWidgets.QMainWindow.closeEvent')
    def test_closeEvent(self, mock_close, mock_delete):
        self.form.close()

        self.assertTrue(mock_close.called)
        self.assertTrue(mock_delete.called)

    def test_update_form(self):
        self.clear_form()
        data = self.p.conf

        self.form._update_form(data)

        self.assertEqual(data['size'], self.form.sizeSpinBox.value())
        self.assertEqual(data['sort'], self.form.sortComboBox.currentIndex())
        self.assertEqual(data['show_similarity'], self.form.similarityBox.isChecked())
        self.assertEqual(data['show_size'], self.form.sizeBox.isChecked())
        self.assertEqual(data['show_path'], self.form.pathBox.isChecked())
        self.assertEqual(data['delete_dirs'], self.form.deldirsBox.isChecked())
        self.assertEqual(data['subfolders'], self.form.subfoldersBox.isChecked())

    def test_gather_prefs(self):
        self.clear_form()
        data = {'delete_dirs': False,
                'show_path': False,
                'show_similarity': False,
                'show_size': False,
                'size': 333,
                'sort': 0,
                'size_format': 'B',
                'subfolders': False}

        gathered_data = self.form._gather_prefs()

        self.assertDictEqual(data, gathered_data)

    @mock.patch('PyQt5.QtWidgets.QMainWindow.deleteLater')
    @mock.patch('doppelganger.config.Config.save')
    @mock.patch('doppelganger.gui.PreferencesForm._gather_prefs', return_value={})
    def test_saveBtn_click(self, mock_prefs, mock_save, mock_del):
        QtTest.QTest.mouseClick(self.form.saveBtn, QtCore.Qt.LeftButton)

        mock_prefs.assert_called_once()
        mock_save.assert_called_once()
        mock_del.assert_called_once()
        self.assertDictEqual(self.p.conf, {})

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.config.Config.save', side_effect=OSError)
    @mock.patch('doppelganger.gui.PreferencesForm._gather_prefs', return_value={})
    def test_saveBtn_click_if_raise_OSError(self, mock_prefs, mock_save, mock_exec):
        QtTest.QTest.mouseClick(self.form.saveBtn, QtCore.Qt.LeftButton)

        mock_prefs.assert_called_once()
        mock_save.assert_called_once()
        mock_exec.assert_called_once()

    @mock.patch('PyQt5.QtWidgets.QMainWindow.deleteLater')
    def test_cancelBtn_click(self, mock_del):
        QtTest.QTest.mouseClick(self.form.cancelBtn, QtCore.Qt.LeftButton)

        mock_del.assert_called_once()


class TestMainForm(TestCase):

    def setUp(self):
        self.conf = config.Config.DEFAULT_CONFIG_DATA.copy()
        with mock.patch('doppelganger.gui.MainForm._load_prefs') as mock_load:
            mock_load.return_value = self.conf

            self.form = gui.MainForm()

    @mock.patch('doppelganger.gui.MainForm._load_prefs')
    @mock.patch('doppelganger.gui.MainForm._setMenubar')
    @mock.patch('doppelganger.gui.QtWidgets.QRadioButton.click')
    @mock.patch('doppelganger.gui.MainForm._setWidgetEvents')
    def test_init(self, mock_events, mock_button, mock_menubar, mock_load):
        form = gui.MainForm()
        scroll_area_align = form.scrollAreaLayout.layout().alignment()
        self.assertEqual(scroll_area_align, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.assertIsInstance(form.threadpool, QtCore.QThreadPool)
        self.assertTrue(mock_events.called)
        self.assertTrue(mock_button.called)
        self.assertTrue(mock_menubar.called)
        self.assertTrue(mock_load.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.config.Config.load', side_effect=OSError)
    def test_load_prefs_if_raise_OSError(self, mock_conf, mock_exec):
        conf = self.form._load_prefs()

        mock_exec.assert_called_once()
        self.assertDictEqual(conf, self.conf)

    def test_init_menubar_disabled_enabled_menus(self):
        enabled = {'File', 'Edit', 'Options', 'Help'}
        for menu in self.form.menubar.findChildren(QtWidgets.QMenu):
            if menu.title() in enabled:
                self.assertTrue(menu.isEnabled())

    @mock.patch('doppelganger.gui.AboutForm')
    @mock.patch('doppelganger.gui.MainForm.findChildren', return_value=[])
    def test_help_menu_calls_openAboutForm(self, mock_form, mock_init):
        aboutAction = self.form.findChild(QtWidgets.QAction, 'aboutAction')
        aboutAction.trigger()

        self.assertTrue(mock_init.called)

    @mock.patch('doppelganger.gui.PreferencesForm')
    @mock.patch('doppelganger.gui.MainForm.findChildren', return_value=[])
    def test_options_menu_calls_openPreferencesForm(self, mock_form, mock_init):
        preferencesAction = self.form.findChild(QtWidgets.QAction, 'preferencesAction')
        preferencesAction.trigger()

        self.assertTrue(mock_init.called)

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
            widgets.ImageGroupWidget(image_group, self.form.conf)
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
            widgets.ImageGroupWidget(image_group, self.form.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True
        with self.assertLogs('main.gui', 'ERROR'):
            self.form._call_on_selected_widgets()

        mock_delete.assert_called_once()
        self.assertTrue(mock_box.called)

    @mock.patch('doppelganger.core.Image.del_parent_dir')
    @mock.patch('doppelganger.widgets.DuplicateWidget.delete')
    def test_call_on_selected_widgets_delete_empty_dir(self, mock_delete, mock_dir):
        image_group = [core.Image('img1.png')]
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget(image_group, self.form.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True
        self.form.conf['delete_dirs'] = True

        self.form._call_on_selected_widgets()

        self.assertTrue(mock_dir.called)

    @mock.patch('doppelganger.core.Image.del_parent_dir')
    @mock.patch('doppelganger.widgets.DuplicateWidget.delete')
    def test_call_on_selected_widgets_not_delete_empty_dir(self, mock_delete, mock_dir):
        image_group = [core.Image('img1.png')]
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget(image_group, self.form.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True
        self.form.conf['delete_dirs'] = False

        self.form._call_on_selected_widgets()

        self.assertFalse(mock_dir.called)

    @mock.patch('doppelganger.widgets.ImageGroupWidget.deleteLater')
    def test_call_on_selected_widgets_deleteLater_on_ImageGroupWidget(self, mock_later):
        image_group = [core.Image('img1.png')]
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget(image_group, self.form.conf)
        )
        self.form._call_on_selected_widgets()

        mock_later.assert_called_once()

    @mock.patch('doppelganger.gui.AboutForm')
    @mock.patch('doppelganger.gui.MainForm.findChildren', return_value=[])
    def test_openAboutForm_init_AboutForm(self, mock_form, mock_init):
        self.form.openAboutForm()

        self.assertTrue(mock_init.called)

    @mock.patch('doppelganger.gui.AboutForm.show')
    @mock.patch('doppelganger.gui.MainForm.findChildren', return_value=[])
    def test_openAboutForm_show_AboutForm(self, mock_form, mock_show):
        self.form.openAboutForm()

        self.assertTrue(mock_show.called)

    @mock.patch('doppelganger.gui.AboutForm.activateWindow')
    def test_openAboutForm_opened(self, mock_activate):
        gui.AboutForm(self.form)
        self.form.openAboutForm()

        self.assertTrue(mock_activate.called)

    @mock.patch('doppelganger.gui.PreferencesForm')
    @mock.patch('doppelganger.gui.MainForm.findChildren', return_value=[])
    def test_openPreferencesForm_init_PreferencesForm(self, mock_form, mock_init):
        self.form.openPreferencesForm()

        self.assertTrue(mock_init.called)

    @mock.patch('doppelganger.gui.PreferencesForm.show')
    @mock.patch('doppelganger.gui.MainForm.findChildren', return_value=[])
    def test_openPreferencesForm_show_PreferencesForm(self, mock_form, mock_show):
        self.form.openPreferencesForm()

        self.assertTrue(mock_show.called)

    @mock.patch('doppelganger.gui.PreferencesForm.activateWindow')
    def test_openPreferencesForm_opened(self, mock_activate):
        gui.PreferencesForm(self.form)
        self.form.openPreferencesForm()

        self.assertTrue(mock_activate.called)

    @mock.patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory')
    def test_openFolderNameDialog(self, mock_dialog):
        self.form.openFolderNameDialog()

        self.assertTrue(mock_dialog.called)

    @mock.patch('doppelganger.gui.webbrowser.open')
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

    def test_clearMainForm_labels(self):
        labels = (self.form.thumbnailsLabel, self.form.dupGroupLabel,
                  self.form.remainingPicLabel, self.form.foundInCacheLabel,
                  self.form.loadedPicLabel, self.form.duplicatesLabel)

        for label in labels:
            t = label.text().split(' ')
            t[-1] = 'ugauga'
            label.setText(' '.join(t))

        self.form.clearMainForm()

        for label in labels:
            num = label.text().split(' ')[-1]
            self.assertEqual(num, str(0))

    def test_clearMainForm_progress_bar(self):
        self.form.progressBar.setValue(13)
        self.form.clearMainForm()

        self.assertEqual(self.form.progressBar.value(), 0)

    def test_getFolders(self):
        self.form.pathListWidget.addItem('item')
        expected = {'item'}
        result = self.form.getFolders()

        self.assertSetEqual(result, expected)

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

    def test_updateLabel(self):
        labels = {'thumbnails': self.form.thumbnailsLabel,
                  'image_groups': self.form.dupGroupLabel,
                  'remaining_images': self.form.remainingPicLabel,
                  'found_in_cache': self.form.foundInCacheLabel,
                  'loaded_images': self.form.loadedPicLabel,
                  'duplicates': self.form.duplicatesLabel}

        for label in labels:
            prev_text = labels[label].text().split(' ')[:-1]
            self.form.updateLabel(label, 'text')
            self.assertEqual(labels[label].text(), ' '.join(prev_text) + ' text')

    def test_hasSelectedWidgets_False(self):
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget([core.Image('image.png')], self.form.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)

        self.assertFalse(w.selected)

    def test_hasSelectedWidgets_True(self):
        self.form.scrollAreaLayout.addWidget(
            widgets.ImageGroupWidget([core.Image('image.png')], self.form.conf)
        )
        w = self.form.findChild(widgets.DuplicateWidget)
        w.selected = True

        self.assertTrue(w.selected)

    @mock.patch('doppelganger.gui.MainForm.hasSelectedWidgets', return_value=True)
    def test_switchButtons_called_when_signal_emitted(self, mock_has):
        self.form.moveBtn.setEnabled(False)
        self.form.deleteBtn.setEnabled(False)
        self.form.render([[core.Image('image.png', 0)]])
        dw = self.form.findChild(widgets.DuplicateWidget)
        dw.signals.clicked.emit()

        self.assertTrue(self.form.moveBtn.isEnabled())
        self.assertTrue(self.form.deleteBtn.isEnabled())

    @mock.patch('doppelganger.gui.MainForm.hasSelectedWidgets', return_value=True)
    def test_switchButtons_if_hasSelectedWidgets_True(self, mock_has):
        self.form.moveBtn.setEnabled(False)
        self.form.deleteBtn.setEnabled(False)
        self.form.switchButtons()

        self.assertTrue(self.form.moveBtn.isEnabled())
        self.assertTrue(self.form.deleteBtn.isEnabled())

    @mock.patch('doppelganger.gui.MainForm.hasSelectedWidgets', return_value=False)
    def test_switch_buttons_if_hasSelectedWidgets_False(self, mock_has):
        self.form.moveBtn.setEnabled(True)
        self.form.deleteBtn.setEnabled(True)
        self.form.switchButtons()

        self.assertFalse(self.form.moveBtn.isEnabled())
        self.assertFalse(self.form.deleteBtn.isEnabled())

    @mock.patch('doppelganger.gui.MainForm.openFolderNameDialog', return_value='path')
    def test_add_folder(self, mock_dialog):
        self.form.add_folder()
        result = self.form.pathListWidget.item(0).data(QtCore.Qt.DisplayRole)

        self.assertEqual(result, 'path')

    @mock.patch('doppelganger.gui.MainForm.openFolderNameDialog')
    def test_add_folder_enable_buttons(self, mock_dialog):
        self.form.add_folder()

        self.assertTrue(self.form.delFolderBtn.isEnabled())
        self.assertTrue(self.form.startBtn.isEnabled())

    def test_del_folder(self):
        self.form.pathListWidget.addItem('item')
        self.form.pathListWidget.item(0).setSelected(True)
        self.form.del_folder()

        self.assertEqual(self.form.pathListWidget.count(), 0)

    @mock.patch('PyQt5.QtWidgets.QListWidget.count', return_value=0)
    def test_del_folder_disables_buttons(self, mock_folder):
        self.form.del_folder()

        self.assertFalse(self.form.delFolderBtn.isEnabled())
        self.assertFalse(self.form.startBtn.isEnabled())

    @mock.patch('doppelganger.gui.MainForm.switchButtons')
    @mock.patch('doppelganger.gui.MainForm._call_on_selected_widgets')
    def test_delete_images(self, mock_call, mock_switch):
        self.form.delete_images()

        self.assertTrue(mock_call.called)
        self.assertTrue(mock_switch.called)

    @mock.patch('doppelganger.gui.MainForm.switchButtons')
    @mock.patch('doppelganger.gui.MainForm._call_on_selected_widgets')
    @mock.patch('doppelganger.gui.MainForm.openFolderNameDialog', return_value='new_dst')
    def test_move_images(self, mock_dialog, mock_call, mock_switch):
        self.form.move_images()

        mock_call.assert_called_once_with('new_dst')
        self.assertTrue(mock_switch.called)

    @mock.patch('doppelganger.gui.MainForm.switchButtons')
    @mock.patch('doppelganger.gui.MainForm._call_on_selected_widgets')
    @mock.patch('doppelganger.gui.MainForm.openFolderNameDialog', return_value='')
    def test_move_images_doesnt_call_if_new_dest_empty(self, mock_dialog, mock_call, mock_switch):
        self.form.move_images()

        self.assertFalse(mock_call.called)
        self.assertFalse(mock_switch.called)

    def test_processing_finished(self):
        self.form.progressBar.setValue(0)
        self.form.startBtn.setEnabled(False)
        self.form.stopBtn.setEnabled(True)
        self.form.processing_finished()

        self.assertEqual(self.form.progressBar.value(), 100)
        self.assertTrue(self.form.startBtn.isEnabled())
        self.assertFalse(self.form.stopBtn.isEnabled())

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

    def test_highRb_click(self):
        self.form.sensitivity = 0
        self.form.show() # some bug: if show() is not used, mouseClick() do nothing
        QtTest.QTest.mouseClick(self.form.highRb, QtCore.Qt.LeftButton)

        self.assertEqual(self.form.sensitivity, 5)

    def test_mediumRb_click(self):
        self.form.sensitivity = 0
        #self.form.show() # some bug: if show() is not used, mouseClick() do nothing
        QtTest.QTest.mouseClick(self.form.mediumRb, QtCore.Qt.LeftButton)

        self.assertEqual(self.form.sensitivity, 10)

    def test_lowRb_click(self):
        self.form.sensitivity = 0
        self.form.show() # some bug: if show() is not used, mouseClick() do nothing
        QtTest.QTest.mouseClick(self.form.lowRb, QtCore.Qt.LeftButton)

        self.assertEqual(self.form.sensitivity, 20)

    @mock.patch('doppelganger.gui.MainForm.add_folder')
    def test_addFolderBtn_click(self, mock_folder):
        QtTest.QTest.mouseClick(self.form.addFolderBtn, QtCore.Qt.LeftButton)

        mock_folder.assert_called_once()

    @mock.patch('doppelganger.gui.MainForm.del_folder')
    def test_delFolderBtn_click(self, mock_folder):
        self.form.delFolderBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.delFolderBtn, QtCore.Qt.LeftButton)

        mock_folder.assert_called_once()

    @mock.patch('doppelganger.gui.MainForm.clearMainForm')
    @mock.patch('doppelganger.gui.MainForm.start_processing')
    def test_startBtn_click_calls_clearMainForm(self, mock_processing, mock_clear):
        self.form.startBtn.setEnabled(True)
        self.form.stopBtn.setEnabled(False)
        QtTest.QTest.mouseClick(self.form.startBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_clear.called)
        self.assertFalse(self.form.startBtn.isEnabled())
        self.assertTrue(self.form.stopBtn.isEnabled())

    @mock.patch('doppelganger.gui.MainForm.start_processing')
    @mock.patch('doppelganger.gui.MainForm.getFolders', return_value=[])
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

    @mock.patch('doppelganger.gui.MainForm.move_images')
    def test_moveBtn_click_calls_move_images(self, mock_move):
        self.form.moveBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.moveBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_move.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_deleteBtn_click_calls_message_box(self, mock_msgbox):
        self.form.deleteBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.deleteBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_msgbox.called)

    @mock.patch('doppelganger.gui.MainForm.delete_images')
    @mock.patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QtWidgets.QMessageBox.Yes)
    def test_deleteBtn_click_calls_delete_images(self, mock_msgbox, mock_del):
        self.form.deleteBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.deleteBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_del.called)
