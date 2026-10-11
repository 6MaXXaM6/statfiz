"""Панель графика: выбор величины, график во времени и распределение рядом с ним."""

import numpy as np
from PyQt5 import QtCore, QtWidgets

from model import theory as tf
from model.experiment import PAIR, SECOND, SINGLE
from ui import labels, style
from ui.plots.hist_plot import HistPlot
from ui.plots.time_plot import TimePlot
from ui.widgets import button, hbox, label, vbox

SIDE_STATS_WIDTH = 14       # ширина подписей справа от графиков (в базовых шрифтах)
QWIDGETSIZE_MAX = (1 << 24) - 1  # "без ограничения" для setMaximumWidth/Height в Qt

# Что можно выбрать в панели: (что наблюдаем, какая величина)
QUANTITIES = ([(obj, kind) for obj in (PAIR, SINGLE, SECOND) for kind in (tf.MODULUS, tf.PROJECTION)]
              + [(SINGLE, tf.ENERGY), (SECOND, tf.ENERGY)])


class GraphPanel(QtWidgets.QWidget):
    """Одна величина: заголовок с выбором и текущим значением, x(t) + распределение, среднее и дисперсия.

    Распределение стоит боком рядом с графиком во времени (общая ось значений).
    Кнопка ↻ поворачивает его в обычный вид — тогда график во времени временно
    скрывается и распределение занимает всю панель.

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
        # Графики и подписи (среднее, дисперсия): подписи под графиками или, когда графики
        # на весь экран, справа от них — чтобы графики не становились слишком длинными.
        self.body = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        self.body.setSpacing(style.px(0.15))
        self.body.addLayout(self.plots_row, 1)
        self.body.addWidget(self.stats)
        self.set_side_stats(False)
        self.setLayout(vbox(hbox(*header, spacing=style.px(0.4)), (self.body, 1), spacing=style.px(0.15)))
        self._last_count = 0
        self._hist_args = None

    def set_side_stats(self, side):
        """Подписи справа от графиков (side=True) или под ними."""
        if side:
            self.body.setDirection(QtWidgets.QBoxLayout.LeftToRight)
            # Сбоку ширина постоянная, и компоновка обязана её выделить (под графиками,
            # наоборот, подпись может сжиматься — Ignored).
            self.stats.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            self.stats.setFixedWidth(style.px(SIDE_STATS_WIDTH))
            self.stats.setMinimumHeight(0)
            self.stats.setMaximumHeight(QWIDGETSIZE_MAX)
            self.stats.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.stats.setFont(style.font(1.0))
        else:
            self.body.setDirection(QtWidgets.QBoxLayout.TopToBottom)
            self.stats.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
            self.stats.setMinimumWidth(0)
            self.stats.setMaximumWidth(QWIDGETSIZE_MAX)
            self.stats.setFont(style.font(0.85))
            # Высота постоянная: иначе от цифр (минус, степени) она меняется на пиксель,
            # и графики над ними дрожат.
            self.stats.setFixedHeight(2 * self.stats.fontMetrics().lineSpacing() + style.px(0.4))
            self.stats.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

    @property
    def quantity(self):
        return QUANTITIES[self.selector.currentIndex()]

    def show_quantity(self, obj, kind):
        """Выбрать величину программно (как будто её выбрали в списке)."""
        self.selector.setCurrentIndex(QUANTITIES.index((obj, kind)))

    def rotate(self):
        """Распределение боком (рядом с графиком во времени) ↔ обычный вид (только распределение)."""
        sideways = not self.hist_plot.sideways
        self.hist_plot.set_orientation(sideways)
        self.hist_plot.setYLink(self.time_plot if sideways else None)
        # История никуда не девается — она копится и дальше и снова видна после поворота обратно.
        self.time_plot.setVisible(sideways)
        if self._hist_args:
            self.hist_plot.configure(*self._hist_args)

    def configure(self, exp, low, high, peak):
        """Диапазон значений и масштаб плотности задаёт страница (у двух панелей они могут быть общими)."""
        obj, kind = self.quantity
        axis = labels.axis_label(obj, kind)
        x = np.linspace(low, high, 300)
        self._hist_args = (axis, x, tf.pdf(kind, x, exp.scale(obj, kind)), None, peak,
                           labels.density_unit(kind), kind != tf.ENERGY)
        self.time_plot.configure(axis, low, high)
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

        digits = 1 if kind == tf.ENERGY else 0
        self.value.setText("= <b>%s</b> %s" % (style.fmt(current, digits) if current is not None else "—",
                                               labels.unit(kind)))
        if self.time_plot.isVisible():
            theory_mean = tf.mean(kind, exp.scale(obj, kind)) if kind != tf.PROJECTION else None
            self.time_plot.update_view(series, theory_mean)
        self.hist_plot.update_view(exp.hist[obj, kind], current, highlight=new_sample and not fast)
        self.stats.setText(stats_text(exp, obj, kind))


def _nowrap(html):
    """Кусок текста, который нельзя переносить посередине (число с единицами и т.п.)."""
    return "<span style='white-space:nowrap'>%s</span>" % html


def stats_text(exp, obj, kind):
    """Среднее и дисперсия: опыт и теория. Переносы строк — только между частями,
    а не внутри числа или единиц (важно, когда подписи стоят узкой колонкой справа)."""
    hist = exp.hist[obj, kind]
    s = exp.scale(obj, kind)
    theory = "<span style='color:%s'>(теор.&nbsp;%%s)</span>" % style.THEORY
    digits = 2 if kind == tf.ENERGY else 0
    unit = labels.unit(kind)
    mean = "%s %s" % (
        _nowrap("⟨%s⟩ = <b>%s</b> %s" % (labels.quantity(obj, kind), style.fmt(hist.mean(), digits), unit)),
        _nowrap(theory % style.fmt(tf.mean(kind, s), digits)))
    divisor, var_unit = labels.variance_unit(kind)
    variance = "%s %s" % (
        _nowrap("D = <b>%s</b>%s" % (style.fmt(hist.variance() / divisor, 1), var_unit.replace(" ", "&nbsp;"))),
        _nowrap(theory % style.fmt(tf.variance(kind, s) / divisor, 1)))
    return mean + "<br>" + variance
