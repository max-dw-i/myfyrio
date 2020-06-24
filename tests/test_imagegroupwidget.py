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

from PyQt5 import QtCore, QtWidgets

from myfyrio import core
from myfyrio.gui import duplicatewidget, imagegroupwidget

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

IGW_MODULE = 'myfyrio.gui.imagegroupwidget.'

# pylint: disable=missing-class-docstring


class TestImageGroupWidget(TestCase):

    IGW = IGW_MODULE + 'ImageGroupWidget.'

    def setUp(self):
        self.conf = {}
        self.mock_image = mock.Mock(spec=core.Image)
        self.image_group = [self.mock_image]
        with mock.patch(self.IGW+'addDuplicateWidget'):
            self.w = imagegroupwidget.ImageGroupWidget(self.image_group,
                                                       self.conf)


class TestImageGroupWidgetMethodInit(TestImageGroupWidget):

    def test_initial_value(self):
        self.assertDictEqual(self.w._conf, self.conf)
        self.assertListEqual(self.w.widgets, [])
        self.assertEqual(self.w._visible_num, 0)

    def test_widget_layout(self):
        self.assertEqual(self.w._layout.spacing(), 10)
        self.assertIsInstance(self.w._layout, QtWidgets.QHBoxLayout)
        self.assertEqual(self.w._layout.alignment(),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def test_addDuplicateWidget_called_with_image_group_arg(self):
        with mock.patch(self.IGW+'addDuplicateWidget') as mock_dupl_call:
            imagegroupwidget.ImageGroupWidget(self.image_group, self.conf)

        mock_dupl_call.assert_called_once_with(self.mock_image)


class TestImageGroupWidgetMethodAddDuplicateWidget(TestImageGroupWidget):

    DW = 'myfyrio.gui.duplicatewidget.DuplicateWidget'

    def setUp(self):
        super().setUp()

        self.conf['lazy'] = True

        self.w._layout = mock.Mock(spec=QtWidgets.QHBoxLayout)

        self.mock_duplW = mock.Mock(spec=duplicatewidget.DuplicateWidget)

    def test_DuplicateWidget_called_with_image_and_conf_args(self):
        with mock.patch(self.DW,
                        return_value=self.mock_duplW) as mock_duplW_call:
            with mock.patch(self.IGW+'_insertIndex', return_value=0):
                self.w.addDuplicateWidget(self.mock_image)

        mock_duplW_call.assert_called_once_with(self.mock_image, self.conf)

    def test_duplW_error_signal_connected_if_duplW_is_not_selected(self):
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(self.IGW+'_insertIndex', return_value=0):
                self.w.addDuplicateWidget(self.mock_image)

        self.mock_duplW.error.connect.assert_called_once()

    def test_duplW_hidden_signal_connected_if_duplW_is_not_selected(self):
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(self.IGW+'_insertIndex', return_value=0):
                self.w.addDuplicateWidget(self.mock_image)

        self.mock_duplW.hidden.connect.assert_called_once_with(
            self.w._duplicateWidgetHidden
        )

    def test_DuplicateWidget_added_to_attr_widgets(self):
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(self.IGW+'_insertIndex', return_value=0):
                self.w.addDuplicateWidget(self.mock_image)

        self.assertListEqual(self.w.widgets, [self.mock_duplW])

    def test_insertIndex_called_with_new_DuplicateWidget(self):
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(self.IGW+'_insertIndex',
                            return_value=0) as mock_insert_call:
                self.w.addDuplicateWidget(self.mock_image)

        mock_insert_call.assert_called_once_with(self.mock_duplW)

    def test_DuplicateWidget_inserted_to_layout(self):
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(self.IGW+'_insertIndex', return_value=0):
                self.w.addDuplicateWidget(self.mock_image)

        self.w._layout.insertWidget.assert_called_once_with(0, self.mock_duplW)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(self.IGW+'_insertIndex', return_value=0):
                with mock.patch(updateGem) as mock_upd_call:
                    self.w.addDuplicateWidget(self.mock_image)

        mock_upd_call.assert_called_once_with()

    def test_added_DuplicateWidget_returned(self):
        with mock.patch(self.DW, return_value=self.mock_duplW):
            with mock.patch(self.IGW+'_insertIndex', return_value=0):
                res = self.w.addDuplicateWidget(self.mock_image)

        self.assertEqual(res, self.mock_duplW)


class TestImageGroupWidgetMethodInsertIndex(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.conf['sort'] = 0
        self.mock_Sort = mock.Mock(spec=core.Sort)
        self.mock_Sort.key.return_value = lambda x: x

        self.mock_new_duplW = mock.Mock()
        self.mock_new_duplW._image = 888

        self.mock_duplW1 = mock.Mock()
        self.mock_duplW1._image = 1
        self.mock_duplW2 = mock.Mock()
        self.mock_duplW2._image = 2

        self.w.widgets = [self.mock_duplW1, self.mock_duplW2]

    def test_Sort_key_called_with_proper_sort_type_from_conf(self):
        with mock.patch('myfyrio.core.Sort',
                        return_value=self.mock_Sort) as mock_Sort_call:
            self.w._insertIndex(self.mock_new_duplW)

        mock_Sort_call.assert_called_once_with(0)
        self.mock_Sort.key.assert_called_once_with()

    def test_new_widget_inserted_in_beginning(self):
        self.mock_new_duplW._image = 0
        with mock.patch('myfyrio.core.Sort', return_value=self.mock_Sort):
            res = self.w._insertIndex(self.mock_new_duplW)

        self.assertEqual(res, 0)

    def test_new_widget_inserted_in_middle(self):
        self.mock_new_duplW._image = 1.5
        with mock.patch('myfyrio.core.Sort', return_value=self.mock_Sort):
            res = self.w._insertIndex(self.mock_new_duplW)

        self.assertEqual(res, 1)

    def test_new_widget_inserted_in_end(self):
        self.mock_new_duplW._image = 3
        with mock.patch('myfyrio.core.Sort', return_value=self.mock_Sort):
            res = self.w._insertIndex(self.mock_new_duplW)

        self.assertEqual(res, 2)


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

        self.mock_duplW0 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_selected_prop0 = mock.PropertyMock(spec=bool)
        type(self.mock_duplW0).selected = self.mock_selected_prop0
        self.mock_duplW1 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_selected_prop1 = mock.PropertyMock(spec=bool)
        type(self.mock_duplW1).selected = self.mock_selected_prop1
        self.w.widgets = [self.mock_duplW0, self.mock_duplW1]

    def test_setSelected_called_on_1st_widget(self):
        self.w.autoSelect()

        self.mock_selected_prop1.assert_called_once_with(True)

    def test_setSelected_not_called_on_0th_widget(self):
        self.w.autoSelect()

        self.mock_selected_prop0.assert_not_called()


class TestImageGroupWidgetMethodUnselect(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.mock_duplW0 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_selected_prop0 = mock.PropertyMock(spec=bool)
        type(self.mock_duplW0).selected = self.mock_selected_prop0
        self.mock_duplW1 = mock.Mock(spec=duplicatewidget.DuplicateWidget)
        self.mock_selected_prop1 = mock.PropertyMock(spec=bool)
        type(self.mock_duplW1).selected = self.mock_selected_prop1
        self.w.widgets = [self.mock_duplW0, self.mock_duplW1]

    def test_setSelected_called_with_False_on_all_widgets(self):
        self.w.unselect()

        self.mock_selected_prop0.assert_called_once_with(False)
        self.mock_selected_prop1.assert_called_once_with(False)


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

    def test_passed_func_called_if_duplicate_widget_is_selected(self):
        self.mock_duplW.selected = True
        self.w._callOnSelected(self.func, self.arg, kwarg=self.kwarg)

        self.func.assert_called_once_with(
            self.mock_duplW, self.arg, kwarg=self.kwarg
        )

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
