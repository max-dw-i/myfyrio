from PyQt5 import QtCore, QtGui


def make_image(path, width, height, suffix):
    '''Create an image and save it on the disk. Necessary for
    checking a few operations with the file system

    :param path: str, full name of the file,
    :param width: int, width in pixels,
    :param height: int, height in pixels,
    :param suffix: str, file suffix (without a dot)
    '''

    img = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
    for i in range(width):
        for j in range(height):
            img.setPixelColor(i, j, QtGui.QColor(QtCore.Qt.black))
    img.save(path, suffix.upper())
