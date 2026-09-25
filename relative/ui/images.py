"""Загрузка картинок из папки assets."""

import os

from PyQt5 import QtCore, QtGui

from ui import style


def load_pixmap(filename, width, height):
    """Картинка, вписанная в width×height, или None, если файла нет."""
    if not filename:
        return None
    path = style.resource_path(filename)
    pix = QtGui.QPixmap(path) if os.path.exists(path) else QtGui.QPixmap()
    if pix.isNull():
        return None
    return pix.scaled(width, height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
