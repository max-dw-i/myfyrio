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

-------------------------------------------------------------------------------

Module implementing widget starting/stopping duplicate images search
and showing info about the process
'''

import pathlib

from PyQt5 import QtWidgets, uic


class ProcessingGroupBox(QtWidgets.QGroupBox):
    '''Widget starting/stopping duplicate images search
    and showing info about the processt
    '''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        UI = pathlib.Path('doppelganger/resources/ui/processinggroupbox.ui')
        uic.loadUi(str(UI), self)

        self.labels = self.findChildren(QtWidgets.QLabel)

        self.startBtn.clicked.connect(self.startProcessing)
        self.stopBtn.clicked.connect(self.stopProcessing)

    def _clearWidget(self) -> None:
        for label in self.labels:
            self.updateLabel(label.property('alias'), str(0))

        self.processProg.setValue(0)

    def updateLabel(self, label_alias: str, text: str) -> None:
        '''Update text of the label

        :param label_alias: one of ("thumbnails", "image_groups",
                                    "remaining_images", "found_in_cache",
                                    "loaded_images", "duplicates"),
        :param text: new text of the label
        '''

        for label in self.labels:
            if label.property('alias') == label_alias:
                label_text = label.text().split(' ')
                label_text[-1] = text
                label.setText(' '.join(label_text))

    def startProcessing(self) -> None:
        '''Prepare all the widgets to image processing'''

        self._clearWidget()
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)

    def stopProcessing(self) -> None:
        '''Prepare all the widgets after image processing'''

        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self.processProg.setValue(100)
