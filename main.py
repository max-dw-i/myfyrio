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

import multiprocessing
import sys

from PyQt5.QtWidgets import QApplication

import myfyrio.gui.mainwindow as mw
from myfyrio.logger import Logger

def main() -> None:
    Logger.setLogger()

    app = QApplication(sys.argv)
    ex = mw.MainWindow()
    ex.show()
    app.exec()

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
