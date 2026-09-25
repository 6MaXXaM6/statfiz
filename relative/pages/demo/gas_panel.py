"""Правая колонка: параметры газа. Настройки смеси видны только в режиме "Смесь"."""

from collections import namedtuple

from PyQt5 import QtCore, QtWidgets

from model.experiment import GAS_MIX, GAS_PURE
from model.physics import MAX_PARTICLES
from ui import style
from ui.widgets import Choice, ParamControl, card, vbox

# Параметры газа, при изменении которых газ создаётся заново
GasParams = namedtuple("GasParams", "gas_mode mass_a mass_b n_total n_b")


class GasPanel(QtWidgets.QWidget):
    gas_changed = QtCore.pyqtSignal()
    pair_chosen = QtCore.pyqtSignal(str)
    temperature_changed = QtCore.pyqtSignal(int)

    def __init__(self, exp):
        super().__init__()
        self.gas_mode = Choice(None, [(GAS_PURE, "Один газ"), (GAS_MIX, "Смесь A + B")])
        self.temperature = ParamControl("Температура T, К", 50, 1500, exp.temperature)
        self.n_total = ParamControl("Число молекул N", 2, MAX_PARTICLES, exp.n_total)
        self.mass_a = ParamControl("Масса A, а.е.м.", 1, 200, exp.mass_a)
        self.mass_b = ParamControl("Масса B, а.е.м.", 1, 200, exp.mass_b)
        self.n_b = ParamControl("Молекул B", 1, exp.n_total - 1, exp.n_b_mix)
        self.n_b.setToolTip("1 — в газе A одна «чужая» молекула B")
        self.pair = Choice("Пара молекул", [("AA", "A – A"), ("AB", "A – B"), ("BB", "B – B")])

        # Настройки смеси показываются только в режиме "Смесь"
        self.mix_widgets = (self.mass_b, self.n_b, self.pair)

        self.gas_mode.changed.connect(lambda _key: self.gas_changed.emit())
        for p in (self.mass_a, self.mass_b, self.n_total, self.n_b):
            p.changed.connect(lambda _value: self.gas_changed.emit())
        self.n_total.changed.connect(lambda n: self.n_b.set_range(1, max(1, n - 1)))
        self.pair.changed.connect(self.pair_chosen)
        self.temperature.changed.connect(self.temperature_changed)

        self.setFont(style.font(0.85))
        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(style.px(0.5))
        self.grid.setVerticalSpacing(style.px(0.1))
        grid_host = QtWidgets.QWidget()
        grid_host.setLayout(self.grid)
        self.setLayout(vbox(card(grid_host, title="Газ")))
        self.set_horizontal(False)

    def set_horizontal(self, horizontal):
        """Столбиком (колонка справа) или в несколько столбцов (полоса внизу страницы)."""
        if horizontal:
            columns = [[self.gas_mode, self.temperature, self.n_total],
                       [self.mass_a, self.mass_b, self.n_b], [self.pair]]
        else:
            columns = [[self.gas_mode, self.temperature, self.n_total, self.mass_a,
                        self.mass_b, self.n_b, self.pair]]
        # В нижней полосе место под настройки смеси оставляем и тогда, когда они скрыты:
        # иначе полоса меняет высоту при переключении "Один газ / Смесь" и графики прыгают.
        for w in self.mix_widgets:
            policy = w.sizePolicy()
            policy.setRetainSizeWhenHidden(horizontal)
            w.setSizePolicy(policy)
        while self.grid.count():
            self.grid.takeAt(0)  # убираем из сетки (сами виджеты остаются)
        for col, widgets in enumerate(columns):
            for row, w in enumerate(widgets):
                self.grid.addWidget(w, row, col)  # addWidget переносит виджет на новое место

    def params(self):
        return GasParams(self.gas_mode.value(), self.mass_a.value(), self.mass_b.value(),
                         self.n_total.value(), self.n_b.value())

    def sync_with(self, exp):
        """Показать настройки смеси и доступные пары по текущему составу газа."""
        for w in self.mix_widgets:
            w.setVisible(exp.gas_mode == GAS_MIX)
        self.pair.set_enabled_options(exp.available_pair_types())
        self.pair.set_value(exp.pair_type)
