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


from unittest import TestCase, mock

from PyQt5 import QtCore, QtWidgets

from doppelganger import core
from doppelganger.gui import duplicatewidget, imagegroupwidget, thumbnailwidget

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


IGW_MODULE = 'doppelganger.gui.imagegroupwidget.'


# pylint: disable=missing-class-docstring


class TestImageGroupWidget(TestCase):

    IGW = IGW_MODULE + 'ImageGroupWidget.'

    def setUp(self):
        self.conf = {}
        self.mock_image = mock.Mock(spec=core.Image)
        self.image_group = [self.mock_image]
        with mock.patch(self.IGW+'_setDuplicateWidgets'):
            self.w = imagegroupwidget.ImageGroupWidget(self.image_group,
                                                       self.conf)


class TestImageGroupWidgetMethodInit(TestImageGroupWidget):

    def test_initial_value(self):
        self.assertDictEqual(self.w._conf, self.conf)
        self.assertListEqual(self.w.widgets, [])

    def test_widget_layout(self):
        self.assertEqual(self.w._layout.spacing(), 10)
        self.assertIsInstance(self.w._layout, QtWidgets.QHBoxLayout)
        self.assertEqual(self.w._layout.alignment(),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def test_setDuplicateWidgets_called_with_image_group_arg(self):
        with mock.patch(self.IGW+'_setDuplicateWidgets') as mock_dupl_call:
            imagegroupwidget.ImageGroupWidget(self.image_group, self.conf)

        mock_dupl_call.assert_called_once_with(self.image_group)


class TestImageGroupWidgetMethodSetDuplicateWidgets(TestImageGroupWidget):

    DW = IGW_MODULE+'DuplicateWidget'

    def setUp(self):
        super().setUp()

        self.conf['lazy'] = True

        self.w._layout = mock.Mock(spec=QtWidgets.QHBoxLayout)

        self.mock_duplW = mock.Mock(spec=duplicatewidget.DuplicateWidget)

    def test_DuplicateWidget_called_with_image_and_conf_args(self):
        with mock.patch(self.DW,
                        return_value=self.mock_duplW) as mock_widg_call:
            self.w._setDuplicateWidgets(self.image_group)

        mock_widg_call.assert_called_once_with(self.mock_image, self.conf)

    def test_processEvents_not_called_if_lazy_mode(self):
        PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(PATCH_EVENTS) as mock_evets_call:
                self.w._setDuplicateWidgets(self.image_group)

        mock_evets_call.assert_not_called()

    def test_processEvents_not_called_if_normal_mode_and_thumbnail_made(self):
        self.conf['lazy'] = False
        PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
        self.mock_duplW.thumbnailWidget = mock.Mock(
            spec=thumbnailwidget.ThumbnailWidget
        )
        self.mock_duplW.thumbnailWidget.empty = False
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(PATCH_EVENTS) as mock_evets_call:
                self.w._setDuplicateWidgets(self.image_group)

        mock_evets_call.assert_not_called()

    def test_processEvents_called_if_normal_mode_and_thumbnail_not_made(self):
        self.conf['lazy'] = False
        PATCH_EVENTS = 'PyQt5.QtCore.QCoreApplication.processEvents'
        self.mock_duplW.thumbnailWidget = mock.Mock(
            spec=thumbnailwidget.ThumbnailWidget
        )
        type(self.mock_duplW.thumbnailWidget).empty = mock.PropertyMock(
            side_effect=[True, False]
        )
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(PATCH_EVENTS) as mock_evets_call:
                self.w._setDuplicateWidgets(self.image_group)

        mock_evets_call.assert_called_once_with()

    def test_DuplicateWidget_added_to_attr_widgets(self):
        with mock.patch(self.DW, return_value=self.mock_duplW):
            self.w._setDuplicateWidgets(self.image_group)

        self.assertListEqual(self.w.widgets, [self.mock_duplW])

    def test_DuplicateWidget_added_to_layout(self):
        with mock.patch(self.DW, return_value=self.mock_duplW):
            self.w._setDuplicateWidgets(self.image_group)

        self.w._layout.addWidget.assert_called_once_with(self.mock_duplW)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(updateGem) as mock_upd_call:
                self.w._setDuplicateWidgets(self.image_group)

        mock_upd_call.assert_called_once_with()


class TestImageGroupWidgetMethodHasSelected(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.mock_duplW = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.w.widgets = [self.mock_duplW]

    def test_return_True_if_duplicate_widget_is_selected(self):
        self.mock_duplW.selected = True
        res = self.w.hasSelected()

        self.assertTrue(res)

    def test_return_False_if_duplicate_widget_is_not_selected(self):
        self.mock_duplW.selected = False
        res = self.w.hasSelected()

        self.assertFalse(res)


class TestImageGroupWidgetMethodAutoSelect(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.mock_duplW1 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_duplW2 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.w.widgets = [self.mock_duplW1, self.mock_duplW2]

    def test_setSelected_called_on_1st_widget(self):
        self.w.autoSelect()

        self.mock_duplW2.setSelected.assert_called_once_with(True)

    def test_setSelected_not_called_on_0th_widget(self):
        self.w.autoSelect()

        self.mock_duplW1.setSelected.assert_not_called()


class TestImageGroupWidgetMethodUnselect(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.mock_duplW1 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_duplW2 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.w.widgets = [self.mock_duplW1, self.mock_duplW2]

    def test_setSelected_called_with_False_on_all_widgets(self):
        self.w.unselect()

        self.mock_duplW1.setSelected.assert_called_once_with(False)
        self.mock_duplW2.setSelected.assert_called_once_with(False)


class TestImageGroupWidgetMethodCallOnSelected(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.mock_duplW = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.w.widgets = [self.mock_duplW]
        self.w._visible_num = 5

        self.func = mock.Mock()
        self.arg = 'arg'
        self.kwarg = 'kwarg'

    def test_passed_func_not_called_if_duplicate_widget_is_not_selected(self):
        self.mock_duplW.selected = False
        self.w._callOnSelected(self.func, self.arg, kwarg=self.kwarg)

        self.func.assert_not_called()

    def test_attr_visible_num_not_decreased_if_duplW_is_not_selected(self):
        num = self.w._visible_num
        self.mock_duplW.selected = False
        self.w._callOnSelected(self.func, self.arg, kwarg=self.kwarg)

        self.assertEqual(self.w._visible_num, num)

    def test_passed_func_called_if_duplicate_widget_is_selected(self):
        self.mock_duplW.selected = True
        self.w._callOnSelected(self.func, self.arg, kwarg=self.kwarg)

        self.func.assert_called_once_with(
            self.mock_duplW, self.arg, kwarg=self.kwarg
        )

    def test_attr_visible_num_decreased_if_duplicate_widget_is_selected(self):
        num = self.w._visible_num
        self.mock_duplW.selected = True
        self.w._callOnSelected(self.func, self.arg, kwarg=self.kwarg)

        self.assertEqual(self.w._visible_num, num-1)

    def test_raise_OSError_if_passed_func_raise_OSError(self):
        self.mock_duplW.selected = True
        self.func.side_effect = OSError
        with self.assertRaises(OSError):
            self.w._callOnSelected(self.func, self.arg, kwarg=self.kwarg)

    def test_hide_not_called_if_attr_visible_num_more_than_1(self):
        self.mock_duplW.selected = False
        self.w._visible_num = 2
        with mock.patch(self.IGW+'hide') as mock_hide_call:
            self.w._callOnSelected(self.func, self.arg, kwarg=self.kwarg)

        mock_hide_call.assert_not_called()

    def test_hide_called_if_attr_visible_num_less_than_2(self):
        self.mock_duplW.selected = False
        self.w._visible_num = 1
        with mock.patch(self.IGW+'hide') as mock_hide_call:
            self.w._callOnSelected(self.func, self.arg, kwarg=self.kwarg)

        mock_hide_call.assert_called_once_with()


class TestImageGroupWidgetMethodDelete(TestImageGroupWidget):

    def test_callOnSelected_called_with_DuplicateWidget_delete_func_arg(self):
        with mock.patch(self.IGW+'_callOnSelected') as mock_call:
            self.w.delete()

        mock_call.assert_called_once_with(
            duplicatewidget.DuplicateWidget.delete
        )


class TestImageGroupWidgetMethodMove(TestImageGroupWidget):

    def test_callOnSelected_called_with_DuplicateWidget_move_func__dst(self):
        with mock.patch(self.IGW+'_callOnSelected') as mock_call:
            self.w.move('new_folder')

        mock_call.assert_called_once_with(
            duplicatewidget.DuplicateWidget.move, 'new_folder'
        )
