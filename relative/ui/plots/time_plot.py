"""График величины во времени — "схлопывающийся": ось времени от начала опыта до сейчас."""

import numpy as np
import pyqtgraph as pg

import settings
from ui import style
from ui.plots.base import StaticPlot, pen, show_line_at

class TimePlot(StaticPlot):
    """Кривая v(t), текущая точка, линия текущего значения и теоретическое среднее.

    Пока точек мало, это обычная ломаная. Когда за долгий опыт их становится больше,
    чем пикселей, рисуется закрашенная полоса от минимума до максимума на каждом
    участке — выглядит так же, а рисуется во много раз быстрее.
    """

    def __init__(self):
        super().__init__(xlabel="время t, пс")
        self.curve = self.plot(pen=pen(style.REL, settings.CURVE_LINE))
        self.live_tail = self.plot(pen=pen(style.REL, settings.CURVE_LINE))
        self.low_edge = pg.PlotCurveItem(pen=pg.mkPen(style.REL, width=1))
        self.high_edge = pg.PlotCurveItem(pen=pg.mkPen(style.REL, width=1))
        self.band = pg.FillBetweenItem(self.low_edge, self.high_edge, brush=pg.mkBrush(settings.COLOR_RANGE))
        self.spread_low = pg.PlotCurveItem(pen=None)
        self.spread_high = pg.PlotCurveItem(pen=None)
        self.spread = pg.FillBetweenItem(self.spread_low, self.spread_high, brush=settings.COLOR_SPREAD)
        self.average = self.plot(pen=pen(style.REL, .08))
        self.add_all(self.band, self.low_edge, self.high_edge, self.spread_low, self.spread_high, self.spread)
        self.average.setZValue(3)
        self.dot = pg.ScatterPlotItem(size=style.px(0.7), brush=style.HILITE, pen=pg.mkPen("k", width=1.5))
        self.dot.setZValue(10)
        self.addItem(self.dot)
        self.current = self.line(0, style.HILITE, width=settings.CURRENT_LINE, dashed=True)
        self.mean_line = self.line(0, style.THEORY, width=0.1, dotted=True)

    def configure(self, axis_label, low, high):
        """axis_label — подпись оси значений с единицами, например "|v₁|, м/с"."""
        self.set_axis_label("left", axis_label)
        self.setYRange(low, high, padding=0)

    def update_view(self, series, theory_mean=None, current=None):
        t, v = series.data()
        bins = max(int(self.getViewBox().width()), 1)
        dense = series.span > 1 or len(series.buckets) >= bins
        if dense and series.buckets:
            buckets = np.asarray(series.buckets)
            count = min(bins, len(buckets))
            # Раскладываем корзины по времени, объединяя их точные моменты.
            start, end = buckets[0, 0], buckets[-1, 1]
            index = np.clip(((buckets[:, 0]+buckets[:, 1])/2-start) /
                            max(end-start, 1e-12)*count, 0, count-1).astype(int)
            n = np.bincount(index, weights=buckets[:, 5], minlength=count)
            sums = np.bincount(index, weights=buckets[:, 6], minlength=count)
            squares = np.bincount(index, weights=buckets[:, 7], minlength=count)
            lo, hi = np.full(count, np.inf), np.full(count, -np.inf)
            np.minimum.at(lo, index, buckets[:, 2])
            np.maximum.at(hi, index, buckets[:, 3])
            valid = n > 0
            means = sums[valid]/n[valid]
            sigma = np.sqrt(np.maximum(squares[valid]/n[valid]-means**2, 0))
            tb = start+(np.arange(count)[valid]+.5)*(end-start)/count
            self.low_edge.setData(tb, lo[valid])
            self.high_edge.setData(tb, hi[valid])
            self.spread_low.setData(tb, means-sigma)
            self.spread_high.setData(tb, means+sigma)
            self.average.setData(tb, means)
            self.curve.setData([], [])
        else:
            self.curve.setData(t, v)
        for item in (self.band, self.low_edge, self.high_edge, self.spread,
                     self.spread_low, self.spread_high, self.average):
            item.setVisible(dense)

        recorded = series.last()
        last = current if current is not None else recorded
        # При смене T/массы на паузе показываем мгновенный скачок, не добавляя
        # фиктивные измерения в историю и гистограмму.
        if recorded is not None and last is not None and recorded != last:
            self.live_tail.setData([recorded[0], last[0]], [recorded[1], last[1]])
        else:
            self.live_tail.setData([], [])
        self.dot.setData(*([[last[0]], [last[1]]] if last else [[], []]))
        show_line_at(self.current, last[1] if last else None)
        show_line_at(self.mean_line, theory_mean)
        # Ось времени от начала набора статистики: график не бежит, а "схлопывается".
        if last is not None:
            start = t[0] if len(t) else last[0]
            self.setXRange(start, max(last[0], start + 1e-3), padding=0)
