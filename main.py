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
import pathlib
import sys

from PyQt5.QtWidgets import QApplication

import myfyrio.gui.mainwindow as mw
from myfyrio import resources
from myfyrio.logger import Logger


def _user_mode() -> None:
    resources.USER = True

    appdata_dir = pathlib.Path(resources.Config.CONFIG.get()).parent # pylint:disable=no-member
    if not appdata_dir.exists():
        appdata_dir.mkdir(parents=True)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', action='store_true')
    args = parser.parse_args()
    if args.user:
        _user_mode()

    Logger.setLogger()

    app = QApplication(sys.argv)
    ex = mw.MainWindow()
    ex.show()
    app.exec()
