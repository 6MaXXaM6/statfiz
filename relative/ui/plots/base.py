"""Общая основа всех графиков презентации."""

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from ui import style


def pen(color, width=0.12, dashed=False, dotted=False):
    """Перо для линий; width — в долях базового шрифта (линии толще на больших экранах)."""
    line = QtCore.Qt.DashLine if dashed else QtCore.Qt.DotLine if dotted else QtCore.Qt.SolidLine
    return pg.mkPen(color, width=style.px(width), style=line)


AXIS_WIDTH = 4.2   # ширина левой оси (подпись + числа вроде "-1000"), в базовых шрифтах
AXIS_HEIGHT = 2.6  # высота нижней оси (числа + подпись)


class StaticPlot(pg.PlotWidget):
    """График без управления мышью, с крупными подписями.

    canvas=True — "холст" без осей с одинаковым масштабом по x и y
    (для сосуда с молекулами и векторной диаграммы).
    """

    def __init__(self, xlabel="", ylabel="", canvas=False):
        super().__init__()
        self.setMenuEnabled(False)
        self.setMouseEnabled(False, False)
        self.hideButtons()
        if canvas:
            self.hideAxis("left")
            self.hideAxis("bottom")
            self.setAspectLocked(True)
            return
        for name in ("bottom", "left"):
            axis = self.getAxis(name)
            axis.setStyle(tickFont=style.font(0.8), tickLength=style.px(0.4))
            axis.setPen(pg.mkPen("k", width=2))
            axis.setTextPen("k")
        # Размер осей постоянный: иначе pyqtgraph подгоняет его под подписи делений,
        # и область графика "ездит", когда меняются числа на осях.
        self.getAxis("left").setWidth(style.px(AXIS_WIDTH))
        self.getAxis("bottom").setHeight(style.px(AXIS_HEIGHT))
        self.set_axis_label("bottom", xlabel)
        self.set_axis_label("left", ylabel)

    def set_axis_label(self, axis, text):
        self.getAxis(axis).setLabel(text, **{"font-size": "%dpx" % style.px(0.85)})

    def set_title(self, text, color="k"):
        self.setTitle(text, size="%dpx" % style.px(0.9), color=color)

    def line(self, angle, color, width=0.12, dashed=False, dotted=False):
        """Бесконечная прямая: angle=0 — горизонтальная, 90 — вертикальная."""
        item = pg.InfiniteLine(angle=angle, pen=pen(color, width, dashed, dotted))
        self.addItem(item)
        return item

    def add_all(self, *items):
        for item in items:
            self.addItem(item)


def show_line_at(line, value):
    """Поставить прямую в value или спрятать, если значения нет."""
    if value is None or not np.isfinite(value):
        line.hide()
    else:
        line.setValue(value)
        line.show()


class Arrow(QtWidgets.QGraphicsPathItem):
    """Стрелка-вектор в координатах графика (оси с одинаковым масштабом)."""

    def __init__(self, color, width=0.22):
        super().__init__()
        p = QtGui.QPen(QtGui.QColor(color))
        p.setWidthF(style.px(width))
        p.setCosmetic(True)  # толщина в пикселях экрана, а не в единицах графика
        p.setCapStyle(QtCore.Qt.RoundCap)
        p.setJoinStyle(QtCore.Qt.MiterJoin)
        self.setPen(p)
        self.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        self.setZValue(10)

    def set(self, start, vector, head):
        """Стрелка из точки start вдоль vector; head — длина наконечника в единицах графика."""
        x0, y0 = start
        dx, dy = vector
        path = QtGui.QPainterPath()
        length = np.hypot(dx, dy)
        if length > 1e-12:
            ux, uy = dx / length, dy / length
            head = min(head, 0.6 * length)
            x1, y1 = x0 + dx, y0 + dy
            bx, by = x1 - ux * head, y1 - uy * head  # основание наконечника
            half = 0.45 * head
            path.moveTo(x0, y0)
            path.lineTo(bx, by)
            path.addPolygon(QtGui.QPolygonF([
                QtCore.QPointF(x1, y1),
                QtCore.QPointF(bx - uy * half, by + ux * half),
                QtCore.QPointF(bx + uy * half, by - ux * half),
            ]))
            path.closeSubpath()
        self.setPath(path)

    def clear(self):
        self.setPath(QtGui.QPainterPath())
