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

from PyQt5 import QtTest, QtWidgets

from doppelganger.gui import sensitivityradiobutton

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=missing-class-docstring


SensRBtn = 'doppelganger.gui.sensitivityradiobutton.SensitivityRadioButton.'


class TestClassSensitivityRBtn(TestCase):

    def setUp(self):
        self.w = sensitivityradiobutton.SensitivityRadioButton()


class TestClassSensitivityRBtnMethodInit(TestClassSensitivityRBtn):

    def test_attr_sensitivity_is_0(self):
        self.assertEqual(self.w.sensitivity, 0)

    def test_setSignals_called(self):
        with mock.patch(SensRBtn+'_setSignals') as mock_signals_call:
            sensitivityradiobutton.SensitivityRadioButton()

        mock_signals_call.assert_called_once_with()


class TestClassSensitivityRBtnMethodSetSignals(TestClassSensitivityRBtn):

    def test_clicked_signal_connected_to_emitSensitivity(self):
        self.w.clicked = mock.Mock()
        self.w._setSignals()

        self.w.clicked.connect.assert_called_once_with(self.w._emitSensitivity)


class TestClassSensitivityRBtnMethodEmitSensitivity(TestClassSensitivityRBtn):

    def test_sensitivityChanged_signal_emitted_with_sensitivity_arg(self):
        spy = QtTest.QSignalSpy(self.w.sensitivityChanged)
        self.w._emitSensitivity()

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], self.w.sensitivity)


class TestClassVeryHighRBtn(TestCase):

    def setUp(self):
        self.w = sensitivityradiobutton.VeryHighRadioButton()


class TestClassVeryHighRBtnMethodInit(TestClassVeryHighRBtn):

    def test_attr_sensitivity_is_0(self):
        self.assertEqual(self.w.sensitivity, 0)

    def test_VeryHighRadioButton_is_subclass_of_SensitivityRadioButton(self):
        self.assertIsInstance(
            self.w, sensitivityradiobutton.SensitivityRadioButton
        )


class TestClassHighRBtn(TestCase):

    def setUp(self):
        self.w = sensitivityradiobutton.HighRadioButton()


class TestClassHighRBtnMethodInit(TestClassHighRBtn):

    def test_attr_sensitivity_is_5(self):
        self.assertEqual(self.w.sensitivity, 5)

    def test_HighRadioButton_is_subclass_of_SensitivityRadioButton(self):
        self.assertIsInstance(
            self.w, sensitivityradiobutton.SensitivityRadioButton
        )


class TestClassMediumRBtn(TestCase):

    def setUp(self):
        self.w = sensitivityradiobutton.MediumRadioButton()


class TestClassMediumRBtnMethodInit(TestClassMediumRBtn):

    def test_attr_sensitivity_is_10(self):
        self.assertEqual(self.w.sensitivity, 10)

    def test_MediumRadioButton_is_subclass_of_SensitivityRadioButton(self):
        self.assertIsInstance(
            self.w, sensitivityradiobutton.SensitivityRadioButton
        )


class TestClassLowRBtn(TestCase):

    def setUp(self):
        self.w = sensitivityradiobutton.LowRadioButton()


class TestClassLowRBtnMethodInit(TestClassLowRBtn):

    def test_attr_sensitivity_is_15(self):
        self.assertEqual(self.w.sensitivity, 15)

    def test_LowRadioButton_is_subclass_of_SensitivityRadioButton(self):
        self.assertIsInstance(
            self.w, sensitivityradiobutton.SensitivityRadioButton
        )


class TestClassVeryLowRBtn(TestCase):

    def setUp(self):
        self.w = sensitivityradiobutton.VeryLowRadioButton()


class TestClassVeryLowRBtnMethodInit(TestClassVeryLowRBtn):

    def test_attr_sensitivity_is_20(self):
        self.assertEqual(self.w.sensitivity, 20)

    def test_VeryLowRadioButton_is_subclass_of_SensitivityRadioButton(self):
        self.assertIsInstance(
            self.w, sensitivityradiobutton.SensitivityRadioButton
        )
