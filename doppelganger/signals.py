'''Custom signals'''

from PyQt5 import QtCore

class Signals(QtCore.QObject):
    '''Supported signals:
    ------------------
    :update_info: label to update: str, text to set: str,
    :update_progressbar: new progress bar's value: float,
    :error: error traceback,
    :result: groups of duplicate images: List[core.Group],
    :finished: processing is done,
    :interrupted: image processing must be stopped,
    :clicked: DuplicateWidget is clicked on
    '''

    update_info = QtCore.pyqtSignal(str, str)
    update_progressbar = QtCore.pyqtSignal(float)
    error = QtCore.pyqtSignal()
    result = QtCore.pyqtSignal(list)
    finished = QtCore.pyqtSignal()
    interrupted = QtCore.pyqtSignal()
    clicked = QtCore.pyqtSignal()