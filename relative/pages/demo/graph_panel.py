"""Панель графика: выбор величины, график во времени и распределение рядом с ним."""

import numpy as np
from PyQt5 import QtCore, QtWidgets

from model import theory as tf
from model.experiment import PAIR, SECOND, SINGLE
from ui import labels, style
from ui.plots.hist_plot import HistPlot
from ui.plots.time_plot import TimePlot
from ui.widgets import button, hbox, label, vbox

# Что можно выбрать в панели: (что наблюдаем, какая величина)
QUANTITIES = [(obj, kind) for obj in (PAIR, SINGLE, SECOND) for kind in (tf.MODULUS, tf.PROJECTION)]


class GraphPanel(QtWidgets.QWidget):
    """Одна величина: заголовок с выбором и текущим значением, v(t) + распределение, среднее и дисперсия.

    quantity_changed — выбрали другую величину; close_clicked — нажали ✕ (если панель можно закрыть).
    """

    quantity_changed = QtCore.pyqtSignal()
    close_clicked = QtCore.pyqtSignal()

    def __init__(self, obj=PAIR, kind=tf.MODULUS, closable=False):
        super().__init__()
        self.selector = QtWidgets.QComboBox()
        self.selector.setFont(style.font(1.1, bold=True))
        for o, k in QUANTITIES:
            self.selector.addItem(labels.quantity_plain(o, k))
        self.selector.setCurrentIndex(QUANTITIES.index((obj, kind)))
        self.selector.currentIndexChanged.connect(lambda _i: self.quantity_changed.emit())
        self.value = label(size=1.2)
        self.value.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        header = [self.selector, (self.value, 1)]
        if closable:
            header.append(button("✕", self.close_clicked.emit))

        self.time_plot = TimePlot()
        self.hist_plot = HistPlot(sideways=True)
        self.hist_plot.setYLink(self.time_plot)
        self.hist_plot.rotate_clicked.connect(self.rotate)
        self.plots_row = hbox((self.time_plot, 3), (self.hist_plot, 2), spacing=0)
        self.stats = label(size=0.85, shrinkable=True)
        # Высота подписей постоянная: иначе от цифр (минус, степени) она меняется на пиксель,
        # и графики над ними дрожат.
        self.stats.setFixedHeight(2 * self.stats.fontMetrics().lineSpacing() + style.px(0.4))
        self.setLayout(vbox(hbox(*header, spacing=style.px(0.4)), (self.plots_row, 1), self.stats, spacing=style.px(0.15)))
        self._last_count = 0

    @property
    def quantity(self):
        return QUANTITIES[self.selector.currentIndex()]

    def rotate(self):
        """Распределение боком (общая ось с графиком во времени) ↔ обычный вид."""
        sideways = not self.hist_plot.sideways
        self.hist_plot.set_orientation(sideways)
        self.hist_plot.setYLink(self.time_plot if sideways else None)
        self.plots_row.setStretch(1, 2 if sideways else 3)  # в обычном виде нужно больше ширины
        self.hist_plot.configure(*self._hist_args)

    def configure(self, exp, low, high, peak):
        """Диапазон значений и масштаб плотности задаёт страница (у двух панелей они могут быть общими)."""
        obj, kind = self.quantity
        name = labels.quantity(obj, kind)
        x = np.linspace(low, high, 300)
        self._hist_args = (name, x, tf.pdf(kind, x, exp.sigma(obj)), None, peak)
        self.time_plot.configure(name, low, high)
        self.hist_plot.configure(*self._hist_args)
        self._last_count = exp.series[obj, kind].count

    def refresh(self, exp, fast):
        obj, kind = self.quantity
        series = exp.series[obj, kind]
        last = series.last()
        current = last[1] if last else None
        # Новое значение "подращивает" свой столбик — в медленном режиме он подсвечивается.
        new_sample = series.count > self._last_count
        self._last_count = series.count

        sigma = exp.sigma(obj)
        self.value.setText("= <b>%s</b> м/с" % (style.fmt(current) if current is not None else "—"))
        self.time_plot.update_view(series, tf.mean(kind, sigma) if kind == tf.MODULUS else None)
        self.hist_plot.update_view(exp.hist[obj, kind], current, highlight=new_sample and not fast)
        self.stats.setText(stats_text(exp, obj, kind))


def stats_text(exp, obj, kind):
    """Среднее и дисперсия: опыт и теория."""
    hist = exp.hist[obj, kind]
    sigma = exp.sigma(obj)
    theory = "<span style='color:%s'>(теор. %%s)</span>" % style.THEORY
    mean = "⟨%s⟩ = <b>%s</b> %s м/с" % (
        labels.quantity(obj, kind), style.fmt(hist.mean()), theory % style.fmt(tf.mean(kind, sigma)))
    variance = "D = <b>%s</b> %s ·10³ (м/с)²" % (
        style.fmt(hist.variance() / 1e3, 1), theory % style.fmt(tf.variance(kind, sigma) / 1e3, 1))
    return mean + "<br>" + variance
