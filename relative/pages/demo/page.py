"""
Страница "Презентация". Собирает части и связывает их с экспериментом.

Пока графиков один-два:
    слева    — сосуд с молекулами и кнопки хода расчёта;
    в центре — панели графиков (по умолчанию |v_отн|; "+ Добавить график" — ещё одна);
    справа   — параметры газа и векторная диаграмма скоростей.
Когда графиков три-четыре, они встают сеткой 2×2, кнопки хода расчёта и параметры
газа переезжают в полосу внизу, а векторная диаграмма — под сосуд.
"""

from PyQt5 import QtCore, QtWidgets

from model import theory as tf
from model.experiment import PAIR, SECOND, SINGLE, Experiment
from pages.demo.gas_panel import GasPanel
from pages.demo.graph_panel import GraphPanel
from pages.demo.readouts import ratio_text, vector_legend
from pages.demo.run_controls import RunControls
from ui import style
from ui.plots.box_view import BoxView
from ui.plots.vector_view import VectorView
from ui.widgets import button, card, hbox, header_bar, label, vbox

FAST_BUDGET = 0.020     # быстрый режим: секунд расчёта на один кадр
VECTOR_RADIUS = 2.6     # радиус векторной диаграммы в единицах наибольшей sqrt(kT/m)
CLICK_DISTANCE = 4.0    # на каком расстоянии (нм) от молекулы щелчок её выбирает
MIDDLE_MIN = 24         # наименьшая ширина средней колонки (в базовых шрифтах)
MAX_PANELS = 4
WIDE_FROM = 3           # с этого числа графиков управление уезжает вниз
# В каком порядке предлагать величины для новых графиков
NEXT_QUANTITIES = [(PAIR, tf.MODULUS), (SINGLE, tf.MODULUS), (PAIR, tf.PROJECTION), (SINGLE, tf.PROJECTION),
                   (SECOND, tf.MODULUS), (SECOND, tf.PROJECTION)]


def pdf_peak(kind, sigma):
    """Максимум теоретической плотности: у модуля (Рэлей) — при v = σ, у проекции (Гаусс) — при 0."""
    return float(tf.pdf(kind, sigma if kind == tf.MODULUS else 0.0, sigma))


def replace_items(layout, items):
    """Положить в layout заново указанные виджеты: элемент — виджет или (виджет, растяжение)."""
    while layout.count():
        layout.takeAt(0)
    for item in items:
        widget, stretch = item if isinstance(item, tuple) else (item, 0)
        layout.addWidget(widget, stretch)


class DemoPage(QtWidgets.QWidget):
    def __init__(self, go_home, go_theory):
        super().__init__()
        self.exp = Experiment()
        self.projection_of = None
        self.wide = None
        self.right_width = None

        # --- части страницы ---
        self.box = BoxView()
        self.run = RunControls()
        self.vectors = VectorView()
        self.legend = label(size=1.1, center=True)
        self.gas = GasPanel(self.exp)
        self.panels = []
        self.panels_grid = QtWidgets.QGridLayout()
        self.panels_grid.setSpacing(style.px(0.5))
        self.add_button = button("+  Добавить график", self.add_next_panel)
        self.ratio = label(size=1.0, shrinkable=True)
        # Высота строки сравнения постоянная (две строки), чтобы графики не прыгали, когда она появляется.
        self.ratio.setFixedHeight(2 * self.ratio.fontMetrics().lineSpacing() + style.px(0.3))

        self.box_card = card(self.box)
        # Высоту сосуда задаёт _fit_box() как максимум; сам он не должен раздвигать страницу.
        self.box_card.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Ignored)
        self.run_card = card(self.run)
        # Диаграмма и подпись: друг под другом в колонке справа, рядом — в нижней полосе.
        self.vectors_box = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        self.vectors_box.addWidget(self.vectors, 0, QtCore.Qt.AlignHCenter)
        self.vectors_box.addWidget(self.legend, 1)
        self.vectors_card = card(self.vectors_box, title="Скорости")
        # Эти карточки не растягиваются по высоте — лишнее место остаётся внизу колонки;
        # карточка с векторами может и сжаться, если места не хватает.
        self.run_card.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.vectors_card.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        middle = card((self.panels_grid, 1), hbox((self.ratio, 1), self.add_button), spacing=style.px(0.3))

        # Колонки и нижняя полоса; что в них лежит, решает _arrange()
        self.left = QtWidgets.QWidget()
        self.left.setLayout(vbox())
        self.right = QtWidgets.QWidget()
        self.right.setLayout(vbox())
        self.bottom = QtWidgets.QWidget()
        self.bottom.setLayout(hbox(spacing=style.px(0.4)))
        m = style.px(0.4)
        body = vbox((hbox(self.left, (middle, 1), self.right, spacing=m), 1), self.bottom,
                    spacing=m, margins=(m, 0, m, m))
        self.header = header_bar("Относительная скорость молекул идеального газа", self._leaving(go_home),
                                 [("Теория", self._leaving(go_theory))])
        self.setLayout(vbox(self.header, (body, 1), spacing=0))

        # --- связи ---
        self.run.started.connect(self.on_start)
        self.run.tick.connect(self.on_tick)
        self.run.mode_changed.connect(self.on_mode_changed)
        self.box.clicked.connect(self.on_box_clicked)
        self.gas.gas_changed.connect(self.on_gas_changed)
        self.gas.pair_chosen.connect(lambda key: self._changed(self.exp.choose_pair, key))
        self.gas.temperature_changed.connect(lambda t: self._changed(self.exp.set_temperature, t))

        self.add_panel(PAIR, tf.MODULUS)

    # ------------------------------------------------------------------
    # Компоновка
    # ------------------------------------------------------------------
    def _arrange(self):
        """Разложить части страницы в зависимости от числа графиков."""
        wide = len(self.panels) >= WIDE_FROM
        if wide != self.wide:
            self.wide = wide
            if wide:
                replace_items(self.left.layout(), [(self.box_card, 1), self.vectors_card])
                replace_items(self.bottom.layout(), [self.run_card, (self.gas, 1)])
                self.vectors.set_sizes(6, 4)
                self.vectors_box.setDirection(QtWidgets.QBoxLayout.LeftToRight)
            else:
                replace_items(self.left.layout(), [(self.box_card, 1), self.run_card])
                self.left.layout().addStretch(0)
                replace_items(self.right.layout(), [self.gas, self.vectors_card])
                self.vectors.set_sizes(10, 4)
                self.right.layout().addStretch(1)
                self.vectors_box.setDirection(QtWidgets.QBoxLayout.TopToBottom)
            self.gas.set_horizontal(wide)
            self.right.setVisible(not wide)
            self.bottom.setVisible(wide)
            if not wide:
                # Ширину правой колонки считаем один раз — пока видны и настройки смеси,
                # чтобы при переключении "Один газ / Смесь" графики не сдвигались.
                if self.right_width is None:
                    self.right_width = self.right.sizeHint().width()
                self.right.setFixedWidth(self.right_width)

        # Графики: один-два — друг под другом, три-четыре — сеткой 2×2.
        while self.panels_grid.count():
            self.panels_grid.takeAt(0)
        for n, panel in enumerate(self.panels):
            row, col = (n, 0) if not wide else divmod(n, 2)
            self.panels_grid.addWidget(panel, row, col)
        self._fit_box()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_box()

    def _fit_box(self):
        """Сосуд квадратный: ширина левой колонки = высота места под сосудом,
        но не меньше, чем нужно кнопкам, и так, чтобы графикам осталось MIDDLE_MIN."""
        margins = self.box_card.layout().contentsMargins()
        spacing = self.left.layout().spacing()
        gap = style.px(0.4)
        # Высота верхнего ряда — из высоты страницы (а не текущей высоты колонки,
        # иначе сосуд не уменьшится, когда появится нижняя полоса).
        free_height = self.height() - self.header.height() - gap
        if self.wide:
            free_height -= self.bottom.sizeHint().height() + gap + self.vectors_card.sizeHint().height() + spacing
        else:
            free_height -= self.run_card.sizeHint().height() + spacing
        side = free_height - (margins.top() + margins.bottom()) + margins.left() + margins.right()
        right = 0 if self.wide else self.right_width
        room = self.width() - right - style.px(MIDDLE_MIN) - 4 * style.px(0.4)
        width = max(min(side, room), self.run_card.minimumSizeHint().width())
        height = min(width, free_height)
        # Меняем размеры только если они другие — иначе Qt будет бесконечно перекладывать виджеты.
        if self.left.width() != width:
            self.left.setFixedWidth(width)
        if self.box_card.maximumHeight() != height:
            self.box_card.setMaximumHeight(max(height, 1))

    def _leaving(self, go):
        """Переход на другую страницу ставит расчёт на паузу."""
        def handler():
            self.run.pause()
            go()
        return handler

    def pause(self):
        self.run.pause()

    # ------------------------------------------------------------------
    # Панели графиков
    # ------------------------------------------------------------------
    def add_next_panel(self):
        """Новый график с первой величиной из NEXT_QUANTITIES, которой ещё нет на экране."""
        shown = [p.quantity for p in self.panels]
        self.add_panel(*next((q for q in NEXT_QUANTITIES if q not in shown), NEXT_QUANTITIES[0]))

    def add_panel(self, obj, kind):
        if len(self.panels) >= MAX_PANELS:
            return
        panel = GraphPanel(obj, kind, closable=bool(self.panels))
        panel.quantity_changed.connect(self.on_experiment_changed)
        panel.close_clicked.connect(lambda: self.remove_panel(panel))
        self.panels.append(panel)
        self._arrange()
        self.on_experiment_changed()

    def remove_panel(self, panel):
        self.panels.remove(panel)
        self.panels_grid.removeWidget(panel)
        # Убираем с экрана сразу: deleteLater удалит виджет только на следующем цикле событий,
        # а до тех пор он висел бы поверх страницы на старом месте.
        panel.hide()
        panel.setParent(None)
        panel.deleteLater()
        self._arrange()
        self.on_experiment_changed()

    # ------------------------------------------------------------------
    # События
    # ------------------------------------------------------------------
    def on_start(self):
        self.exp.rebuild()  # новый опыт: газ заново, статистика с нуля
        self.on_experiment_changed()

    def on_tick(self, fast, factor):
        if fast:
            self.exp.advance_for_seconds(FAST_BUDGET)
        else:
            self.exp.advance_by(factor)
        self.refresh()

    def on_mode_changed(self, fast):
        # Быстрый режим — для набора статистики: считаем её сразу по всем молекулам.
        self.exp.ensemble = fast
        self.refresh()

    def on_gas_changed(self):
        self.exp.configure_gas(*self.gas.params())
        self.on_experiment_changed()

    def on_box_clicked(self, x, y, which):
        k = self.exp.gas.nearest(x, y, max_dist=CLICK_DISTANCE)
        if k is not None:
            self._changed(self.exp.select, k, which)

    def _changed(self, action, *args):
        """Выполнить действие над экспериментом и перестроить графики."""
        action(*args)
        self.on_experiment_changed()

    def on_experiment_changed(self):
        """Изменились газ, выбор молекул или графики: заново настроить масштабы и подписи."""
        self.gas.sync_with(self.exp)
        self.configure_plots()
        self.refresh()

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------
    def _comparisons(self):
        """Пары графиков "молекула — относительная скорость" одного вида: [(молекула, вид), ...]."""
        shown = [p.quantity for p in self.panels]
        return [(obj, kind) for obj, kind in shown if obj != PAIR and (PAIR, kind) in shown]

    def configure_plots(self):
        exp = self.exp
        for panel in self.panels:
            obj, kind = panel.quantity
            # Графики одного вида (все модули или все проекции) — в общем масштабе,
            # чтобы разницу в √2 было видно на глаз.
            sigmas = [exp.sigma(p.quantity[0]) for p in self.panels if p.quantity[1] == kind]
            low, high = tf.value_range(kind, max(sigmas))
            panel.configure(exp, low, high, max(pdf_peak(kind, s) for s in sigmas))

        speed_scale = exp.max_speed_scale()
        self.box.configure(exp.gas.box, speed_scale)
        self.vectors.set_radius(VECTOR_RADIUS * speed_scale)
        self.projection_of = next((p.quantity[0] for p in self.panels if p.quantity[1] == tf.PROJECTION), None)
        self.legend.setText(vector_legend(self.projection_of))
        self.add_button.setVisible(len(self.panels) < MAX_PANELS)
        if not self._comparisons():
            self.ratio.setText("")

    def refresh(self):
        exp = self.exp
        self.box.update_view(exp, PAIR)
        self.vectors.update_view(exp, self.projection_of)
        for panel in self.panels:
            panel.refresh(exp, self.run.fast)
        comparisons = self._comparisons()[:2]  # не больше двух строк
        if comparisons:
            self.ratio.setText("<br>".join(ratio_text(exp, obj, kind) for obj, kind in comparisons))
