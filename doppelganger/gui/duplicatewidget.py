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

Module implementing widget representing a duplicate image
'''


import pathlib
import subprocess
import sys
from typing import Callable

from PyQt5 import QtCore, QtWidgets

from doppelganger import config, core
from doppelganger.gui.errornotifier import errorMessage
from doppelganger.gui.infolabel import (ImagePathLabel, ImageSizeLabel,
                                        SimilarityLabel)
from doppelganger.gui.thumbnailwidget import ThumbnailWidget
from doppelganger.logger import Logger

logger = Logger.getLogger('duplicatewidget')


class DuplicateWidget(QtWidgets.QWidget):
    '''Widget viewing a duplicate image and all info about it (its similarity
    rate, size and path)

    :param image:       "Image" object,
    :param conf:        programme's preferences as a "Config" object,
    :param parent:      widget's parent (optional),

    :signal hidden:     widget has been hidden,
    :signal clicked:    widget has been clicked,
    :signal error:      error message: str
    '''

    hidden = QtCore.pyqtSignal()
    clicked = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, image: core.Image, conf: config.Config,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self._image = image
        self._conf = conf

        self._selected = False

        self.setFixedWidth(self._conf['size'])

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setAlignment(QtCore.Qt.AlignTop)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.thumbnailWidget = self._setThumbnailWidget()
        if self._conf['show_similarity']:
            self.similarityLabel = self._setSimilarityLabel()
        if self._conf['show_size']:
            self.imageSizeLabel = self._setImageSizeLabel()
        if self._conf['show_path']:
            self.imagePathLabel = self._setImagePathLabel()

        self.setLayout(self._layout)

    def _setThumbnailWidget(self) -> ThumbnailWidget:
        thumbnailWidget = ThumbnailWidget(self._image, self._conf['size'],
                                          self._conf['lazy'])
        self._layout.addWidget(thumbnailWidget)
        self._layout.setAlignment(thumbnailWidget, QtCore.Qt.AlignHCenter)
        self.updateGeometry()

        return thumbnailWidget

    def _setSimilarityLabel(self) -> SimilarityLabel:
        similarity = self._image.similarity()
        similarityLabel = SimilarityLabel(f'{similarity}%', self._conf['size'])
        self._layout.addWidget(similarityLabel)
        self.updateGeometry()

        return similarityLabel

    def _setImageSizeLabel(self) -> ImageSizeLabel:
        try:
            width, height = self._image.width, self._image.height

        except OSError as e:
            logger.exception(e)
            width, height = (0, 0)

        size_format = core.SizeFormat(self._conf['size_format'])

        try:
            filesize = self._image.filesize(size_format)

        except OSError as e:
            logger.exception(e)
            filesize = 0

        imageSizeLabel = ImageSizeLabel(width, height, filesize,
                                        size_format.name, self._conf['size'])
        self._layout.addWidget(imageSizeLabel)
        self.updateGeometry()

        return imageSizeLabel

    def _setImagePathLabel(self) -> ImagePathLabel:
        imagePathLabel = ImagePathLabel(self._image.path, self._conf['size'])
        self._layout.addWidget(imagePathLabel)
        self.updateGeometry()

        return imagePathLabel

    def openImage(self) -> None:
        '''Open the image in the OS default image viewer'''

        if sys.platform.startswith('linux'):
            command = 'xdg-open'
        elif sys.platform.startswith('win32'):
            command = 'explorer'
        elif sys.platform.startswith('darwin'):
            command = 'open'
        else:
            command = 'Unknown platform'

        try:
            subprocess.run([command, self._image.path], check=True)

        except (FileNotFoundError, subprocess.CalledProcessError):
            err_msg = 'Something went wrong while opening the image'
            logger.exception(err_msg)
            errorMessage([err_msg])

    def renameImage(self) -> None:
        '''Rename the image'''

        name = pathlib.Path(self._image.path).name
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            'New name',
            'Input a new name of the image:',
            text=name,
        )
        if ok:
            try:
                self._image.rename(new_name)

            except FileExistsError:
                err_msg = f'File with the name "{new_name}" already exists'
                logger.exception(err_msg)
                errorMessage([err_msg])

            except FileNotFoundError:
                err_msg = f'File with the name "{name}" does not exist'
                logger.exception(err_msg)
                errorMessage([err_msg])

            else:
                self.imagePathLabel.setText(self._image.path)

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

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, select: bool) -> None:
        '''Select/unselect the widget and emit the "clicked" signal

        :param select: True - select the widget, False - unselect it
        '''

        self._selected = select
        self.thumbnailWidget.setMarked(select)

        self.clicked.emit()

    def mouseReleaseEvent(self, event) -> None:
        self.selected = not self.selected

        event.ignore()

    def hideEvent(self, event) -> None:
        self.hidden.emit()

        event.accept()

    def _callOnImage(self, func: Callable[..., None], *args, **kwargs) -> None:
        try:
            func(self._image, *args, **kwargs)

        except OSError as e:
            logger.exception(e)
            self.error.emit(str(e))

        else:
            self.selected = False
            self.hide()

            if self._conf['delete_dirs']:
                self._image.del_parent_dir()

    def delete(self):
        '''Delete the image from the disk, hide its "DuplicateWidget"
        instance and unselect it. If the preference "Delete folders
        if they are empty..." is on, also delete empty folders. Emit
        the "error" signal with the error message, if something went
        wrong during the process
        '''

        self._callOnImage(core.Image.delete)

    def move(self, dst: core.FolderPath):
        '''Move the image to a new location, hide its "DuplicateWidget"
        instance and unselect it. If the preference "Delete folders
        if they are empty..." is on, also delete empty folders. Emit
        the "error" signal with the error message, if something went
        wrong during the process

        :param dst: new location, e.g. "/new/location"
        '''

        self._callOnImage(core.Image.move, dst)
