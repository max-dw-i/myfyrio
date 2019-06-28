import sys
from unittest import TestCase, mock

from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

from doppelganger import core, gui, processing


app = QtWidgets.QApplication(sys.argv)


class TestInfoLabelWidget(TestCase):

    def test_init(self):
        text = 'test'
        w = gui.InfoLabelWidget(text)

        self.assertEqual(w.text(), text)
        self.assertEqual(w.alignment(), QtCore.Qt.AlignHCenter)


class TestSimilarityLabel(TestInfoLabelWidget):
    '''The same test as for TestInfoLabelWidget'''


class ImageSizeLabel(TestInfoLabelWidget):
    '''The same test as for TestInfoLabelWidget'''


class ImagePathLabel(TestCase):

    @mock.patch('doppelganger.gui.QFileInfo.canonicalFilePath', return_value='test')
    def test_init(self, mock_path):
        text = 'test'
        w = gui.ImagePathLabel(text)

        self.assertTrue(w.isReadOnly())
        self.assertEqual(w.frameStyle(), QtWidgets.QFrame.NoFrame)
        self.assertEqual(w.verticalScrollBarPolicy(), QtCore.Qt.ScrollBarAlwaysOff)
        self.assertEqual(w.palette().color(QtGui.QPalette.Base), QtCore.Qt.transparent)
        self.assertEqual(w.toPlainText(), text)
        self.assertEqual(w.alignment(), QtCore.Qt.AlignCenter)


class TestImageInfoWidget(TestCase):

    @mock.patch('doppelganger.gui.QFileInfo.canonicalFilePath', return_value='path')
    def test_init(self, mock_path):
        path, difference, dimensions, filesize = 'path', 0, (1, 2), 3
        w = gui.ImageInfoWidget(path, difference, dimensions, filesize)

        similarity_label = w.findChildren(
            gui.SimilarityLabel,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]
        image_size_label = w.findChildren(
            gui.ImageSizeLabel,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]
        image_path_label = w.findChildren(
            gui.ImagePathLabel,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]

        self.assertEqual(w.layout().alignment(), QtCore.Qt.AlignBottom)
        self.assertEqual(similarity_label.text(), str(difference))
        self.assertEqual(image_size_label.text(), '1x2, 3 KB')
        self.assertEqual(image_path_label.toPlainText(), path)

    def test_get_image_size(self):
        result = gui.ImageInfoWidget._get_image_size((1, 2), 3)
        expected = '1x2, 3 KB'

        self.assertEqual(result, expected)


class TestThumbnailWidget(TestCase):

    @mock.patch('doppelganger.gui.ThumbnailWidget._QByteArray_to_QPixmap', return_value='pixmap')
    @mock.patch('doppelganger.gui.ThumbnailWidget.setPixmap')
    def test_init(self, mock_set, mock_pixmap):
        th = 'thumbnail'
        w = gui.ThumbnailWidget(th)

        self.assertEqual(w.alignment(), QtCore.Qt.AlignHCenter)
        mock_pixmap.assert_called_once_with(th)
        mock_set.assert_called_once_with('pixmap')
        self.assertTrue(mock_set.called)

    @mock.patch('doppelganger.gui.QPixmap')
    def test_QByteArray_to_QPixmap_returns_error_image_if_thumbnail_is_None(self, mock_qp):
        gui.ThumbnailWidget._QByteArray_to_QPixmap(None)

        mock_qp.assert_called_once_with(gui.IMAGE_ERROR)

    def test_QByteArray_to_QPixmap_returns_QPixmap_obj_if_thumbnail_is_None(self):
        qp = gui.ThumbnailWidget._QByteArray_to_QPixmap(None)

        self.assertIsInstance(qp, QtGui.QPixmap)

    @mock.patch('doppelganger.gui.QPixmap')
    @mock.patch('doppelganger.gui.QPixmap.isNull', return_value=True)
    @mock.patch('doppelganger.gui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_error_image_if_isNull(
            self, mock_load, mock_null, mock_qp
        ):
        gui.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail')

        mock_qp.assert_called_with(gui.IMAGE_ERROR)

    @mock.patch('doppelganger.gui.QPixmap.isNull', return_value=True)
    @mock.patch('doppelganger.gui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_QPixmap_obj_if_isNull(self, mock_load, mock_null):
        qp = gui.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail')

        self.assertIsInstance(qp, QtGui.QPixmap)

    @mock.patch('doppelganger.gui.QPixmap.isNull', return_value=False)
    @mock.patch('doppelganger.gui.QPixmap.loadFromData')
    def test_QByteArray_to_QPixmap_returns_QPixmap_obj(self, mock_load, mock_null):
        qp = gui.ThumbnailWidget._QByteArray_to_QPixmap('thumbnail')

        self.assertIsInstance(qp, QtGui.QPixmap)

    @mock.patch('doppelganger.gui.ThumbnailWidget._QByteArray_to_QPixmap')
    @mock.patch('doppelganger.gui.ThumbnailWidget.setPixmap')
    def test_unmark(self, mock_set, mock_qp):
        w = gui.ThumbnailWidget('thumbnail')
        w.unmark()

        mock_set.assert_called_with(w.pixmap)

    @mock.patch('doppelganger.gui.ThumbnailWidget._QByteArray_to_QPixmap')
    @mock.patch('doppelganger.gui.ThumbnailWidget.setPixmap')
    def test_mark(self, mock_set, mock_qp):
        w = gui.ThumbnailWidget('thumbnail')
        w.unmark()

        self.assertTrue(mock_qp.called)


class TestDuplicateCandidateWidget(TestCase):

    def setUp(self):
        self.path, self.difference = 'image.png', 1
        self.image = core.Image(self.path, self.difference)
        self.w = gui.DuplicateCandidateWidget(self.image)

    def test_init(self):
        self.assertEqual(self.w.width(), 200)
        self.assertIsInstance(self.w.layout(), QtWidgets.QVBoxLayout)
        self.assertEqual(self.w.image, self.image)
        self.assertFalse(self.w.selected)

    @mock.patch('doppelganger.gui.DuplicateCandidateWidget._setWidgetEvents')
    def test_init_calls_setWidgetEvents(self, mock_events):
        gui.DuplicateCandidateWidget(core.Image('image.png'))

        self.assertTrue(mock_events.called)

    def test_ThumbnailWidget_n_ImageInfoWidget_in_DuplicateCandidateWidget(self):
        th_widgets = self.w.findChildren(
            gui.ThumbnailWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        info_widgets = self.w.findChildren(
            gui.ImageInfoWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        self.assertEqual(len(th_widgets), 1)
        self.assertEqual(len(info_widgets), 1)

    @mock.patch('doppelganger.core.Image.get_filesize', return_value=3)
    @mock.patch('doppelganger.core.Image.get_dimensions', side_effect=OSError)
    @mock.patch('doppelganger.gui.ImageInfoWidget')
    def test_widgets_if_get_dimensions_raises_OSError(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, (0, 0), 3)

    @mock.patch('doppelganger.core.Image.get_filesize', side_effect=OSError)
    @mock.patch('doppelganger.core.Image.get_dimensions', return_value=2)
    @mock.patch('doppelganger.gui.ImageInfoWidget')
    def test_widgets_if_get_filesize_raises_OSError(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, 2, 0)

    @mock.patch('doppelganger.core.Image.get_filesize', return_value=3)
    @mock.patch('doppelganger.core.Image.get_dimensions', return_value=2)
    @mock.patch('doppelganger.gui.ImageInfoWidget')
    def test_widgets_ImageInfoWidget_called_with_what_args(self, mock_info, mock_dim, mock_size):
        self.w._widgets()

        mock_info.assert_called_once_with(self.path, self.difference, 2, 3)

    @mock.patch('doppelganger.gui.ThumbnailWidget')
    def test_widgets_calls_ThumbnailWidget(self, mock_th):
        self.w._widgets()

        self.assertTrue(mock_th.called)

    def test_setWidgetEvents(self):
        self.w._setWidgetEvents()

        self.assertIsInstance(self.w.mouseReleaseEvent, type(self.w._mouseRelease))

    @mock.patch('doppelganger.gui.MainForm.has_selected_widgets', return_value=False)
    @mock.patch('doppelganger.gui.ThumbnailWidget.unmark')
    def test_mouseRelease_on_selected_widget(self, mock_unmark, mock_selected):
        mw = gui.MainForm()
        mw.scrollAreaLayout.addWidget(self.w)
        self.w.selected = True
        self.w._mouseRelease('event')

        self.assertFalse(self.w.selected)
        self.assertTrue(mock_unmark.called)
        self.assertFalse(mw.deleteBtn.isEnabled())

    @mock.patch('doppelganger.gui.ThumbnailWidget.mark')
    def test_mouseRelease_on_unselected_widget(self, mock_mark):
        mw = gui.MainForm()
        mw.scrollAreaLayout.addWidget(self.w)
        self.w.selected = False
        self.w._mouseRelease('event')

        self.assertTrue(self.w.selected)
        self.assertTrue(mock_mark.called)
        self.assertTrue(mw.deleteBtn.isEnabled())

    @mock.patch('PyQt5.QtCore.QObject.deleteLater')
    @mock.patch('doppelganger.core.Image.delete_image')
    def test_delete_normal_flow(self, mock_img, mock_later):
        self.w.delete()

        self.assertTrue(mock_img.called)
        self.assertTrue(mock_later.called)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    @mock.patch('doppelganger.core.Image.delete_image', side_effect=OSError)
    def test_delete_show_message_box(self, mock_img, mock_box):
        self.w.delete()

        self.assertTrue(mock_box.called)


class TestImageGroupWidget(TestCase):

    def setUp(self):
        self.w = gui.ImageGroupWidget([core.Image('image.png')])

    def test_widget_alignment(self):
        l = self.w.layout()

        self.assertEqual(l.alignment(), QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def test_number_of_created_widgets(self):
        widget = self.w.findChildren(
            gui.DuplicateCandidateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        self.assertEqual(len(self.w), len(widget))

    def test_getSelectedWidgets(self):
        widgets = self.w.findChildren(
            gui.DuplicateCandidateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        widgets[0].selected = True

        self.assertListEqual(self.w.getSelectedWidgets(), widgets)

    def test_len(self):
        self.w = gui.ImageGroupWidget([core.Image('image.png')])

        self.assertEqual(len(self.w), 1)


class TestMainForm(TestCase):

    def setUp(self):
        self.form = gui.MainForm()

    def test_init(self):
        self.assertIsInstance(self.form.threadpool, QtCore.QThreadPool)
        self.assertIsInstance(self.form.signals, processing.Signals)
        self.assertEqual(self.form.sensitivity, 5)

    @mock.patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory')
    def test_openFolderNameDialog(self, mock_dialog):
        self.form._openFolderNameDialog()

        self.assertTrue(mock_dialog.called)

    def test_clear_form_before_start_no_group_widgets(self):
        self.form._clear_form_before_start()

        group_widgets = self.form.scrollAreaWidget.findChildren(
            gui.ImageGroupWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        self.assertFalse(group_widgets)

    def test_clear_form_before_start_labels(self):
        labels = (self.form.thumbnailsLabel, self.form.dupGroupLabel,
                  self.form.remainingPicLabel, self.form.foundInCacheLabel,
                  self.form.loadedPicLabel)

        for label in labels:
            t = label.text().split(' ')
            t[-1] = 'ugauga'
            label.setText(' '.join(t))

        self.form._clear_form_before_start()

        for label in labels:
            num = label.text().split(' ')[-1]
            self.assertEqual(num, str(0))

    def test_clear_form_before_start_progress_bar(self):
        self.form.progressBar.setValue(13)
        self.form._clear_form_before_start()

        self.assertEqual(self.form.progressBar.value(), 0)

    def test_get_user_folders(self):
        self.form.pathListWidget.addItem('item')
        expected = ['item']
        result = self.form._get_user_folders()

        self.assertListEqual(result, expected)

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_render_image_groups_empty_image_groups(self, mock_msgbox):
        self.form._render_image_groups([])

        self.assertTrue(mock_msgbox.called)

    def test_render_image_groups(self):
        image_groups = [[core.Image('image.jpg')]]
        self.form._render_image_groups(image_groups)

        rendered_widgets = self.form.scrollAreaWidget.findChildren(
            gui.ImageGroupWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )

        self.assertEqual(len(rendered_widgets), len(image_groups))
        self.assertIsInstance(rendered_widgets[0], gui.ImageGroupWidget)

    def test_update_label_info(self):
        labels = {'thumbnails': self.form.thumbnailsLabel,
                  'image_groups': self.form.dupGroupLabel,
                  'remaining_images': self.form.remainingPicLabel,
                  'found_in_cache': self.form.foundInCacheLabel,
                  'loaded_images': self.form.loadedPicLabel}

        for label in labels:
            prev_text = labels[label].text().split(' ')[:-1]
            self.form._update_label_info(label, 'text')
            self.assertEqual(labels[label].text(), ' '.join(prev_text) + ' text')

    def test_has_selected_widgets_False(self):
        self.form.scrollAreaLayout.addWidget(gui.ImageGroupWidget([core.Image('image.png')]))
        group_widget = self.form.scrollAreaWidget.findChildren(
            gui.ImageGroupWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]
        image_widget = group_widget.findChildren(
            gui.DuplicateCandidateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]

        self.assertFalse(image_widget.selected)

    def test_has_selected_widgets_True(self):
        self.form.scrollAreaLayout.addWidget(gui.ImageGroupWidget([core.Image('image.png')]))
        group_widget = self.form.scrollAreaWidget.findChildren(
            gui.ImageGroupWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]
        image_widget = group_widget.findChildren(
            gui.DuplicateCandidateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]
        image_widget.selected = True

        self.assertTrue(image_widget.selected)

    def test_image_processing_finished(self):
        self.form.progressBar.setValue(0)
        self.form.startBtn.setEnabled(False)
        self.form.stopBtn.setEnabled(True)
        self.form._image_processing_finished()

        self.assertEqual(self.form.progressBar.value(), 100)
        self.assertTrue(self.form.startBtn.isEnabled())
        self.assertFalse(self.form.stopBtn.isEnabled())

    @mock.patch('PyQt5.QtWidgets.QWidget.deleteLater')
    @mock.patch('doppelganger.gui.DuplicateCandidateWidget.delete')
    def test_delete_selected_widgets_not_selected_more_than_one(self, mock_del, mock_later):
        image_group = [core.Image('img1.png'), core.Image('img2.png'), core.Image('img3.png')]
        self.form.scrollAreaLayout.addWidget(gui.ImageGroupWidget(image_group))
        group_widget = self.form.scrollAreaWidget.findChildren(
            gui.ImageGroupWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]
        image_widgets = group_widget.findChildren(
            gui.DuplicateCandidateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        image_widgets[0].selected = True
        self.form._delete_selected_widgets()

        self.assertEqual(mock_del.call_count, 1)
        self.assertFalse(mock_later.called)

    @mock.patch('PyQt5.QtWidgets.QWidget.deleteLater')
    @mock.patch('doppelganger.gui.DuplicateCandidateWidget.delete')
    def test_delete_selected_widgets_not_selected_less_than_two(self, mock_del, mock_later):
        image_group = [core.Image('img1.png'), core.Image('img2.png'), core.Image('img3.png')]
        self.form.scrollAreaLayout.addWidget(gui.ImageGroupWidget(image_group))
        group_widget = self.form.scrollAreaWidget.findChildren(
            gui.ImageGroupWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )[0]
        image_widgets = group_widget.findChildren(
            gui.DuplicateCandidateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        image_widgets[0].selected = True
        image_widgets[1].selected = True
        self.form._delete_selected_widgets()

        self.assertEqual(mock_del.call_count, 2)
        self.assertTrue(mock_later.called)

    @mock.patch('doppelganger.processing.ImageProcessing')
    def test_start_processing_calls_ImageProcessing(self, mock_processing):
        self.form._start_processing([])

        self.assertTrue(mock_processing.called)

    @mock.patch('PyQt5.QtCore.QThreadPool.start')
    @mock.patch('doppelganger.processing.Worker')
    def test_start_processing_creates_Worker_n_thread(self, mock_worker, mock_thread):
        self.form._start_processing([])

        self.assertTrue(mock_worker.called)
        self.assertTrue(mock_thread.called)

    def test_highRb_click(self):
        self.form.sensitivity = 0
        self.form.show() # some bug: if sho() is not used, mouseClick() do nothing
        QtTest.QTest.mouseClick(self.form.highRb, QtCore.Qt.LeftButton)

        self.assertEqual(self.form.sensitivity, 5)

    def test_mediumRb_click(self):
        self.form.sensitivity = 0
        #self.form.show() # some bug: if sho() is not used, mouseClick() do nothing
        QtTest.QTest.mouseClick(self.form.mediumRb, QtCore.Qt.LeftButton)

        self.assertEqual(self.form.sensitivity, 10)

    def test_lowRb_click(self):
        self.form.sensitivity = 0
        self.form.show() # some bug: if sho() is not used, mouseClick() do nothing
        QtTest.QTest.mouseClick(self.form.lowRb, QtCore.Qt.LeftButton)

        self.assertEqual(self.form.sensitivity, 20)

    @mock.patch('doppelganger.gui.MainForm._openFolderNameDialog', return_value='path')
    def test_addFolderBtn_click(self, mock_dialog):
        self.form.delFolderBtn.setEnabled(False)
        QtTest.QTest.mouseClick(self.form.addFolderBtn, QtCore.Qt.LeftButton)
        result = self.form.pathListWidget.item(0).data(QtCore.Qt.DisplayRole)

        self.assertEqual(result, 'path')

    @mock.patch('doppelganger.gui.MainForm._openFolderNameDialog')
    def test_addFolderBtn_click_enables_delFolderBtn(self, mock_dialog):
        self.form.delFolderBtn.setEnabled(False)
        QtTest.QTest.mouseClick(self.form.addFolderBtn, QtCore.Qt.LeftButton)

        self.assertTrue(self.form.delFolderBtn.isEnabled())

    def test_delFolderBtn_click(self):
        self.form.delFolderBtn.setEnabled(True)
        self.form.pathListWidget.addItem('item')
        self.form.pathListWidget.item(0).setSelected(True)
        QtTest.QTest.mouseClick(self.form.delFolderBtn, QtCore.Qt.LeftButton)

        self.assertEqual(self.form.pathListWidget.count(), 0)

    @mock.patch('PyQt5.QtWidgets.QListWidget.count', return_value=0)
    def test_delFolderBtn_click_disables_delFolderBtn(self, mock_folder):
        self.form.delFolderBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.delFolderBtn, QtCore.Qt.LeftButton)

        self.assertFalse(self.form.delFolderBtn.isEnabled())

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_stopBtn_click_emits_interrupt_signal(self, mock_msgbox):
        self.form.stopBtn.setEnabled(True)
        spy = QtTest.QSignalSpy(self.form.signals.interrupt)
        QtTest.QTest.mouseClick(self.form.stopBtn, QtCore.Qt.LeftButton)

        self.assertTrue(spy)

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

    @mock.patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_deleteBtn_click_calls_message_box(self, mock_msgbox):
        self.form.deleteBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.deleteBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_msgbox.called)

    @mock.patch('doppelganger.gui.MainForm._delete_selected_widgets')
    @mock.patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QtWidgets.QMessageBox.Yes)
    def test_deleteBtn_click_calls_delete_selected_widgets(self, mock_msgbox, mock_del):
        self.form.deleteBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.deleteBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_del.called)

    @mock.patch('doppelganger.gui.MainForm._delete_selected_widgets')
    @mock.patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QtWidgets.QMessageBox.Yes)
    def test_deleteBtn_click_disables_deleteBtn(self, mock_msgbox, mock_del):
        self.form.deleteBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.deleteBtn, QtCore.Qt.LeftButton)

        self.assertFalse(self.form.deleteBtn.isEnabled())

    @mock.patch('doppelganger.gui.MainForm._clear_form_before_start')
    @mock.patch('doppelganger.gui.MainForm._start_processing')
    def test_startBtn_click_calls_clear_form_before_start(self, mock_processing, mock_clear):
        self.form.startBtn.setEnabled(True)
        self.form.stopBtn.setEnabled(False)
        QtTest.QTest.mouseClick(self.form.startBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_clear.called)
        self.assertFalse(self.form.startBtn.isEnabled())
        self.assertTrue(self.form.stopBtn.isEnabled())

    @mock.patch('doppelganger.gui.MainForm._start_processing')
    @mock.patch('doppelganger.gui.MainForm._get_user_folders', return_value=[])
    def test_startBtn_click_calls_start_processing(self, mock_folders, mock_processing):
        self.form.startBtn.setEnabled(True)
        QtTest.QTest.mouseClick(self.form.startBtn, QtCore.Qt.LeftButton)

        self.assertTrue(mock_folders.called)
        self.assertTrue(mock_processing.called)
