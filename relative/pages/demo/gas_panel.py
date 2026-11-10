"""Верхняя строка параметров газа. Настройки B видны только для смеси."""

import settings

from collections import namedtuple

from PyQt5 import QtCore, QtWidgets

from model.experiment import GAS_MIX, GAS_PURE
from ui import style
from ui.widgets import Choice, ParamControl, hbox, label

# Параметры газа, при изменении которых газ создаётся заново
GasParams = namedtuple("GasParams", "gas_mode mass_a mass_b n_total n_b start collisions")


# Верхние поля опыта; их подписи меняются здесь, стартовые значения и диапазоны — в settings.py.
class GasPanel(QtWidgets.QWidget):
    gas_changed = QtCore.pyqtSignal()
    pair_chosen = QtCore.pyqtSignal(str)
    temperature_changed = QtCore.pyqtSignal(int)

    # Создать поля, варианты выбора и подсказки; внутренние ключи Choice сохранять при переименовании.
    def __init__(self, exp):
        super().__init__()
        # В парах Choice второй элемент — текст кнопки, первый — ключ, используемый логикой программы.
        self.gas_mode = Choice(None, [(GAS_PURE, "Один газ"), (GAS_MIX, "Смесь A + B")])
        # ParamControl: подпись, минимум, максимум, значение. Температура и массы здесь — параметры презентации.
        self.temperature = ParamControl("T, у.е.", settings.TEMPERATURE_MIN, settings.TEMPERATURE_MAX, exp.temperature)
        self.n_total = ParamControl("Частиц N", settings.N_MIN, settings.N_MAX, exp.n_total)
        self.mass_a = ParamControl("mA, у.е.", settings.MASS_MIN, settings.MASS_MAX, exp.mass_a)
        self.mass_b = ParamControl("mB, у.е.", settings.MASS_MIN, settings.MASS_MAX, exp.mass_b)
        self.n_b = ParamControl("Частиц B", 1, exp.n_total - 1, exp.n_b_mix)
        self.n_b.setToolTip("1 — в газе A одна «чужая» молекула B")
        self.pair = Choice(None, [("AA", "A – A"), ("AB", "A – B"), ("BB", "B – B")])

        # Названия начальных условий и пояснение меняются здесь; maxwell/beam — служебные ключи.
        self.start = Choice(None, [("maxwell", "Максвелл"), ("beam", "Все одинаковые")])
        self.start.setToolTip("Все молекулы летят в одну сторону. Столкновения устанавливают распределение Максвелла.")
        self.collisions = QtWidgets.QCheckBox("Столкновения")
        self.collisions.setChecked(True)
        self.collisions.setFocusPolicy(QtCore.Qt.NoFocus)
        self.collisions.setToolTip("Без столкновений молекулы проходят сквозь друг друга и отражаются только от стенок.")
        self.start.changed.connect(lambda _: self.gas_changed.emit())
        self.collisions.toggled.connect(lambda _: self.gas_changed.emit())

        # Настройки смеси показываются только в режиме "Смесь"
        self.pair_group = QtWidgets.QWidget()
        self.pair_group.setLayout(hbox(label("Пара:"), self.pair, spacing=style.px(.3)))
        self.mix_widgets = (self.mass_b, self.n_b, self.pair_group)

        self.gas_mode.changed.connect(lambda _key: self.gas_changed.emit())
        for p in (self.mass_a, self.mass_b, self.n_total, self.n_b):
            p.changed.connect(lambda _value: self.gas_changed.emit())
        self.n_total.changed.connect(lambda n: self.n_b.set_range(1, max(1, n - 1)))
        self.pair.changed.connect(self.pair_chosen)
        self.temperature.changed.connect(self.temperature_changed)

        # Реальный шрифт верхней панели задаётся здесь; settings.GAS_PANEL_FONT сейчас не подключён.
        self.setFont(style.font(.95))
        self.setLayout(hbox(
            label("Газ:"), self.gas_mode, (self.temperature, 1), (self.n_total, 1),
            (self.mass_a, 1), (self.mass_b, 1), (self.n_b, 1),
            spacing=style.px(.6), margins=(0, 0, 0, 0),
        ))

    # Собрать выбранные настройки для DemoPage.on_gas_changed(); этот метод сам опыт не пересоздаёт.
    def params(self):
        return GasParams(self.gas_mode.value(), self.mass_a.value(), self.mass_b.value(),
                         self.n_total.value(), self.n_b.value(), self.start.value(), self.collisions.isChecked())

    # Согласовать видимость полей B и доступность AA/AB/BB с текущим составом газа.
    def sync_with(self, exp):
        """Показать настройки смеси и доступные пары по текущему составу газа."""
        for w in self.mix_widgets:
            w.setVisible(exp.gas_mode == GAS_MIX)
        self.pair.set_enabled_options(exp.available_pair_types())
        self.pair.set_value(exp.pair_type)
