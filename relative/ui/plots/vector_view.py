"""Векторная диаграмма скоростей."""

import settings

import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from ui import style
from ui.plots.base import Arrow, StaticPlot

HEAD = 0.12  # наконечник стрелки в долях радиуса диаграммы


class VectorView(StaticPlot):
    """v1, v2 из общего начала и v_отн = v1 − v2 (из конца v2 в конец v1); проекция — вектор на оси x."""

    def __init__(self, embedded=False):
        super().__init__(canvas=True)
        self.embedded = embedded
        self._pixel_scale_key = None
        if embedded:
            self.setBackground(None)
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            self.setStyleSheet("background: transparent; border: none;")
            self.getPlotItem().layout.setContentsMargins(0, 0, 0, 0)
        else:
            self.getViewBox().setBorder(pg.mkPen("#999999", width=1))
        self.axes = (self.line(0, "#bbbbbb", width=.05),
                     self.line(90, "#bbbbbb", width=.05))
        self.x_label = pg.TextItem("x", color="#888888", anchor=(1, 0))
        self.x_label.setFont(style.font(0.8))
        self.v1 = Arrow(style.MOL1)
        self.v2 = Arrow(style.MOL2)
        self.rel = Arrow(style.REL, width=0.28)
        self.proj = Arrow(style.PROJ, width=0.35)
        self.add_all(self.x_label, self.v1, self.v2, self.rel, self.proj)
        self.radius = 1.0
        self.set_sizes(settings.VECTOR_SIZE, settings.VECTOR_MIN_SIZE)

    def set_sizes(self, preferred, minimum):
        """Желаемая и наименьшая сторона (в базовых шрифтах). Если места мало, компоновка
        сама уменьшит диаграмму до minimum; рисунок остаётся квадратным (оси в одном масштабе)."""
        self._size_factors = preferred, minimum
        self._preferred = QtCore.QSize(style.px(preferred), style.px(preferred))
        self._minimum = QtCore.QSize(style.px(minimum), style.px(minimum))
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.setMinimumSize(QtCore.QSize(0, 0) if self.embedded else self._minimum)
        self.setMaximumSize(QtCore.QSize(16777215, 16777215) if self.embedded else self._preferred)
        self.updateGeometry()

    def rescale_layout(self):
        self.set_sizes(*self._size_factors)
        self.x_label.setFont(style.font(.8))

    def sizeHint(self):
        return self._preferred

    def minimumSizeHint(self):
        return self._minimum

    def set_radius(self, r):
        self.radius = r
        self._pixel_scale_key = None
        self.setRange(xRange=(-r, r), yRange=(-r, r), padding=0.02)
        self.x_label.setPos(r, 0)

    def match_pixel_scale(self, pixels_per_velocity):
        """Одинаковая длина одной и той же скорости в сосуде и построении."""
        view = self.getViewBox()
        key = pixels_per_velocity, view.width(), view.height()
        if key == self._pixel_scale_key or pixels_per_velocity <= 0:
            return
        self._pixel_scale_key = key
        width = view.width() / pixels_per_velocity
        height = view.height() / pixels_per_velocity
        self.setRange(xRange=(-.35 * width, .65 * width),
                      yRange=(-.4 * height, .6 * height), padding=0)
        self.x_label.setPos(.6 * width, 0)

    def update_view(self, exp, projection_of=None):
        """projection_of — чью проекцию на ось x показать (PAIR или SINGLE) или None."""
        for axis in self.axes:
            axis.setVisible(not self.embedded or projection_of is not None)
        self.x_label.setVisible(not self.embedded or projection_of is not None)
        head = HEAD * self.radius
        origin = (0.0, 0.0)
        v1 = exp.gas.vel[exp.i]
        v2 = exp.gas.vel[exp.j]
        self.v1.set(origin, v1, head)
        self.v2.set(origin, v2, head)
        self.rel.set(v2, v1 - v2, head)
        if projection_of is None:
            self.proj.clear()
        else:
            self.proj.set(origin, (exp.velocity(projection_of)[0], 0.0), head)
