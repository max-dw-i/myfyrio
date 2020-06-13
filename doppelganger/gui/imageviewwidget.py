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

Module implementing widget rendering found duplicate images
'''

from typing import Callable, Collection, List

from PyQt5 import QtCore, QtWidgets

from doppelganger import config, core
from doppelganger.gui.errornotifier import errorMessage
from doppelganger.gui.imagegroupwidget import ImageGroupWidget
from doppelganger.logger import Logger

logger = Logger.getLogger('imageviewwidget')


class ImageViewWidget(QtWidgets.QWidget):
    '''Widget rendering found duplicate images

    :param parent:              widget's parent (optional),

    :signal selected:           True - there are selected "DuplicateWidget"s,
                                False - otherwise, emitted when any
                                "DuplicateWidget" is clicked,
    :signal updateProgressBar:  new value of progress bar: float,
    :signal finished:           widgets rendering has been finished,
    :signal interrupted:        widgets rendering has been interrupted
                                by the user
    '''

    selected = QtCore.pyqtSignal(bool)
    updateProgressBar = QtCore.pyqtSignal(float)
    finished = QtCore.pyqtSignal()
    interrupted = QtCore.pyqtSignal()

    # Progress bar consts
    PROG_MIN = 70
    PROG_MAX = 100

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent=parent)

        self.conf: config.Config = None
        self._widgets: List[ImageGroupWidget] = []

        self._progressBarValue = float(self.PROG_MIN)
        self._interrupted = False
        self._errors: List[str] = []

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.setLayout(self._layout)

    def render(self, image_groups: Collection[core.Group]) -> None:
        '''Render "ImageGroupWidget"s with duplicate image groups

        :param image_groups: duplicate image groups
        '''

        if image_groups:
            self._render(image_groups)
        else:
            self.finished.emit()

            msg_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                'No duplicate images found',
                'No duplicate images have been found in the selected folders'
            )
            msg_box.exec()

    def _render(self, image_groups) -> None:
        if self.conf is None:
            err_msg = ('"Config" object must be assigned to the attribute '
                       '"conf" before continuing')
            raise ValueError(err_msg)

        prog_step = (self.PROG_MAX - self.PROG_MIN) / len(image_groups)

        for group in image_groups:
            if self._interrupted:
                self.interrupted.emit()
                return

            group_w = ImageGroupWidget(group, self.conf)
            group_w.error.connect(self._errors.append)

            for dup_w in group_w.widgets:
                dup_w.clicked.connect(self._hasSelected)

            self._layout.addWidget(group_w)
            self._widgets.append(group_w)
            self.updateGeometry()

            self._updateProgressBar(self._progressBarValue+prog_step)

            QtCore.QCoreApplication.processEvents()

        self.finished.emit()

    def _updateProgressBar(self, value: float) -> None:
        old_val = self._progressBarValue
        self._progressBarValue = value
        emit_val = int(value)
        if emit_val > old_val:
            self.updateProgressBar.emit(emit_val)

    def _hasSelected(self) -> None:
        for group_w in self._widgets:
            if group_w.hasSelected():
                self.selected.emit(True)
                return

        self.selected.emit(False)

    def clear(self) -> None:
        '''Clear the widget from the found duplicate images'''

        threadpool = QtCore.QThreadPool.globalInstance()
        threadpool.clear()
        threadpool.waitForDone()

        for group_w in self._widgets:
            group_w.deleteLater()

        self._widgets.clear()
        self._interrupted = False
        self._progressBarValue = float(self.PROG_MIN)

    def _callOnSelected(self, func: Callable[..., None], *args,
                        **kwargs) -> None:
        for group_w in self._widgets:
            func(group_w, *args, **kwargs)

        errorMessage(self._errors)
        self._errors.clear()

    def delete(self) -> None:
        '''Delete the selected images'''

        confirm = QtWidgets.QMessageBox.question(
            self,
            'Deletion confirmation',
            'Do you really want to remove the selected images?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
        )

        if confirm == QtWidgets.QMessageBox.Yes:
            self._callOnSelected(ImageGroupWidget.delete)

    def move(self) -> None:
        '''Move the selected images into another folder

        :param dst: folder to move the images into
        '''

        dialog = QtWidgets.QFileDialog(self, 'Open Folder', '')
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog
                          | QtWidgets.QFileDialog.ReadOnly)

        if dialog.exec():
            dst = dialog.selectedFiles()[0]
            self._callOnSelected(ImageGroupWidget.move, dst)

    def autoSelect(self) -> None:
        '''Automatic selection of "DuplicateWidget"s'''

        for group_w in self._widgets:
            group_w.autoSelect()

    def unselect(self) -> None:
        '''Unselect all selected "DuplicateWidget"s'''

        for group_w in self._widgets:
            group_w.unselect()

    def interrupt(self) -> None:
        self._interrupted = True
