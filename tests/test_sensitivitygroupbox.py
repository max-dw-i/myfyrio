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

from doppelganger.gui import sensitivitygroupbox

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=missing-class-docstring


class TestSensitivityGroupBox(TestCase):

    def setUp(self):
        self.w = sensitivitygroupbox.SensitivityGroupBox()
        self.w.sensitivity = 666

    def test_veryHighRbtn_initially_checked(self):
        self.assertTrue(self.w.veryHighRbtn.isChecked())

    def test_highRbtn_initially_not_checked(self):
        self.assertFalse(self.w.highRbtn.isChecked())

    def test_mediumRbtn_initially_not_checked(self):
        self.assertFalse(self.w.mediumRbtn.isChecked())

    def test_lowRbtn_initially_not_checked(self):
        self.assertFalse(self.w.lowRbtn.isChecked())

    def test_veryLowRbtn_initially_not_checked(self):
        self.assertFalse(self.w.veryLowRbtn.isChecked())

    def test_setVeryHighSensitivity(self):
        self.w.setVeryHighSensitivity()

        self.assertEqual(self.w.sensitivity, 0)

    def test_setHighSensitivity(self):
        self.w.setHighSensitivity()

        self.assertEqual(self.w.sensitivity, 5)

    def test_setMediumSensitivity(self):
        self.w.setMediumSensitivity()

        self.assertEqual(self.w.sensitivity, 10)

    def test_setLowSensitivity(self):
        self.w.setLowSensitivity()

        self.assertEqual(self.w.sensitivity, 15)

    def test_setVeryLowSensitivity(self):
        self.w.setVeryLowSensitivity()

        self.assertEqual(self.w.sensitivity, 20)
