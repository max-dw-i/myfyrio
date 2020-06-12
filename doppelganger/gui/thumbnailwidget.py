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

Module implementing widget viewing image thumbnails
'''


from PyQt5 import QtCore, QtGui, QtWidgets

from doppelganger import core, resources, workers
from doppelganger.logger import Logger

logger = Logger.getLogger('thumbnailwidget')


class ThumbnailWidget(QtWidgets.QLabel):
    '''Widget renderering an image thumbnail

    :param image:           "Image" object,
    :param thumbnail_size:  the biggest dimension (width or height) of
                            the image thumbnail,
    :param lazy:            True - use the "lazy" mode (thumbnails are made
                            only when the widget is visible to the user),
                            False - normal mode (thumbnails are made when
                            the widget is made),
    :param parent:          widget's parent (optional)
    '''

    KEEP_TIME_MSEC = 10000

    def __init__(self, image: core.Image, thumbnail_size: int, lazy: bool,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self._image = image
        self._size = thumbnail_size
        self._lazy = lazy

        self.empty = True

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                           QtWidgets.QSizePolicy.Fixed)

        self.setFrameStyle(QtWidgets.QFrame.Box)

        self._pixmap = self._setEmptyPixmap()

        if lazy:
            self._setSize()

            self._qtimer = QtCore.QTimer(self)
            self._qtimer.timeout.connect(self._clear)
        else:
            self._makeThumbnail()

    def _setSize(self) -> None:
        width, height = self._image.scaling_dimensions(self._size)
        self.setFixedWidth(width)
        self.setFixedHeight(height)
        self.updateGeometry()

    def _setEmptyPixmap(self) -> QtGui.QPixmap:
        pixmap = QtGui.QPixmap()
        self.setPixmap(pixmap)
        self.updateGeometry()

        self.empty = True

        return pixmap

    def _setThumbnail(self) -> None:
        # If 'lazy' mode and the widget is not visible,
        # there's no point in setting the made thumbnail
        if not self._lazy or self.isVisible():
            if not self._pixmap.convertFromImage(self._image.thumb):
                self._pixmap = self._errorThumbnail()

            self.setPixmap(self._pixmap)
            self.updateGeometry()

            self.empty = False
            if self._lazy:
                self._qtimer.start(self.KEEP_TIME_MSEC)
        else:
            self._image.thumb = None

    def _errorThumbnail(self) -> QtGui.QPixmap:
        err_msg = 'Something went wrong while converting QImage into QPixmap'
        logger.exception(err_msg)

        size = self._size
        err_img = resources.Image.ERR_IMG.abs_path # pylint: disable=no-member
        err_pixmap = QtGui.QPixmap(err_img)
        return err_pixmap.scaled(size, size)

    def _makeThumbnail(self) -> None:
        if self._lazy:
            p = workers.ThumbnailProcessing(self._image, self._size, self)
        else:
            p = workers.ThumbnailProcessing(self._image, self._size)

        p.finished.connect(self._setThumbnail)

        worker = workers.Worker(p.run)
        threadpool = QtCore.QThreadPool.globalInstance()
        threadpool.start(worker)

    def paintEvent(self, event) -> None:
        if self._lazy and self.empty:
            self._makeThumbnail()

        super().paintEvent(event)

    def _clear(self) -> None:
        if not self.empty and not self.isVisible():
            self._qtimer.stop()

            self._setEmptyPixmap()
            self._image.thumb = None

            self.empty = True

    def isVisible(self) -> bool:
        '''Check if the widget is visible to the user

        :return: True - visible, False - not visible
        '''

        return not self.visibleRegion().isNull()

    def _mark(self) -> None:
        marked = self._pixmap.copy()
        width, height = marked.width(), marked.height()

        painter = QtGui.QPainter(marked)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        painter.setBrush(brush)
        painter.drawRect(0, 0, width, height)
        painter.end()
        self.setPixmap(marked)

    def setMarked(self, mark: bool) -> None:
        '''Mark the widget as selected/unselected (change colour)

        :param mark: True - mark as selected (make it darker),
                     False - mark as not selected (set the original image back)
        '''

        if mark:
            self._mark()
        else:
            self.setPixmap(self._pixmap)
