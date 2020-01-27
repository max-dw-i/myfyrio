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

-------------------------------------------------------------------------------

Module implementing widgets rendering duplicate images found
'''


import logging
import pathlib
import subprocess
import sys
from typing import Callable, Iterable, List, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from doppelganger import config, core, signals
from doppelganger.resources.paths import ERR_IMG, resource_path

widgets_logger = logging.getLogger('main.widgets')


class InfoLabel(QtWidgets.QLabel):
    '''Abstract Label class'''

    def __init__(self, text: str, widget_width: int,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.widget_width = widget_width

        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setText(text)

    def setText(self, text: str):
        new_text = self._wordWrap(text)
        super().setText(new_text)

    def _wordWrap(self, text: str) -> str:
        '''QLabel wraps words only at word-breaks but we need
        it to happen at any letter'''

        fontMetrics = QtGui.QFontMetrics(self.font())
        wrapped_text = ''
        line = ''

        for c in text:
            # We have 4 margins 9px each (I guess) so we take 40
            width = fontMetrics.size(QtCore.Qt.TextSingleLine, line+c).width()
            if width > self.widget_width - 40:
                wrapped_text += line + '\n'
                line = c
            else:
                line += c
        wrapped_text += line
        return wrapped_text


class SimilarityLabel(InfoLabel):
    '''Widget viewing info about images similarity'''


class ImageSizeLabel(InfoLabel):
    '''Widget viewing info about size of an image'''


class ImagePathLabel(InfoLabel):
    '''Widget viewing the path of an image'''

    def __init__(self, path: core.ImagePath, widget_width: int,
                 parent: QtWidgets.QWidget = None) -> None:
        path = QtCore.QFileInfo(path).canonicalFilePath()
        super().__init__(path, widget_width, parent)


class ImageInfoWidget(QtWidgets.QWidget):
    '''Widget showing info about the image (its similarity
    rate, size and path)
    '''

    def __init__(self, image: core.Image, conf: config.Conf,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.image = image
        self.conf = conf

        self.similarityLabel: Optional[SimilarityLabel] = None
        self.imageSizeLabel: Optional[ImageSizeLabel] = None
        self.imagePathLabel: Optional[ImagePathLabel] = None

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignBottom)
        self.setLayout(self.layout)

    def render(self) -> None:
        '''Create and render widgets "SimilarityLabel",
        "ImageSizeLabel", "ImagePathLabel"'''

        if self.conf['show_similarity']:
            self._setSimilarityLabel()
        if self.conf['show_size']:
            self._setImageSizeLabel()
        if self.conf['show_path']:
            self._setImagePathLabel()

    def _setSimilarityLabel(self) -> None:
        self.similarityLabel = SimilarityLabel(f'{self.image.difference}%',
                                               self.conf['size'], self)
        self.layout.addWidget(self.similarityLabel)

    def _setImageSizeLabel(self) -> None:
        sizeInfo = self._sizeInfo()
        self.imageSizeLabel = ImageSizeLabel(sizeInfo, self.conf['size'], self)
        self.layout.addWidget(self.imageSizeLabel)

    def _setImagePathLabel(self) -> None:
        self.imagePathLabel = ImagePathLabel(self.image.path,
                                             self.conf['size'], self)
        self.layout.addWidget(self.imagePathLabel)

    def _sizeInfo(self) -> str:
        try:
            width, height = self.image.dimensions()
        except OSError as e:
            widgets_logger.error(e)
            width, height = (0, 0)

        try:
            filesize = self.image.filesize(self.conf['size_format'])
        except OSError as e:
            widgets_logger.error(e)
            filesize = 0

        units = {0: 'B',
                 1: 'KB',
                 2: 'MB'}[self.conf['size_format']]

        return f'{width}x{height}, {filesize} {units}'


class ThumbnailWidget(QtWidgets.QLabel):
    '''Widget renderering the thumbnail of an image'''

    def __init__(self, thumbnail: QtCore.QByteArray, size: int,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.thumbnail = thumbnail
        self.size = size

        self.pixmap: Optional[QtGui.QPixmap] = None

        self.setAlignment(QtCore.Qt.AlignHCenter)

    def render(self) -> None:
        '''Create and render "Pixmap" with the thumbnail'''

        self.pixmap = self._QByteArrayToQPixmap()
        self.setPixmap(self.pixmap)

    def _QByteArrayToQPixmap(self) -> QtGui.QPixmap:
        # Pixmap can read BMP, GIF, JPG, JPEG, PNG, PBM, PGM, PPM, XBM, XPM
        if self.thumbnail is None:
            return QtGui.QPixmap(resource_path(ERR_IMG)).scaled(self.size,
                                                                self.size)

        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(self.thumbnail)

        if pixmap.isNull():
            err_msg = ('Something happened while converting '
                       'QByteArray into QPixmap')
            widgets_logger.error(err_msg)
            return QtGui.QPixmap(resource_path(ERR_IMG)).scaled(self.size,
                                                                self.size)

        return pixmap

    def mark(self) -> None:
        '''Mark the widget as selected (change colour)'''

        marked = self.pixmap.copy()
        width, height = marked.width(), marked.height()

        painter = QtGui.QPainter(marked)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        painter.setBrush(brush)
        painter.drawRect(0, 0, width, height)
        painter.end()
        self.setPixmap(marked)

    def unmark(self) -> None:
        '''Mark the thumbnail as not selected (change colour back)'''

        self.setPixmap(self.pixmap)


class DuplicateWidget(QtWidgets.QWidget):
    '''Widget viewing a duplicate image and all info
    about it (its similarity rate, size and path)
    '''

    def __init__(self, image: core.Image, conf: config.Conf,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.image = image
        self.conf = conf
        self.selected = False
        self.signals = signals.Signals()

        self.imageLabel: Optional[ThumbnailWidget] = None
        self.infoLabel: Optional[ImageInfoWidget] = None

        self.setFixedWidth(conf['size'])
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.layout)

    def render(self) -> None:
        '''Create and render "ThumbnailWidget" and "ImageInfoWidget"'''

        self.imageLabel = ThumbnailWidget(self.image.thumbnail,
                                          self.conf['size'], self)
        self.layout.addWidget(self.imageLabel)
        self.imageLabel.render()

        self.infoLabel = ImageInfoWidget(self.image, self.conf, self)
        self.layout.addWidget(self.infoLabel)
        self.infoLabel.render()

    def openImage(self) -> None:
        '''Open the image in the OS default image viewer'''

        open_image_command = {'linux': 'xdg-open',
                              'win32': 'explorer',
                              'darwin': 'open'}
        command = open_image_command.get(sys.platform, 'Unknown platform')

        try:
            subprocess.run([command, self.image.path], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            widgets_logger.error(e, exc_info=True)

            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Opening image',
                'Something went wrong while opening the image'
            )
            msgBox.exec()

    def renameImage(self) -> None:
        '''Rename the image'''

        name = pathlib.Path(self.image.path).name
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            'New name',
            'Input a new name of the image:',
            text=name,
        )
        if ok:
            try:
                self.image.rename(new_name)
            except FileExistsError as e:
                widgets_logger.error(e)

                msgBox = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning,
                    'Renaming image',
                    f'File with name "{new_name}" already exists'
                )
                msgBox.exec()
            else:
                self.infoLabel.imagePathLabel.setText(self.image.path)

    def contextMenuEvent(self, event) -> None:
        menu = QtWidgets.QMenu(self)
        openAction = menu.addAction('Open')
        menu.addSeparator()
        renameAction = menu.addAction('Rename')

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == openAction:
            self.openImage()
        if action == renameAction:
            self.renameImage()

    def click(self) -> None:
        '''Select/unselect widget and emit signal "clicked"'''

        if self.selected:
            self.selected = False
            self.imageLabel.unmark()
        else:
            self.selected = True
            self.imageLabel.mark()

        self.signals.clicked.emit()

    def mouseReleaseEvent(self, event) -> None:
        self.click()

    def delete(self) -> None:
        '''Delete the image from the disk and its "DuplicateWidget" instance

        :raise OSError: something went wrong while removing the image
        '''

        try:
            self.image.delete()
        except OSError as e:
            raise OSError(e)
        else:
            self.selected = False
            self.hide()

    def move(self, dst: core.FolderPath) -> None:
        '''Move the image to a new location and delete
        its "DuplicateWidget" instance

        :param dst: new location, eg. /new/location,
        :raise OSError: something went wrong while moving the image
        '''

        try:
            self.image.move(dst)
        except OSError as e:
            raise OSError(e)
        else:
            self.selected = False
            self.hide()


class ImageGroupWidget(QtWidgets.QWidget):
    '''Widget grouping similar images together'''

    def __init__(self, conf: config.Conf, parent: QtWidgets.QWidget = None) \
        -> None:
        super().__init__(parent)

        self.conf = conf
        self.widgets: List[DuplicateWidget] = []

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setLayout(self.layout)

    def render(self, image_group: Iterable[core.Image]) -> None:
        '''Create and render "DuplicateWidget"s

        :param image_group: group of similar images
        '''

        for image in image_group:
            dupl_w = DuplicateWidget(image, self.conf, self)
            self.widgets.append(dupl_w)
            self.layout.addWidget(dupl_w)
            dupl_w.render()

    def selectedWidgets(self) -> List[DuplicateWidget]:
        '''Return selected "DuplicateWidget"s

        :return: list with selected "DuplicateWidget"s
        '''

        return [widget for widget in self.widgets if widget.selected]

    def visibleWidgets(self) -> List[DuplicateWidget]:
        '''Return visible "DuplicateWidget"s

        :return: list with visible "DuplicateWidget"s
        '''

        return [widget for widget in self.widgets if widget.isVisible()]

    def hasSelectedWidgets(self) -> bool:
        '''Check if there are selected "DuplicateWidget"s

        :return: True if there are any selected "DuplicateWidget"s
        '''

        for dupl_w in self.widgets:
            if dupl_w.selected:
                return True
        return False

    def autoSelect(self) -> None:
        '''Automatic selection of "DuplicateWidget"s'''

        for i in range(1, len(self)):
            if not self.widgets[i].selected:
                self.widgets[i].click()

    def __len__(self) -> int:
        return len(self.widgets)


class ImageViewWidget(QtWidgets.QWidget):
    '''Widget rendering duplicate images found'''

    def __init__(self, conf: config.Conf, parent: QtWidgets.QWidget = None) \
        -> None:
        super().__init__(parent)

        self.conf = conf
        self.widgets: List[ImageGroupWidget] = []

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def render(self, image_groups: Iterable[core.Group]) -> None:
        '''Create and render "ImageGroupWidget"s

        :param image_groups: groups of similar images
        '''

        for group in image_groups:
            widget = ImageGroupWidget(self.conf, self)
            self.widgets.append(widget)
            self.layout.addWidget(widget)
            widget.render(group)

    def hasSelectedWidgets(self) -> bool:
        '''Check if there are selected "DuplicateWidget"s

        :return: True if there are any selected "DuplicateWidget"s
        '''

        for group_w in self.widgets:
            if group_w.hasSelectedWidgets():
                return True
        return False

    def clear(self) -> None:
        '''Clear the widget from duplicate images found'''

        for group_w in self.widgets:
            group_w.deleteLater()

        self.widgets = []

    def delete(self) -> None:
        '''Delete selected images'''

        try:
            self._callOnSelectedWidgets(DuplicateWidget.delete)
        except OSError as e:
            err_msg = f'Error occured while removing image "{e}"'
            widgets_logger.error(err_msg)

            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Removing image',
                err_msg
            )
            msgBox.exec()

    def move(self, dst: core.FolderPath) -> None:
        '''Move selected images into another folder

        :param dst: folder to move the images into,
        '''
        try:
            self._callOnSelectedWidgets(DuplicateWidget.move, dst)
        except OSError as e:
            err_msg = f'Error occured while moving image "{e}"'
            widgets_logger.error(err_msg)

            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Moving image',
                err_msg
            )
            msgBox.exec()

    def _callOnSelectedWidgets(self, func: Callable,
                               *args, **kwargs) -> None:
        for group_w in self.widgets:
            for selected_w in group_w.selectedWidgets():
                try:
                    func(selected_w, *args, **kwargs)
                except OSError as e:
                    raise OSError(selected_w.image.path) from e
                else:
                    if self.conf['delete_dirs']:
                        selected_w.image.del_parent_dir()

            if len(group_w.visibleWidgets()) <= 1:
                group_w.hide()

    def autoSelect(self) -> None:
        '''Automatic selection of "DuplicateWidget"s'''

        for group_w in self.widgets:
            group_w.autoSelect()

    def unselect(self) -> None:
        '''Unselect all selected "DuplicateWidget"s'''

        for group_w in self.widgets:
            for dupl_w in group_w.selectedWidgets():
                dupl_w.click()
