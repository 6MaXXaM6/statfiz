"""График величины во времени — "схлопывающийся": ось времени от начала опыта до сейчас."""

import numpy as np
import pyqtgraph as pg

from ui import style
from ui.plots.base import StaticPlot, pen, show_line_at

POINTS_PER_PIXEL = 0.5  # больше точек на пиксель — рисуем не линию, а полосу min…max


def envelope(t, v, bins):
    """Разбить ряд на bins частей и вернуть (t, min, max) по каждой части."""
    edges = np.linspace(0, len(t), bins + 1).astype(int)
    starts = edges[:-1]
    t_mid = t[np.minimum((starts + edges[1:]) // 2, len(t) - 1)]
    return t_mid, np.minimum.reduceat(v, starts), np.maximum.reduceat(v, starts)


class TimePlot(StaticPlot):
    """Кривая v(t), текущая точка, линия текущего значения и теоретическое среднее.

    Пока точек мало, это обычная ломаная. Когда за долгий опыт их становится больше,
    чем пикселей, рисуется закрашенная полоса от минимума до максимума на каждом
    участке — выглядит так же, а рисуется во много раз быстрее.
    """

    def __init__(self):
        super().__init__(xlabel="время t, пс")
        self.curve = self.plot(pen=pen(style.REL, 0.08))
        self.low_edge = pg.PlotCurveItem(pen=pg.mkPen(style.REL, width=1))
        self.high_edge = pg.PlotCurveItem(pen=pg.mkPen(style.REL, width=1))
        self.band = pg.FillBetweenItem(self.low_edge, self.high_edge, brush=pg.mkBrush("#9aa5b8"))
        self.add_all(self.band, self.low_edge, self.high_edge)
        self.dot = pg.ScatterPlotItem(size=style.px(0.7), brush=style.HILITE, pen=pg.mkPen("k", width=1.5))
        self.dot.setZValue(10)
        self.addItem(self.dot)
        self.current = self.line(0, style.HILITE, dashed=True)
        self.mean_line = self.line(0, style.THEORY, width=0.1, dotted=True)

    def configure(self, value_label, low, high):
        self.set_axis_label("left", value_label + ", м/с")
        self.setYRange(low, high, padding=0)

    def update_view(self, series, theory_mean=None):
        t, v = series.data()
        bins = max(int(self.width() * POINTS_PER_PIXEL), 10)
        dense = len(t) > bins
        if dense:
            tb, lo, hi = envelope(t, v, bins)
            self.low_edge.setData(tb, lo)
            self.high_edge.setData(tb, hi)
            self.curve.setData([], [])
        else:
            self.curve.setData(t, v)
        for item in (self.band, self.low_edge, self.high_edge):
            item.setVisible(dense)

        last = series.last()
        self.dot.setData(*([[last[0]], [last[1]]] if last else [[], []]))
        show_line_at(self.current, last[1] if last else None)
        show_line_at(self.mean_line, theory_mean)
        # Ось времени от начала набора статистики: график не бежит, а "схлопывается".
        if len(t):
            self.setXRange(t[0], max(t[-1], t[0] + 1e-3), padding=0)
