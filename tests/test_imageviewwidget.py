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

from doppelganger import core, imageviewwidget, widgets

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


# pylint: disable=missing-class-docstring


class TestImageViewWidget(TestCase):

    def setUp(self):
        self.w = imageviewwidget.ImageViewWidget()
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

    @mock.patch('PyQt5.QtWidgets.QMessageBox.exec')
    def test_render_empty_image_groups(self, mock_msgbox):
        self.w.render(self.conf, [])

        self.assertTrue(mock_msgbox.called)

    def test_render(self):
        image_groups = [[core.Image('image.jpg')]]
        self.w.render(self.conf, image_groups)
        rendered_widgets = self.w.findChildren(widgets.ImageGroupWidget)

        self.assertEqual(len(rendered_widgets), len(image_groups))
        self.assertIsInstance(rendered_widgets[0], widgets.ImageGroupWidget)

    def test_hasSelectedWidgets_False(self):
        self.w.layout.addWidget(
            widgets.ImageGroupWidget([core.Image('image.png')], self.conf)
        )
        w = self.w.findChild(widgets.DuplicateWidget)

        self.assertFalse(w.selected)

    def test_hasSelectedWidgets_True(self):
        self.w.layout.addWidget(
            widgets.ImageGroupWidget([core.Image('image.png')], self.conf)
        )
        w = self.w.findChild(widgets.DuplicateWidget)
        w.selected = True

        self.assertTrue(w.selected)
