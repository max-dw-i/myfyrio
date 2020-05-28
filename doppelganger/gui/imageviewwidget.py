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


import pathlib
import subprocess
import sys
from typing import Callable, Collection, Iterable, List

from PyQt5 import QtCore, QtGui, QtWidgets

from doppelganger import config, core, processing, resources, signals
from doppelganger.logger import Logger

logger = Logger.getLogger('widgets')


class InfoLabel(QtWidgets.QLabel):
    '''Abstract Label class'''

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
    '''Widget viewing info about images similarity'''


class ImageSizeLabel(InfoLabel):
    '''Widget viewing info about size of an image'''

    def __init__(self, width: core.Width, height: core.Height,
                 file_size: core.FileSize, size_format: core.SizeFormat,
                 widget_width: int, parent: QtWidgets.QWidget = None) -> None:
        units = str(size_format).split('.')[-1]
        text = f'{width}x{height}, {file_size} {units}'

        super().__init__(text, widget_width, parent)


class ImagePathLabel(InfoLabel):
    '''Widget viewing the path of an image'''

    def __init__(self, path: core.ImagePath, widget_width: int,
                 parent: QtWidgets.QWidget = None) -> None:
        path = QtCore.QFileInfo(path).canonicalFilePath()

        super().__init__(path, widget_width, parent)


class ThumbnailWidget(QtWidgets.QLabel):
    '''Widget renderering the thumbnail of an image'''

    def __init__(self, image: core.Image, size: int, lazy: bool,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.image = image
        self.size = size
        self.lazy = lazy

        self.empty = True

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                           QtWidgets.QSizePolicy.Fixed)

        self.setFrameStyle(QtWidgets.QFrame.Box)

        self._setEmptyPixmap()

        if lazy:
            self._setSize()

            self.qtimer = QtCore.QTimer(self)
            self.qtimer.timeout.connect(self._clear)
        else:
            self._makeThumbnail()

    def _setSize(self) -> None:
        width, height = self.image.scaling_dimensions(self.size)
        self.setFixedWidth(width)
        self.setFixedHeight(height)
        self.updateGeometry()

    def _setEmptyPixmap(self) -> None:
        self.pixmap = QtGui.QPixmap()
        self.setPixmap(self.pixmap)
        self.updateGeometry()

        self.empty = True

    def _setThumbnail(self) -> None:
        # If 'lazy' mode and the widget is not visible,
        # there's no point in setting the made thumbnail
        if not self.lazy or self.isVisible():
            if not self.pixmap.convertFromImage(self.image.thumb):
                self.pixmap = self._errorThumbnail()

            self.setPixmap(self.pixmap)
            self.updateGeometry()

            self.empty = False
            if self.lazy:
                self.qtimer.start(10000)
        else:
            self.image.thumb = None

    def _errorThumbnail(self) -> QtGui.QPixmap:
        logger.error('Something happened while converting QImage into QPixmap')
        size = self.size
        err_img = resources.Image.ERR_IMG.abs_path # pylint: disable=no-member
        err_pixmap = QtGui.QPixmap(err_img)
        return err_pixmap.scaled(size, size)

    def _makeThumbnail(self) -> None:
        if self.lazy:
            p = processing.ThumbnailProcessing(self.image, self.size, self)
        else:
            p = processing.ThumbnailProcessing(self.image, self.size)

        p.signals.finished.connect(self._setThumbnail)

        worker = processing.Worker(p.run)
        threadpool = QtCore.QThreadPool.globalInstance()
        threadpool.start(worker)

    def paintEvent(self, event) -> None:
        if self.lazy and self.empty:
            self._makeThumbnail()

        super().paintEvent(event)

    def _clear(self) -> None:
        if not self.empty and not self.isVisible():
            self.qtimer.stop()

            self._setEmptyPixmap()
            self.image.thumb = None

            self.empty = True

    def isVisible(self) -> bool:
        '''Check if the widget is visible by the user

        :return: True - visible, False - not visible
        '''

        return not self.visibleRegion().isNull()

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

    def __init__(self, image: core.Image, conf: config.Config,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.image = image
        self.conf = conf
        self.selected = False
        self.signals = signals.DuplicateWidgetSignals()

        self.setFixedWidth(self.conf['size'])

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.imageLabel = self._setThumbnailWidget()
        if self.conf['show_similarity']:
            self.similarityLabel = self._setSimilarityLabel()
        if self.conf['show_size']:
            self.imageSizeLabel = self._setImageSizeLabel()
        if self.conf['show_path']:
            self.imagePathLabel = self._setImagePathLabel()

        self.setLayout(self.layout)

    def _setThumbnailWidget(self) -> ThumbnailWidget:
        imageLabel = ThumbnailWidget(self.image, self.conf['size'],
                                     self.conf['lazy'])
        self.layout.addWidget(imageLabel)
        self.layout.setAlignment(imageLabel, QtCore.Qt.AlignHCenter)
        self.updateGeometry()

        return imageLabel

    def _setSimilarityLabel(self) -> SimilarityLabel:
        similarity = self.image.similarity()
        similarityLabel = SimilarityLabel(f'{similarity}%', self.conf['size'])
        self.layout.addWidget(similarityLabel)
        self.updateGeometry()

        return similarityLabel

    def _setImageSizeLabel(self) -> ImageSizeLabel:
        try:
            width, height = self.image.width, self.image.height
        except OSError as e:
            logger.error(e)
            width, height = (0, 0)

        size_format = core.SizeFormat(self.conf['size_format'])

        try:
            filesize = self.image.filesize(size_format)
        except OSError as e:
            logger.error(e)
            filesize = 0

        imageSizeLabel = ImageSizeLabel(width, height, filesize,
                                        size_format, self.conf['size'])
        self.layout.addWidget(imageSizeLabel)
        self.updateGeometry()

        return imageSizeLabel

    def _setImagePathLabel(self) -> ImagePathLabel:
        imagePathLabel = ImagePathLabel(self.image.path, self.conf['size'])
        self.layout.addWidget(imagePathLabel)
        self.updateGeometry()

        return imagePathLabel

    def openImage(self) -> None:
        '''Open the image in the OS default image viewer'''

        open_image_command = {'linux': 'xdg-open',
                              'win32': 'explorer',
                              'darwin': 'open'}
        command = open_image_command.get(sys.platform, 'Unknown platform')

        try:
            subprocess.run([command, self.image.path], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logger.error(e, exc_info=True)

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
                logger.error(e)

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

        event.ignore()

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

    def __init__(self, image_group: Iterable[core.Image], conf: config.Config,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self.conf = conf
        self.image_group = image_group
        self.widgets: List[DuplicateWidget] = []

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.layout.setSpacing(10)

        self._setDuplicateWidgets()

        self.setLayout(self.layout)

    def _setDuplicateWidgets(self) -> None:
        lazy = self.conf['lazy']

        for image in self.image_group:
            dupl_w = DuplicateWidget(image, self.conf)
            while not lazy and dupl_w.imageLabel.empty:
                QtCore.QCoreApplication.processEvents()

            self.widgets.append(dupl_w)
            self.layout.addWidget(dupl_w)
            self.updateGeometry()

    def isVisible(self) -> bool:
        '''Check if the widget is visible by the user

        :return: True - visible, False - not visible
        '''

        return not self.visibleRegion().isNull()

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

    def __init__(self, conf: config.Config, parent: QtWidgets.QWidget = None) \
        -> None:
        super().__init__(parent)

        self.conf = conf
        self.widgets: List[ImageGroupWidget] = []

        self.signals = signals.WidgetsRenderingSignals()
        self.progressBarValue: float = 0.0
        self.interrupted = False

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setLayout(self.layout)

    def render(self, image_groups: Collection[core.Group]) -> None:
        '''Create and render "ImageGroupWidget"s

        :param image_groups: groups of similar images
        '''

        step = self._progressBarStep(len(image_groups))

        for group in image_groups:
            if self.interrupted:
                self.signals.interrupted.emit()
                return

            widget = ImageGroupWidget(group, self.conf)
            self.layout.addWidget(widget)
            self.widgets.append(widget)
            self.updateGeometry()

            self._updateProgressBar(self.progressBarValue+step)

            QtCore.QCoreApplication.processEvents()

        self.signals.finished.emit()

    def _updateProgressBar(self, value: float) -> None:
        self.progressBarValue = value
        self.signals.update_progressbar.emit(value)

    def _progressBarStep(self, denominator: int) -> float:
        current = self.progressBarValue
        numerator = (100 - current) if current else 100
        return numerator / denominator

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

        if self.conf['lazy']:
            threadpool = QtCore.QThreadPool.globalInstance()
            threadpool.clear()
            threadpool.waitForDone()

        for group_w in self.widgets:
            group_w.deleteLater()

        self.widgets = []

    def delete(self) -> None:
        '''Delete selected images'''

        try:
            self._callOnSelectedWidgets(DuplicateWidget.delete)
        except OSError as e:
            err_msg = f'Error occured while removing image "{e}"'
            logger.error(err_msg)

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
            logger.error(err_msg)

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

    def setInterrupted(self) -> None:
        self.interrupted = True
