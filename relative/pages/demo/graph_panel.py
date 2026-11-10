"""Панель графика: выбор величины, график во времени и распределение рядом с ним."""

import settings

import numpy as np
from PyQt5 import QtCore, QtWidgets

from model import theory as tf
from model.experiment import PAIR, SECOND, SINGLE
from pages.demo.readouts import significant, stats_ready
from ui import labels, style, units
from ui.plots.hist_plot import HistPlot
from ui.plots.time_plot import TimePlot
from ui.widgets import button, hbox, label, vbox


# Что можно выбрать в панели: (что наблюдаем, какая величина)
# Набор и порядок пунктов списка; написание символов менять в ui/labels._PLAIN, HTML-подписи — в _HTML.
QUANTITIES = ([(obj, kind) for obj in (PAIR, SINGLE, SECOND) for kind in (tf.MODULUS, tf.PROJECTION)]
              + [(SINGLE, tf.ENERGY), (SECOND, tf.ENERGY)])


# Панель величины; значения предоставляет опыт, внешний вид графиков — ui/plots/.
class GraphPanel(QtWidgets.QWidget):
    """Одна величина: выбор и статистика в шапке, x(t) + распределение.

    Распределение стоит боком рядом с графиком во времени (общая ось значений).
    Кнопка ↻ поворачивает его в обычный вид — тогда график во времени временно
    скрывается и распределение занимает всю панель.

    quantity_changed — выбрали другую величину; close_clicked — нажали ✕ (если панель можно закрыть).
    """

    quantity_changed = QtCore.pyqtSignal()
    close_clicked = QtCore.pyqtSignal()

    # Здесь менять заголовок, список, кнопки и пропорции блока; текущие числа обновляются в refresh().
    def __init__(self, obj=PAIR, kind=tf.MODULUS, closable=False):
        super().__init__()
        self.selector = QtWidgets.QComboBox()
        self.selector.setFont(style.font(settings.SELECTOR_FONT, bold=True))
        for o, k in QUANTITIES:
            self.selector.addItem(labels.quantity_plain(o, k))
        self.selector.setCurrentIndex(QUANTITIES.index((obj, kind)))
        self.selector.currentIndexChanged.connect(lambda _i: self.quantity_changed.emit())
        # Вся шапка — один ряд, без номеров панелей и мгновенных чисел.
        header = [self.selector]

        self.time_plot = TimePlot()
        self.hist_plot = HistPlot(sideways=True)
        self.hist_plot.setYLink(self.time_plot)
        self.hist_plot.rotate_clicked.connect(self.rotate)
        # Соотношение ширин истории и распределения сейчас 3:2; менять числа для другой компоновки.
        self.plots_row = hbox((self.time_plot, 3), (self.hist_plot, 2), spacing=0)
        # Статистика всегда в шапке, в том числе при повороте и «только графиках».
        self.stats = label(size=settings.STATS_FONT)
        self.stats.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self.stats.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.stats.installEventFilter(self)
        header.append((self.stats, 1))
        self.rescale_layout()
        # Эта строка заменяет исходный символ ↻ из HistPlot; видимую надпись презентации менять здесь.
        self.hist_plot.rotate_button.setText("↻ Повернуть")
        header.append(self.hist_plot.rotate_button)
        if closable:
            header.append(button("✕", self.close_clicked.emit))
        self.header = QtWidgets.QFrame()
        self.header.setObjectName("plotHeader")
        self.header.setLayout(hbox(*header, spacing=style.px(.4),
                                  margins=(style.px(.3), style.px(.2), style.px(.3), style.px(.2))))
        self.setLayout(vbox(self.header, (self.plots_row, 1), spacing=style.px(.2)))
        self._last_count = 0
        self._hist_args = None

    # Фиксируем высоту одной строки: изменение цифр не двигает графики.
    def rescale_layout(self):
        self.stats.setFont(style.font(settings.STATS_FONT))
        self.stats.setFixedHeight(self.stats.fontMetrics().lineSpacing() + style.px(.6))

    def eventFilter(self, watched, event):
        if watched is self.stats and event.type() == QtCore.QEvent.Resize:
            self._fit_stats_font()
        return super().eventFilter(watched, event)

    def _fit_stats_font(self):
        """На узкой панели уменьшаем только текст статистики, сохраняя одну строку."""
        font = style.font(settings.STATS_FONT)
        self.stats.setFont(font)
        while font.pixelSize() > 8 and self.stats.sizeHint().width() > self.stats.width():
            font.setPixelSize(font.pixelSize() - 1)
            self.stats.setFont(font)

    def refresh_stats(self, exp):
        obj, kind = self.quantity
        self.stats.setText(stats_text(exp, obj, kind))
        self._fit_stats_font()
        _, var_unit = labels.variance_unit(kind)
        self.stats.setToolTip(
            "Среднее — в единицах оси: %s. Дисперсия —%s.\n"
            "Красным показана теория. Первые %d шагов числа скрыты;\n"
            "это задержка показа, а не гарантия статистической точности."
            % (labels.unit(kind), var_unit, settings.STATS_MIN_STEPS))

    # Вернуть пару (объект, величина), соответствующую выбранному пункту списка.
    @property
    def quantity(self):
        return QUANTITIES[self.selector.currentIndex()]

    # Программный аналог выбора из списка; obj/kind должны входить в QUANTITIES.
    def show_quantity(self, obj, kind):
        """Выбрать величину программно (как будто её выбрали в списке)."""
        self.selector.setCurrentIndex(QUANTITIES.index((obj, kind)))

    # Меняется только способ показа: вертикальная шкала общая с историей только при боковом виде.
    def rotate(self):
        """Распределение боком (рядом с графиком во времени) ↔ обычный вид (только распределение)."""
        sideways = not self.hist_plot.sideways
        self.hist_plot.set_orientation(sideways)
        self.hist_plot.setYLink(self.time_plot if sideways else None)
        # История никуда не девается — она копится и дальше и снова видна после поворота обратно.
        self.time_plot.setVisible(sideways)
        if self._hist_args:
            self.hist_plot.configure(*self._hist_args)
        self.quantity_changed.emit()  # перерисовать и на паузе, не дожидаясь шага

    # Перенастроить оси и теорию по параметрам опыта; тексты единиц приходят из ui/labels.py.
    def configure(self, exp, low, high, peak):
        """Диапазон значений и масштаб плотности задаёт страница (у двух панелей они могут быть общими)."""
        obj, kind = self.quantity
        axis = labels.axis_label(obj, kind)
        x = np.linspace(low, high, 300)
        self._hist_args = (axis, x, tf.pdf(kind, x, exp.scale(obj, kind)), None, peak,
                           labels.density_unit(kind), False, units.value_factor(kind))
        self.time_plot.configure(axis, low, high, units.value_factor(kind), units.TIME_FACTOR)
        self.hist_plot.configure(*self._hist_args)
        self._last_count = exp.series[obj, kind].count

    # Обновить текущую точку, число и столбики; статистика отдельно в refresh_stats().
    def refresh(self, exp, fast):
        obj, kind = self.quantity
        series = exp.series[obj, kind]
        current = exp.current_value(obj, kind)
        # Новое значение "подращивает" свой столбик — в медленном режиме он подсвечивается.
        new_sample = series.count > self._last_count
        self._last_count = series.count

        if self.time_plot.isVisible():
            theory_mean = tf.mean(kind, exp.scale(obj, kind)) if kind != tf.PROJECTION else None
            self.time_plot.update_view(series, theory_mean, current=(exp.gas.time, current))
        self.hist_plot.update_view(exp.hist[obj, kind], current, highlight=new_sample and not fast)


# Сохраняет число вместе с единицами при переносе текста; видимые слова менять в stats_text().
def _nowrap(html):
    """Кусок текста, который нельзя переносить посередине (число с единицами и т.п.)."""
    return "<span style='white-space:nowrap'>%s</span>" % html


# Подписи шапки. Единицы среднего уже на оси, D — в квадрате этих единиц.
def stats_text(exp, obj, kind):
    """Одна строка с двумя значащими цифрами, без изменения накопленных данных."""
    if not stats_ready(exp):
        return "Набор статистики… ⟨%s⟩ = —; D = —" % labels.quantity(obj, kind)
    hist = exp.hist[obj, kind]
    scale = exp.scale(obj, kind)
    factor = units.value_factor(kind)
    theory = "<span style='color:%s'>(теор.&nbsp;%%s)</span>" % style.THEORY
    mean = _nowrap("⟨%s⟩ = <b>%s</b> %s" % (
        labels.quantity(obj, kind), significant(hist.mean() * factor), theory % significant(tf.mean(kind, scale) * factor)))
    divisor, _ = labels.variance_unit(kind)
    # Для скорости сохраняем прежний масштаб дисперсии 10³, явно указывая деление.
    name = "D/10³" if divisor == 1e3 else "D"
    variance = _nowrap("%s = <b>%s</b> %s" % (
        name, significant(hist.variance() * factor**2 / divisor), theory % significant(tf.variance(kind, scale) * factor**2 / divisor)))
    return mean + "&nbsp;&nbsp; " + variance
