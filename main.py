import logging
import sys

from PyQt5.QtWidgets import QApplication

import doppelganger.gui as gui

if __name__ == '__main__':
    logger = logging.getLogger('main')
    logger.setLevel(logging.WARNING)
    fh = logging.FileHandler('errors.log')
    FORMAT = '{asctime} - {name} - {levelname} - {message}'
    formatter = logging.Formatter(fmt=FORMAT, style='{')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    app = QApplication(sys.argv)
    ex = gui.MainForm()
    ex.show()
    sys.exit(app.exec_())
