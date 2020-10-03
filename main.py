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

import argparse
import multiprocessing
import sys

from PyQt5.QtWidgets import QApplication

from myfyrio import resources
from myfyrio.gui import mainwindow
from myfyrio.logger import Logger


def main() -> None:
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', action='store_true')
    args = parser.parse_args()

    if args.user and getattr(sys, 'frozen', False):
        resources.USER = True

    Logger.setLogger()

    app = QApplication(sys.argv)
    mw = mainwindow.MainWindow()
    mw.show()
    app.exec()


if __name__ == '__main__':

    main()
