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

-------------------------------------------------------------------------------

Module implementing widgets viewing such information about images as size,
width, height, path, etc.
'''


from typing import Union

from PyQt5 import QtCore, QtGui, QtWidgets


class InfoLabel(QtWidgets.QLabel):
    '''General image info class

    :param text:            text to set,
    :param widget_width:    widget width (used in word wrapping),
    :param parent:          widget's parent (optional)
    '''

    def __init__(self, text: str, widget_width: int,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.widget_width = widget_width

        self.setAlignment(QtCore.Qt.AlignHCenter)

        self.setText(text)

    def setText(self, text: str) -> None:
        new_text = self._wordWrap(text)

        super().setText(new_text)

        self.updateGeometry()

    def _wordWrap(self, text: str) -> str:
        '''QLabel wraps words only at word-breaks but we need
        it to happen at any letter'''

        fontMetrics = QtGui.QFontMetrics(self.font())
        wrapped_text = ''
        line = ''

        for c in text:
            width = fontMetrics.size(QtCore.Qt.TextSingleLine, line+c).width()
            if width > self.widget_width - 10:
                wrapped_text += line + '\n'
                line = c
            else:
                line += c
        wrapped_text += line
        return wrapped_text


class SimilarityLabel(InfoLabel):
    '''Widget viewing the image similarity rate

    :param text:            text to set,
    :param widget_width:    widget width (used in word wrapping),
    :param parent:          widget's parent (optional)
    '''


class ImageSizeLabel(InfoLabel):
    '''Widget viewing the image size

    :param width:           image width,
    :param height:          image height,
    :param file_size:       image file size (on the disk),
    :param size_format:     image file size units (e.g. B, KB, MB),
    :param widget_width:    widget width (used in word wrapping),
    :param parent:          widget's parent (optional)
    '''

    def __init__(self, width: int, height: int, file_size: Union[int, float],
                 size_format: str, widget_width: int,
                 parent: QtWidgets.QWidget = None) -> None:
        text = f'{width}x{height}, {file_size} {size_format}'

        super().__init__(text, widget_width, parent)


class ImagePathLabel(InfoLabel):
    '''Widget viewing the image path

    :param path:            image path,
    :param widget_width:    widget width (used in word wrapping),
    :param parent:          widget's parent (optional)
    '''

    def __init__(self, path: str, widget_width: int,
                 parent: QtWidgets.QWidget = None) -> None:
        path = QtCore.QFileInfo(path).canonicalFilePath()

        super().__init__(path, widget_width, parent)
