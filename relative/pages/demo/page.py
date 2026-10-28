"""
Страница "Презентация". Собирает части и связывает их с экспериментом:

    слева    — сосуд с молекулами и кнопки хода расчёта;
    в центре — один или два графика (по умолчанию |v_отн| и |v₁|);
    справа   — параметры газа и векторная диаграмма скоростей.
"""

import settings

from PyQt5 import QtCore, QtWidgets

from model import theory as tf
from model.experiment import BINS_RANGE, MEMORY_RANGE, PAIR, SINGLE, Experiment
from pages.demo.gas_panel import GasPanel
from pages.demo.graph_panel import GraphPanel
from pages.demo.readouts import ratio_text, vector_legend
from pages.demo.run_controls import RunControls
from ui import style
from ui.icons import zoom_icon
from ui.plots.box_view import BoxView
from ui.plots.vector_view import VectorView
from ui.widgets import ParamControl, button, card, hbox, header_bar, label, vbox

FAST_BUDGET = settings.FAST_BUDGET     # быстрый режим: секунд расчёта на один кадр
VECTOR_RADIUS = settings.VECTOR_RADIUS     # радиус векторной диаграммы в единицах наибольшей sqrt(kT/m)
CLICK_DISTANCE = settings.CLICK_DISTANCE    # на каком расстоянии (нм) от молекулы щелчок её выбирает
MIDDLE_MIN = settings.MIDDLE_MIN         # наименьшая ширина средней колонки (в базовых шрифтах)
MAX_PANELS = 2
SECOND_PANEL = (SINGLE, tf.MODULUS)  # второй график сначала показывает |v₁| — для сравнения с |v_отн|


class DemoPage(QtWidgets.QWidget):
    def __init__(self, go_home, go_theory):
        super().__init__()
        self.exp = Experiment()
        self.projection_of = None

        # --- части страницы ---
        self.box = BoxView()
        self.run = RunControls()
        self.vectors = VectorView()
        self.legend = label(size=settings.LEGEND_FONT, center=True)
        self.gas = GasPanel(self.exp)
        self.bins = ParamControl("Столбиков", *BINS_RANGE, self.exp.bins, show_slider=False)
        self.bins.setToolTip("Число столбиков в гистограммах; накопленная статистика сохраняется")
        self.memory = ParamControl("Память", *MEMORY_RANGE, self.exp.memory_collisions, show_slider=False)
        self.memory.spin.setSingleStep(50)
        self.memory.setToolTip(
            "Сколько столкновений помнит статистика: старые отсчёты забываются как exp(−t/τ).\n"
            "Меньше — гистограмма быстрее перестраивается (например, после смены T), но шумнее.\n"
            "Больше — глаже, но дольше помнит старое. 300 — подобрано статистическим тестом.")
        self.panels = []
        self.panels_box = vbox(spacing=style.px(0.5))
        self.add_button = button("+  График", lambda: self.add_panel(*SECOND_PANEL))
        # Кнопка "графики на весь экран": квадратная, той же высоты, что "+ Добавить график"
        self.zoom_button = button("", self.toggle_graphs_zoom, checkable=True)
        side = self.add_button.sizeHint().height()
        self.zoom_button.setFixedSize(side, side)
        self.zoom_button.setIcon(zoom_icon(side))
        self.zoom_button.setIconSize(QtCore.QSize(int(side * 0.6), int(side * 0.6)))
        self.zoom_button.setToolTip("Графики на весь экран (сосуд и настройки скрываются)")
        self.ratio = label(size=settings.RATIO_FONT, shrinkable=True)
        # Высота строки сравнения постоянная (две строки), чтобы графики не прыгали, когда она появляется.
        self.ratio.setFixedHeight(2 * self.ratio.fontMetrics().lineSpacing() + style.px(0.3))

        # Слева: сосуд (квадратный, размер задаёт _fit_box) и кнопки хода расчёта
        self.box_card = card(self.box)
        self.box_card.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Ignored)
        self.run_card = card(self.run, self.gas.start, self.gas.collisions)
        self.run_card.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.left = QtWidgets.QWidget()
        self.left.setLayout(vbox((self.box_card, 1), self.run_card))

        # Справа: параметры газа и векторы (векторы сжимаются, если места мало)
        vectors_box = vbox(self.vectors, (self.legend, 1))
        vectors_box.setAlignment(self.vectors, QtCore.Qt.AlignHCenter)
        self.vectors_card = card(vectors_box, title="Скорости")
        self.vectors_card.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        self.right = QtWidgets.QWidget()
        self.right.setLayout(vbox(self.gas, self.vectors_card, None))
        # Ширину правой колонки считаем сразу — пока видны и настройки смеси,
        # чтобы при переключении "Один газ / Смесь" графики не сдвигались.
        self.right_width = self.right.sizeHint().width()
        self.right.setFixedWidth(self.right_width)

        # Под графиками: строка сравнения (√2), затем число столбиков, "+ график" и "на весь экран"
        middle = card((self.panels_box, 1), hbox((self.ratio, 1), self.add_button, spacing=style.px(0.4)),
                      hbox(self.bins, self.memory, None, self.zoom_button, spacing=style.px(0.6)),
                      spacing=style.px(0.3))
        self.middle = middle
        m = style.px(0.4)
        body = hbox(self.left, (middle, 1), self.right, spacing=m, margins=(m, 0, m, m))
        self.header = header_bar("Относительная скорость молекул идеального газа", self._leaving(go_home),
                                 [("Теория", self._leaving(go_theory))])
        self.setLayout(vbox(self.header, (body, 1), spacing=0))

        # --- связи ---
        self.run.started.connect(self.on_start)
        self.run.tick.connect(self.on_tick)
        self.run.mode_changed.connect(self.on_mode_changed)
        self.run.ensemble_changed.connect(self.on_ensemble_changed)
        self.box.clicked.connect(self.on_box_clicked)
        self.gas.gas_changed.connect(self.on_gas_changed)
        self.gas.pair_chosen.connect(lambda key: self._changed(self.exp.choose_pair, key))
        self.gas.temperature_changed.connect(lambda t: self._changed(self.exp.set_temperature, t))
        self.bins.changed.connect(lambda n: self._changed(self.exp.set_bins, n))
        self.memory.changed.connect(self.exp.set_memory)

        self.exp.ensemble = self.run.ensemble_box.isChecked()
        self.add_panel(PAIR, tf.MODULUS)
        if settings.START_TWO_PANELS:
            self.add_next_panel()
        self._autostarted = False

    def showEvent(self, event):
        super().showEvent(event)
        if settings.AUTOSTART and not self._autostarted and self.run.state == "stopped":
            self._autostarted = True
            self.run.start()

    # ------------------------------------------------------------------
    # Компоновка
    # ------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_box()

    def toggle_graphs_zoom(self):
        """Графики на всю ширину: сосуд и колонка настроек скрываются (расчёт продолжается)."""
        zoomed = self.zoom_button.isChecked()
        self.left.setVisible(not zoomed)
        self.right.setVisible(not zoomed)
        for panel in self.panels:
            panel.set_side_stats(zoomed)  # во всю ширину подписи — справа от графиков
        self.zoom_button.setToolTip("Вернуть сосуд и настройки" if zoomed
                                    else "Графики на весь экран (сосуд и настройки скрываются)")

    def _fit_box(self):
        """Сосуд квадратный: ширина левой колонки = высота места под сосудом,
        но не меньше, чем нужно кнопкам, и так, чтобы графикам осталось MIDDLE_MIN."""
        margins = self.box_card.layout().contentsMargins()
        spacing = self.left.layout().spacing()
        gap = style.px(0.4)
        # Высота — из высоты страницы, а не текущей высоты колонки (иначе сосуд не уменьшится).
        free_height = self.height() - self.header.height() - gap - self.run_card.sizeHint().height() - spacing
        side = free_height - (margins.top() + margins.bottom()) + margins.left() + margins.right()
        room = self.width() - self.right_width - max(style.px(settings.MIDDLE_MIN), self.middle.minimumSizeHint().width()) - 4 * gap
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
        self.add_panel(*SECOND_PANEL)

    def add_panel(self, obj, kind):
        if len(self.panels) >= MAX_PANELS:
            return
        panel = GraphPanel(obj, kind, closable=bool(self.panels))
        panel.set_side_stats(self.zoom_button.isChecked())
        panel.quantity_changed.connect(self.on_experiment_changed)
        panel.close_clicked.connect(lambda: self.remove_panel(panel))
        self.panels.append(panel)
        self.panels_box.addWidget(panel, 1)
        self.on_experiment_changed()

    def remove_panel(self, panel):
        self.panels.remove(panel)
        self.panels_box.removeWidget(panel)
        # Убираем с экрана сразу: deleteLater удалит виджет только на следующем цикле событий,
        # а до тех пор он висел бы поверх страницы на старом месте.
        panel.hide()
        panel.setParent(None)
        panel.deleteLater()
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
        self.exp.ensemble = self.run.ensemble_box.isChecked()
        self.exp.restart_history()
        self.on_experiment_changed()

    def on_ensemble_changed(self, enabled):
        self.exp.ensemble = enabled
        self.refresh()

    def on_gas_changed(self):
        params = self.gas.params()
        if params.start != self.exp.start:
            beam = params.start == "beam"
            memory = settings.RELAX_MEMORY if beam else settings.START_MEMORY
            self.memory.set_value_silently(memory)
            self.exp.set_memory(memory)
            self.run.speed.set_value_silently(settings.RELAX_SPEED if beam else settings.START_SPEED)
        self.exp.configure_gas(*params)
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
        """Пары графиков "молекула — относительная скорость" одного вида (только скорости)."""
        shown = [p.quantity for p in self.panels]
        return [(obj, kind) for obj, kind in shown
                if obj != PAIR and kind != tf.ENERGY and (PAIR, kind) in shown]

    def configure_plots(self):
        exp = self.exp
        for panel in self.panels:
            obj, kind = panel.quantity
            # Графики одного вида — в общем масштабе, чтобы разницу (например, в √2) было видно на глаз.
            scales = [exp.scale(p.quantity[0], kind) for p in self.panels if p.quantity[1] == kind]
            low, high = tf.value_range(kind, max(scales))
            panel.configure(exp, low, high, max(tf.peak(kind, s) for s in scales))

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
        comparisons = self._comparisons()
        if comparisons:
            self.ratio.setText(ratio_text(exp, *comparisons[0]))
