import logging
import logging.handlers
import sys

from PyQt5.QtWidgets import QApplication

import doppelganger.gui as gui

if __name__ == '__main__':
    logger = logging.getLogger('main')
    logger.setLevel(logging.WARNING)
    rh = logging.handlers.RotatingFileHandler('errors.log', maxBytes=1024**2, backupCount=1)
    FORMAT = '{asctime} - {name} - {levelname} - {message}'
    formatter = logging.Formatter(fmt=FORMAT, style='{')
    rh.setFormatter(formatter)
    logger.addHandler(rh)

    app = QApplication(sys.argv)
    ex = gui.MainForm()
    ex.show()
    sys.exit(app.exec_())
