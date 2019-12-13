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

-------------------------------------------------------------------------------

Module with custom widgets
'''

import logging
import pathlib
import subprocess
import sys
from typing import Iterable, List, Tuple

from PyQt5 import QtCore, QtGui, QtWidgets

from doppelganger import config, core, signals

IMAGE_ERROR = str(pathlib.Path('doppelganger') / 'resources' / 'image_error.png')
SIZE = 200

widgets_logger = logging.getLogger('main.widgets')


class InfoLabelWidget(QtWidgets.QLabel):
    '''Abstract Label class'''

    def __init__(self, text: str, widget_size: int, parent=None) -> None:
        super().__init__(parent)
        self.widget_size = widget_size

        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setText(self._word_wrap(text))

    def _word_wrap(self, text: str) -> str:
        '''QLabel wraps words only at word-breaks but we need
        it to happen at any letter

        :param text: text,
        :return: wrapped text
        '''

        fontMetrics = QtGui.QFontMetrics(self.font())
        wrapped_text = ''
        line = ''

        for c in text:
            # We have 4 margins 9px each (I guess) so we take 40
            width = fontMetrics.size(QtCore.Qt.TextSingleLine, line + c).width()
            if width > self.widget_size - 40:
                wrapped_text += line + '\n'
                line = c
            else:
                line += c
        wrapped_text += line

        return wrapped_text


class SimilarityLabel(InfoLabelWidget):
    '''Widget to show info about images similarity'''


class ImageSizeLabel(InfoLabelWidget):
    '''Widget to show info about the image size'''


class ImagePathLabel(InfoLabelWidget):
    '''Widget to show the path to an image'''

    def __init__(self, text: core.ImagePath, widget_size: int, parent=None) -> None:
        super().__init__(QtCore.QFileInfo(text).canonicalFilePath(),
                         widget_size, parent)

class ImageInfoWidget(QtWidgets.QWidget):
    '''Widget to show info about an image (its similarity
    rate, size and path)'''

    def __init__(self, path: core.ImagePath, difference: core.Distance,
                 dimensions: Tuple[core.Width, core.Height], filesize: core.FileSize,
                 conf: config.ConfigData, parent=None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignBottom)

        if conf['show_similarity']:
            widget = SimilarityLabel(str(difference), conf['size'], self)
            layout.addWidget(widget)
        if conf['show_size']:
            widget = ImageSizeLabel(
                self._get_image_size(dimensions, filesize),
                conf['size'],
                self
            )
            layout.addWidget(widget)
        if conf['show_path']:
            widget = ImagePathLabel(path, conf['size'], self)
            layout.addWidget(widget)

        self.setLayout(layout)

    @staticmethod
    def _get_image_size(dimensions: Tuple[core.Width, core.Height],
                        filesize: core.FileSize) -> str:
        '''Return info about image dimensions and file size

        :param dimensions: image dimensions,
        :param filesize: file size in bytes, kilobytes or megabytes,
                         rounded to the first decimal place,
        :return: string with format '{width}x{height}, {file_size} {units}'
        '''

        width, height = dimensions[0], dimensions[1]
        units = 'KB'

        return f'{width}x{height}, {filesize} {units}'


class ThumbnailWidget(QtWidgets.QLabel):
    '''Widget to render the thumbnail of an image'''

    def __init__(self, thumbnail: QtCore.QByteArray, size: int, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.pixmap = self._QByteArray_to_QPixmap(thumbnail, size)
        self.setPixmap(self.pixmap)

    @staticmethod
    def _QByteArray_to_QPixmap(thumbnail: QtCore.QByteArray,
                               size: int) -> QtGui.QPixmap:
        '''Convert 'QByteArray' to 'QPixmap'

        :param thumbnails: image in format 'QByteArray',
        :param size: thumbnail size,
        :return: image in format 'QPixmap' or, if something's
                 wrong - error image
        '''

        # Pixmap can read BMP, GIF, JPG, JPEG, PNG, PBM, PGM, PPM, XBM, XPM
        if thumbnail is None:
            return QtGui.QPixmap(IMAGE_ERROR).scaled(size, size)

        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(thumbnail)

        if pixmap.isNull():
            widgets_logger.error('Something happened while converting QByteArray into QPixmap')
            return QtGui.QPixmap(IMAGE_ERROR).scaled(size, size)

        return pixmap

    def mark(self) -> None:
        '''Mark the thumbnail as selected'''

        marked = self.pixmap.copy()
        width, height = marked.width(), marked.height()

        painter = QtGui.QPainter(marked)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        painter.setBrush(brush)
        painter.drawRect(0, 0, width, height)
        painter.end()
        self.setPixmap(marked)

    def unmark(self) -> None:
        '''Mark the thumbnail as not selected'''

        self.setPixmap(self.pixmap)


class DuplicateWidget(QtWidgets.QWidget, QtCore.QObject):
    '''Widget to render a duplicate image and all the info
    about it (its similarity rate, size and path)
    '''

    def __init__(self, image: core.HashedImage, conf: config.ConfigData,
                 parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self.conf = conf
        self.selected = False
        self.imageLabel, self.imageInfo = self._widgets()

        self.signals = signals.Signals()

        self.setFixedWidth(conf['size'])
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        for widget in (self.imageLabel, self.imageInfo):
            layout.addWidget(widget)
        self.setLayout(layout)

    def _widgets(self) -> Tuple[ThumbnailWidget, ImageInfoWidget]:
        '''Return ThumbnailWidget and ImageInfoWidget objects

        :return: tuple, ('ThumbnailWidget' obj, 'ImageInfoWidget' obj)
        '''

        imageLabel = ThumbnailWidget(self.image.thumbnail, self.conf['size'], self)

        try:
            dimensions = self.image.dimensions()
        except OSError as e:
            widgets_logger.error(e)
            dimensions = (0, 0)

        try:
            filesize = self.image.filesize()
        except OSError as e:
            widgets_logger.error(e)
            filesize = 0

        imageInfo = ImageInfoWidget(self.image.path, self.image.difference,
                                    dimensions, filesize, self.conf, self)

        return imageLabel, imageInfo

    def _open_image(self) -> None:
        '''Open the image in the OS default image viewer'''

        open_image_command = {'linux': 'xdg-open',
                              'win32': 'explorer',
                              'darwin': 'open'}[sys.platform]

        try:
            subprocess.run([open_image_command, self.image.path], check=True)
        except subprocess.CalledProcessError:
            msg = 'Something wrong happened while opening the image viewer'
            widgets_logger.error(msg, exc_info=True)

    def contextMenuEvent(self, event) -> None:
        menu = QtWidgets.QMenu(self)
        openAction = menu.addAction("Open")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == openAction:
            self._open_image()

    def mouseReleaseEvent(self, event) -> None:
        '''Function called on mouse release event'''

        super().mouseReleaseEvent(event)

        if self.selected:
            self.selected = False
            self.imageLabel.unmark()
        else:
            self.selected = True
            self.imageLabel.mark()

        self.signals.clicked.emit()

    def delete(self) -> None:
        '''Delete the image from disk and its DuplicateWidget instance

        :raise OSError: something went wrong while removing the image
        '''

        try:
            self.image.delete()
        except OSError as e:
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Removing image',
                f'Error occured while removing image {self.image.path}'
            )
            msgBox.exec()

            raise OSError(e)
        else:
            self.selected = False
            self.deleteLater()

    def move(self, dst: core.FolderPath) -> None:
        '''Move the image to a new location and delete
        its DuplicateWidget instance

        :param dst: new location, eg. /new/location,
        :raise OSError: something went wrong while moving the image
        '''

        try:
            self.image.move(dst)
        except OSError as e:
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Moving image',
                f'Error occured while moving image {self.image.path}'
            )
            msgBox.exec()

            raise OSError(e)
        else:
            self.selected = False
            self.deleteLater()


class ImageGroupWidget(QtWidgets.QWidget):
    '''Widget to group similar images together'''

    def __init__(self, image_group: Iterable[core.HashedImage],
                 conf: config.ConfigData, parent=None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        for image in image_group:
            thumbnail = DuplicateWidget(image, conf, self)
            layout.addWidget(thumbnail)
        self.setLayout(layout)

    def getSelectedWidgets(self) -> List[DuplicateWidget]:
        '''Return a list of the selected DuplicateWidget instances

        :return: selected DuplicateWidget instances
        '''

        widgets = self.findChildren(
            DuplicateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        return [widget for widget in widgets if widget.selected]

    def __len__(self) -> int:
        return len(self.findChildren(DuplicateWidget,
                                     options=QtCore.Qt.FindDirectChildrenOnly))
