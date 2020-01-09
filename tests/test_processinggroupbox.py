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

from doppelganger import processinggroupbox

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=missing-class-docstring,protected-access


class TestProcessingGroupBox(TestCase):

    def setUp(self):
        self.w = processinggroupbox.ProcessingGroupBox()
        self.new_val = '13'
        self.w.processProg.setValue(int(self.new_val))
        labels = self.w.findChildren(QtWidgets.QLabel)
        for label in labels:
            label.setText(label.text()[:-1] + self.new_val)

    def test_startBtn_initially_disabled(self):
        self.assertFalse(self.w.startBtn.isEnabled())

    def test_stopBtn_initially_disabled(self):
        self.assertFalse(self.w.stopBtn.isEnabled())

    def test_right_labels_found(self):
        self.assertIn(self.w.loadedPicLbl, self.w.labels)
        self.assertIn(self.w.foundInCacheLbl, self.w.labels)
        self.assertIn(self.w.remainingPicLbl, self.w.labels)
        self.assertIn(self.w.dupGroupLbl, self.w.labels)
        self.assertIn(self.w.duplicatesLbl, self.w.labels)
        self.assertIn(self.w.thumbnailsLbl, self.w.labels)
        self.assertEqual(len(self.w.labels), 6)

    def test_clearWidget_clear_progress_bar(self):
        self.w._clearWidget()

        self.assertEqual(self.w.processProg.value(), 0)

    def test_clearWidget_clear_labels(self):
        self.w._clearWidget()

        for label in self.w.findChildren(QtWidgets.QLabel):
            self.assertEqual(label.text()[-1], '0')

    def test_update_label_with_alias_thumbnails(self):
        alias = 'thumbnails'
        new_text = '666'
        self.w.updateLabel(alias, new_text)
        for label in self.w.findChildren(QtWidgets.QLabel):
            if label.property('alias') == alias:
                self.assertEqual(label.text()[-3:], new_text)
            else:
                self.assertEqual(label.text()[-2:], self.new_val)

    def test_update_label_with_alias_image_groups(self):
        alias = 'image_groups'
        new_text = '666'
        self.w.updateLabel(alias, new_text)
        for label in self.w.findChildren(QtWidgets.QLabel):
            if label.property('alias') == alias:
                self.assertEqual(label.text()[-3:], new_text)
            else:
                self.assertEqual(label.text()[-2:], self.new_val)

    def test_update_label_with_alias_remaining_images(self):
        alias = 'remaining_images'
        new_text = '666'
        self.w.updateLabel(alias, new_text)
        for label in self.w.findChildren(QtWidgets.QLabel):
            if label.property('alias') == alias:
                self.assertEqual(label.text()[-3:], new_text)
            else:
                self.assertEqual(label.text()[-2:], self.new_val)

    def test_update_label_with_alias_found_in_cache(self):
        alias = 'found_in_cache'
        new_text = '666'
        self.w.updateLabel(alias, new_text)
        for label in self.w.findChildren(QtWidgets.QLabel):
            if label.property('alias') == alias:
                self.assertEqual(label.text()[-3:], new_text)
            else:
                self.assertEqual(label.text()[-2:], self.new_val)

    def test_update_label_with_alias_loaded_images(self):
        alias = 'loaded_images'
        new_text = '666'
        self.w.updateLabel(alias, new_text)
        for label in self.w.findChildren(QtWidgets.QLabel):
            if label.property('alias') == alias:
                self.assertEqual(label.text()[-3:], new_text)
            else:
                self.assertEqual(label.text()[-2:], self.new_val)

    def test_update_label_with_alias_duplicates(self):
        alias = 'duplicates'
        new_text = '666'
        self.w.updateLabel(alias, new_text)
        for label in self.w.findChildren(QtWidgets.QLabel):
            if label.property('alias') == alias:
                self.assertEqual(label.text()[-3:], new_text)
            else:
                self.assertEqual(label.text()[-2:], self.new_val)

    def test_update_label_with_unexisting_alias(self):
        alias = 'not_existing'
        new_text = '666'
        self.w.updateLabel(alias, new_text)
        for label in self.w.findChildren(QtWidgets.QLabel):
            self.assertEqual(label.text()[-2:], self.new_val)

    def test_startProcessing_call_clearWidget(self):
        NM = 'doppelganger.processinggroupbox.ProcessingGroupBox._clearWidget'
        with mock.patch(NM) as mock_start:
            self.w.startProcessing()

        mock_start.assert_called_once_with()

    def test_startProcessing_disable_startBtn(self):
        self.w.startBtn.setEnabled(True)
        self.w.startProcessing()

        self.assertFalse(self.w.startBtn.isEnabled())

    def test_startProcessing_enable_stopBtn(self):
        self.w.stopBtn.setEnabled(False)
        self.w.startProcessing()

        self.assertTrue(self.w.stopBtn.isEnabled())

    def test_stopProcessing_enable_startBtn(self):
        self.w.startBtn.setEnabled(False)
        self.w.stopProcessing()

        self.assertTrue(self.w.startBtn.isEnabled())

    def test_stopProcessing_disable_stopBtn(self):
        self.w.stopBtn.setEnabled(True)
        self.w.stopProcessing()

        self.assertFalse(self.w.stopBtn.isEnabled())

    def test_stopProcessing_set_progress_bar_0(self):
        self.w.processProg.setValue(13)
        self.w.stopProcessing()

        self.assertEqual(self.w.processProg.value(), 100)
