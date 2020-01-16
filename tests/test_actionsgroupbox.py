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

from unittest import TestCase

from PyQt5 import QtWidgets

from doppelganger.gui import actionsgroupbox

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=missing-class-docstring


class TestProcessingGroupBox(TestCase):

    def setUp(self):
        self.w = actionsgroupbox.ActionsGroupBox()

    def test_moveBtn_initially_disabled(self):
        self.assertFalse(self.w.moveBtn.isEnabled())

    def test_deleteBtn_initially_disabled(self):
        self.assertFalse(self.w.deleteBtn.isEnabled())

    def test_unselectBtn_initially_disabled(self):
        self.assertFalse(self.w.unselectBtn.isEnabled())

    def test_autoSelectBtn_initially_disabled(self):
        self.assertFalse(self.w.autoSelectBtn.isEnabled())

    def test_setEnabled_enable_moveBtn(self):
        self.w.moveBtn.setEnabled(False)
        self.w.setEnabled(True)

        self.assertTrue(self.w.moveBtn.isEnabled())

    def test_setEnabled_enable_deleteBtn(self):
        self.w.deleteBtn.setEnabled(False)
        self.w.setEnabled(True)

        self.assertTrue(self.w.deleteBtn.isEnabled())

    def test_setEnabled_enable_unselectBtn(self):
        self.w.unselectBtn.setEnabled(False)
        self.w.setEnabled(True)

        self.assertTrue(self.w.unselectBtn.isEnabled())

    def test_setEnabled_disable_moveBtn(self):
        self.w.moveBtn.setEnabled(True)
        self.w.setEnabled(False)

        self.assertFalse(self.w.moveBtn.isEnabled())

    def test_setEnabled_disable_deleteBtn(self):
        self.w.deleteBtn.setEnabled(True)
        self.w.setEnabled(False)

        self.assertFalse(self.w.deleteBtn.isEnabled())

    def test_setEnabled_disable_unselectBtn(self):
        self.w.unselectBtn.setEnabled(True)
        self.w.setEnabled(False)

        self.assertFalse(self.w.unselectBtn.isEnabled())
