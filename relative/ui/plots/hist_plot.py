"""Распределение вероятностей: столбики эксперимента и кривая теории."""

import settings

import math

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

from ui import style
from ui.plots.base import StaticPlot, pen, show_line_at
from ui.widgets import overlay_button, place_overlay

FLASH_DECAY = settings.FLASH_DECAY   # за каждый кадр подсветка столбика гаснет в столько раз
FLASH_MIN = 0.03     # более слабая подсветка не рисуется
HEADROOM = settings.HIST_HEADROOM      # запас по высоте над максимумом теоретической кривой


def density_exponent(peak):
    """Показатель степени для оси плотности: 0.0012 с/м -> -3 (ось в единицах 10⁻³ с/м)."""
    if peak <= 0 or not np.isfinite(peak):
        return 0
    return int(math.floor(math.log10(peak)))


class HistPlot(StaticPlot):
    """Гистограмма + теория.

    sideways=True — распределение "лёжа на боку": значение величины по вертикали
    (так его можно поставить рядом с графиком во времени с общей осью),
    плотность вероятности — по горизонтали. sideways=False — обычный вид.

    Масштаб осей задаётся только в configure() по теории и во время опыта не меняется.
    Столбик выше края обрезается, а на краю рисуется треугольник-метка.
    Кнопка ↻ в углу отправляет сигнал rotate_clicked.
    """

    rotate_clicked = QtCore.pyqtSignal()

    def __init__(self, sideways=True):
        super().__init__()
        self.theory = self.plot(pen=pen(style.THEORY, settings.THEORY_LINE))
        self.theory.setZValue(5)
        self.other_theory = self.plot(pen=pen("#777777", dashed=True))
        self.other_theory.setZValue(4)
        self.current = self.line(0, style.HILITE, dashed=True)
        self.exp_mean = self.line(0, "k", dashed=True)
        self.clipped = pg.ScatterPlotItem(size=style.px(0.8), brush="#1a2a4a", pen=None)
        self.clipped.setZValue(6)
        self.addItem(self.clipped)
        self.rotate_button = overlay_button(self, "↻", "Повернуть распределение", self.rotate_clicked.emit)
        self.bars = None
        self.flash_bars = None
        self.sideways = None
        self.value_label = ""
        self.density_unit = "с/м"
        self.low, self.high = 0.0, 1.0
        self.exponent = 0
        self.top = 1.0
        self.flash = np.zeros(0)
        self._curves = {}
        self.set_orientation(sideways)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # pyqtgraph вызывает resizeEvent ещё до конца __init__, когда кнопки нет.
        button = self.__dict__.get("rotate_button")
        if button is not None:
            place_overlay(button, self)

    # --- ориентация: единственное место, где важно, что по какой оси ---
    def _xy(self, values, densities):
        """Координаты точки графика по (значение величины, плотность)."""
        return (densities, values) if self.sideways else (values, densities)

    def _bar_opts(self, centers, width, heights):
        n = len(centers)
        if self.sideways:
            return dict(x0=np.zeros(n), y=centers, width=heights, height=np.full(n, width))
        return dict(x=centers, y0=np.zeros(n), width=np.full(n, width), height=heights)

    def set_orientation(self, sideways):
        if sideways == self.sideways:
            return
        self.sideways = sideways
        for item in (self.bars, self.flash_bars):
            if item is not None:
                self.removeItem(item)
        empty = self._bar_opts(np.zeros(1), 1.0, np.zeros(1))
        self.bars = pg.BarGraphItem(brush=style.BAR, pen=pg.mkPen(style.BAR_EDGE, width=1), **empty)
        self.flash_bars = pg.BarGraphItem(pen=None, **empty)
        self.add_all(self.bars, self.flash_bars)
        angle = 0 if sideways else 90
        self.current.setAngle(angle)
        self.exp_mean.setAngle(angle)
        self.clipped.setSymbol("t2" if sideways else "t1")  # треугольник по направлению роста
        self.showAxis("left", not sideways)  # боком: ось значений — общая с соседним графиком
        self._apply_axes()
        self._draw_curves()

    # --- настройка под выбранную величину ---
    def configure(self, value_label, x, pdf, other_pdf=None, peak=None, density_unit="с/м", rescale=True):
        """value_label — подпись оси значений с единицами ("|v₁|, м/с");
        x, pdf — теоретическая кривая; other_pdf — вторая кривая пунктиром;
        peak — максимум плотности для масштаба оси (по умолчанию — максимум pdf);
        density_unit — единица плотности; rescale — показывать плотность в 10ⁿ единиц
        (для скоростей плотность ~10⁻³ с/м, для энергии этого не нужно).
        """
        self.value_label = value_label
        self.density_unit = density_unit
        self.low, self.high = x[0], x[-1]
        peak = pdf.max() if peak is None else peak
        self.exponent = density_exponent(peak) if rescale else 0
        self.top = HEADROOM * peak * self._density_factor()
        self._curves = {"x": x, "pdf": pdf, "other": other_pdf}
        self.flash = np.zeros(0)
        self._apply_axes()
        self._draw_curves()

    def _density_factor(self):
        return 10.0 ** (-self.exponent)

    def _apply_axes(self):
        power = "10%s " % style.sup(self.exponent) if self.exponent else ""
        density = "f, %s%s" % (power, self.density_unit)  # f — плотность вероятности
        value = self.value_label
        self.set_axis_label("bottom", density if self.sideways else value)
        if not self.sideways:
            self.set_axis_label("left", density)
        x_min, y_min = self._xy(self.low, 0.0)
        x_max, y_max = self._xy(self.high, self.top)
        self.setXRange(x_min, x_max, padding=0)
        self.setYRange(y_min, y_max, padding=0)

    def _draw_curves(self):
        if not self._curves:
            return
        k = self._density_factor()
        x, other = self._curves["x"], self._curves["other"]
        self.theory.setData(*self._xy(x, self._curves["pdf"] * k))
        self.other_theory.setVisible(other is not None)
        if other is not None:
            self.other_theory.setData(*self._xy(x, other * k))

    # --- кадр ---
    def update_view(self, hist, current=None, highlight=False, show_mean=False):
        """highlight=True — подсветить столбик, в который попало текущее значение."""
        dens = hist.density() * self._density_factor()
        shown = np.minimum(dens, self.top)
        self.bars.setOpts(**self._bar_opts(hist.centers, hist.width, shown))
        over = dens > self.top
        self.clipped.setData(*self._xy(hist.centers[over], np.full(over.sum(), self.top * 0.97)))
        self._update_flash(hist, shown, current if highlight else None)
        show_line_at(self.current, current)
        show_line_at(self.exp_mean, hist.mean() if show_mean else None)

    def _update_flash(self, hist, heights, value):
        """Столбик, который только что подрос, вспыхивает оранжевым и плавно гаснет."""
        if len(self.flash) != len(heights):
            self.flash = np.zeros(len(heights))
        self.flash *= FLASH_DECAY
        k = hist.bin_of(value) if value is not None else None
        if k is not None:
            self.flash[k] = 1.0
        lit = np.nonzero(self.flash > FLASH_MIN)[0]
        self.flash_bars.setVisible(len(lit) > 0)
        if len(lit):
            brushes = []
            for alpha in self.flash[lit]:
                color = QtGui.QColor(style.HILITE)
                color.setAlphaF(float(alpha))
                brushes.append(pg.mkBrush(color))
            self.flash_bars.setOpts(brushes=brushes, **self._bar_opts(hist.centers[lit], hist.width, heights[lit]))
