"""Значки, нарисованные программой (без файлов): чётко выглядят при любом масштабе экрана."""

from PyQt5 import QtCore, QtGui

DARK = "#1c3f7a"


def _corner_arrows(size, color, outward):
    """Четыре стрелки по углам: наружу ("развернуть") или внутрь ("свернуть")."""
    pix = QtGui.QPixmap(size, size)
    pix.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pix)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    pen = QtGui.QPen(QtGui.QColor(color), max(2.0, size / 11), QtCore.Qt.SolidLine,
                     QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    p.setPen(pen)
    m = size * 0.14            # отступ от края
    inner = size * 0.40        # где кончается стрелка ближе к центру
    head = size * 0.22         # длина "уголка" наконечника
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        corner = QtCore.QPointF(size / 2 + sx * (size / 2 - m), size / 2 + sy * (size / 2 - m))
        near = QtCore.QPointF(size / 2 + sx * (size / 2 - inner), size / 2 + sy * (size / 2 - inner))
        p.drawLine(corner, near)
        tip = corner if outward else near
        d = -1 if outward else 1  # уголок смотрит в сторону острия
        p.drawLine(tip, QtCore.QPointF(tip.x() + d * sx * head, tip.y()))
        p.drawLine(tip, QtCore.QPointF(tip.x(), tip.y() + d * sy * head))
    p.end()
    return pix


def zoom_icon(size):
    """Значок кнопки "на весь экран": обычное состояние — стрелки наружу (тёмные),
    нажатая кнопка — стрелки внутрь (белые, на синем фоне нажатой кнопки)."""
    icon = QtGui.QIcon()
    icon.addPixmap(_corner_arrows(size, DARK, outward=True), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    icon.addPixmap(_corner_arrows(size, "#ffffff", outward=False), QtGui.QIcon.Normal, QtGui.QIcon.On)
    return icon
