"""
Страница "Презентация". Собирает части и связывает их с экспериментом:

    сверху — две строки параметров;
    слева — сосуд, построение векторов и управление расчётом;
    справа — две независимые панели графиков;
    снизу — память, число столбиков и сравнение с теорией.
"""

import time

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

FAST_BUDGET = settings.FAST_BUDGET     # секунд расчёта в одной порции кадра
VECTOR_RADIUS = settings.VECTOR_RADIUS     # радиус векторной диаграммы в единицах наибольшей sqrt(kT/m)
CLICK_DISTANCE = settings.CLICK_DISTANCE    # на каком расстоянии (нм) от молекулы щелчок её выбирает
MIDDLE_MIN = settings.MIDDLE_MIN         # наименьшая ширина средней колонки (в базовых шрифтах)
# Ограничение интерфейса: при добавлении третьей панели также согласовать названия и надпись «2 / 2».
MAX_PANELS = 2
# Здесь выбрать величину второго графика при добавлении, например (SINGLE, tf.ENERGY).
SECOND_PANEL = (SINGLE, tf.MODULUS)  # второй график сначала показывает |v₁| — для сравнения с |v_отн|


# Сборщик экрана опыта: компоненты создаются здесь, а сами графики рисуются в ui/plots/.
class DemoPage(QtWidgets.QWidget):
    # Для изменения состава экрана править блоки ниже; текст кнопок задаётся при создании или в setText().
    def __init__(self, go_home, go_theory, go_authors=None):
        super().__init__()
        self.exp = Experiment()
        self._last_plot_refresh = 0.
        self._last_stats_refresh = float("-inf")
        self._frame_remaining = None
        self._frame_timer = QtCore.QTimer(self)
        self._frame_timer.setSingleShot(True)
        self._frame_timer.timeout.connect(self._continue_frame)
        # Геометрия дочерних блоков окончательно меняется после resize окна.
        # Объединяем события и подгоняем сосуд уже по готовой компоновке.
        self._box_fit_timer = QtCore.QTimer(self)
        self._box_fit_timer.setSingleShot(True)
        self._box_fit_timer.timeout.connect(self._fit_box)
        self.projection_of = None

        # --- части страницы ---
        self.box = BoxView()
        self.run = RunControls()
        self.vectors = VectorView()
        # Размер легенды задаётся здесь (.85); settings.LEGEND_FONT текущим экраном не используется.
        self.legend = label(size=.85, wrap=True)
        self.box.attach_vectors(self.vectors, self.legend)
        self.gas = GasPanel(self.exp)
        # Названия нижних полей и их всплывающие пояснения менять в этом блоке.
        self.bins = ParamControl("Столбиков", *BINS_RANGE, self.exp.bins, show_slider=False)
        self.bins.setToolTip("Число столбиков в гистограммах; накопленная статистика сохраняется")
        self.memory = ParamControl("Память", *MEMORY_RANGE, self.exp.memory_collisions, show_slider=False)
        # Шаг стрелок числового поля памяти; это не значение памяти по умолчанию.
        self.memory.spin.setSingleStep(50)
        self.memory.setToolTip(
            "Память в столкновениях: вес старых измерений уменьшается как exp(−t/τ).\n"
            "График хранит последние 3τ (около 95% статистического веса).\n"
            "Увеличение памяти не восстанавливает уже удалённую историю.")
        self.panels = []
        self.panels_box = vbox(spacing=style.px(0.5))
        # Первоначальная надпись кнопки; окончательный текст также назначается в configure_plots().
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
        self.ratio.setFixedHeight(self.ratio.fontMetrics().lineSpacing() + style.px(0.3))

        # Две верхние строки: газ и начальные условия.
        # Порядок элементов второго верхнего ряда и текст «Начальные скорости:» задаются здесь.
        self.conditions = card(hbox(
            self.gas.pair_group, label("Начальные скорости:"), self.gas.start,
            self.gas.collisions, self.run.ensemble_box, None, spacing=style.px(.6),
        ))
        self.conditions.setFont(style.font(.9))
        self.gas_card = card(self.gas)

        # Сосуд и построение векторов находятся в одной системе экранных длин.
        # Флажок скрывает дополнительное построение и легенду, но не стрелки возле выбранных частиц.
        self.vector_toggle = QtWidgets.QCheckBox("Построение векторов")
        self.vector_toggle.setChecked(True)
        self.vector_toggle.toggled.connect(self.vectors.setVisible)
        self.vector_toggle.toggled.connect(self.legend.setVisible)
        self.vector_toggle.toggled.connect(self.on_display_options_changed)
        self.box_card = card(self.box)
        self.box_card.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Ignored)
        self.run_card = card(self.run, self.vector_toggle)
        self.run_card.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.left = QtWidgets.QWidget()
        self.left.setLayout(vbox((self.box_card, 1), self.run_card, spacing=style.px(.5)))

        # Связанные шкалы меняют только представление графиков, а не параметры физического опыта.
        self.link_scales = button("Связать шкалы", checkable=True)
        self.link_scales.setChecked(True)
        self.link_scales.setToolTip(
            "Включено: одинаковые шкалы сравнимых величин.\n"
            "Выключено: каждая панель подбирает свой диапазон.")
        # Меню остаётся доступно и в режиме «только графики».
        self.display_button = QtWidgets.QToolButton()
        self.display_button.setText("Вид")
        self.display_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(self.display_button)
        self.instant_action = menu.addAction("Мгновенные значения")
        self.instant_action.setCheckable(True)
        self.instant_action.setChecked(settings.SHOW_INSTANT_VALUES)
        self.projection_action = menu.addAction("Проекция на ось x")
        self.projection_action.setCheckable(True)
        self.projection_action.setChecked(settings.SHOW_VECTOR_PROJECTION)
        self.display_button.setMenu(menu)
        self.display_button.setToolTip("Показать мгновенные числа и фиолетовую проекцию вектора")
        for action in (self.instant_action, self.projection_action):
            action.toggled.connect(self.on_display_options_changed)
        self.history_caption = label(size=.85, shrinkable=True)
        self.middle = card(
            hbox(self.link_scales, self.display_button, (self.history_caption, 1), self.zoom_button,
                 spacing=style.px(.5)),
            (self.panels_box, 1), spacing=style.px(.4),
        )
        self.body = QtWidgets.QWidget()
        # Основное расположение: hbox — в строку, vbox — в столбец; spacing задаёт промежутки.
        self.body.setLayout(hbox(self.left, (self.middle, 1), spacing=style.px(.6)))
        self.body.installEventFilter(self)
        self.run_card.installEventFilter(self)
        self.footer = card(hbox(
            self.bins, self.memory, (self.ratio, 1), self.add_button, spacing=style.px(.7),
        ))
        # Тексты навигации и заголовка страницы править здесь; «На главную» задано в ui/widgets.header_bar().
        extra = [("Теория", self._leaving(go_theory))]
        if go_authors is not None:
            extra.append(("Авторы", self._leaving(go_authors)))
        self.header = header_bar("Скорости молекул", self._leaving(go_home), extra)
        self.header.setObjectName("experimentHeader")
        margin = style.px(.5)
        self.setLayout(vbox(
            self.header, self.gas_card, self.conditions, (self.body, 1), self.footer,
            spacing=style.px(.4), margins=(margin, 0, margin, margin),
        ))
        self.run.btn_start.setObjectName("primary")
        self.link_scales.clicked.connect(self.on_experiment_changed)

        # --- связи ---
        # Связи действий с обработчиками: для изменения поведения кнопки искать соответствующий метод ниже.
        self.run.state_changed.connect(self.on_run_state_changed)
        self.run.started.connect(self.on_start)
        self.run.tick.connect(self.on_tick)
        self.run.speed.changed.connect(lambda _: self._cancel_frame())
        self.run.mode_changed.connect(self.on_mode_changed)
        self.run.ensemble_changed.connect(self.on_ensemble_changed)
        self.box.clicked.connect(self.on_box_clicked)
        self.gas.gas_changed.connect(self.on_gas_changed)
        self.gas.pair_chosen.connect(lambda key: self._changed(self.exp.choose_pair, key))
        self.gas.temperature_changed.connect(lambda t: self._changed(self.exp.set_temperature, t))
        self.bins.changed.connect(lambda n: self._changed(self.exp.set_bins, n))
        self.memory.changed.connect(lambda value: self._changed(self.exp.set_memory, value))

        self.exp.ensemble = self.run.ensemble_box.isChecked()
        # Здесь выбирается первая величина; число стартовых панелей регулирует START_TWO_PANELS.
        self.add_panel(PAIR, tf.MODULUS)
        if settings.START_TWO_PANELS:
            self.add_next_panel()
        self._autostarted = False

    # Автоматический запуск только при первом открытии; выключается настройкой AUTOSTART.
    def showEvent(self, event):
        super().showEvent(event)
        if settings.AUTOSTART and not self._autostarted and self.run.state == "stopped":
            self._autostarted = True
            self.run.start()

    # ------------------------------------------------------------------
    # Компоновка
    # ------------------------------------------------------------------
    # Пересчитать место для сосуда после изменения размеров окна.
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._box_fit_timer.start(0)

    def eventFilter(self, watched, event):
        # При F11 область опыта может изменить размер уже после resizeEvent
        # страницы. Без этой проверки остаётся ограничение от переходного кадра.
        if event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.LayoutRequest, QtCore.QEvent.Show):
            self._box_fit_timer.start(0)
        return super().eventFilter(watched, event)

    # Обновить размеры кнопок и подписей при смене масштаба шрифта.
    def rescale_layout(self):
        self.ratio.setFixedHeight(self.ratio.fontMetrics().lineSpacing() + style.px(.3))
        side = self.add_button.sizeHint().height()
        self.zoom_button.setFixedSize(side, side)
        self.zoom_button.setIcon(zoom_icon(side))
        self.zoom_button.setIconSize(QtCore.QSize(int(side * .6), int(side * .6)))
        self._box_fit_timer.start(0)
        self.box.place_vectors()

    # Отдельный от F11 режим: отдать ширину страницы графикам, сохранив текущий опыт.
    def toggle_graphs_zoom(self):
        """Графики на всю ширину: сосуд и колонка настроек скрываются (расчёт продолжается)."""
        zoomed = self.zoom_button.isChecked()
        self.left.setVisible(not zoomed)
        self.gas_card.setVisible(not zoomed)
        self.conditions.setVisible(not zoomed)
        self._box_fit_timer.start(0)
        self.zoom_button.setToolTip("Вернуть сосуд и настройки" if zoomed
                                    else "Графики на весь экран (сосуд и настройки скрываются)")

    # Для изменения доли сосуда на экране смотреть free_height, room и ограничитель .43 ниже.
    def _fit_box(self):
        """Сосуд квадратный: ширина левой колонки = высота места под сосудом,
        но не меньше, чем нужно кнопкам, и так, чтобы графикам осталось MIDDLE_MIN."""
        if not hasattr(self, "body") or self.left.isHidden():
            return
        gap = self.left.layout().spacing()
        free_height = self.body.height() - self.run_card.sizeHint().height() - gap
        room = self.body.width() - max(style.px(MIDDLE_MIN), self.middle.minimumSizeHint().width()) - gap
        width = max(self.run_card.minimumSizeHint().width(),
                    min(free_height, room, int(self.body.width() * .43)))
        if self.left.width() != width:
            self.left.setFixedWidth(width)
        height = max(1, min(width, free_height))
        if self.box_card.maximumHeight() != height:
            self.box_card.setMaximumHeight(height)

    # Оборачивает переход на другую страницу так, чтобы опыт не продолжался скрытым.
    def _leaving(self, go):
        """Переход на другую страницу ставит расчёт на паузу."""
        # Сначала остановить анимацию, затем вызвать переданную функцию перехода.
        def handler():
            self.run.pause()
            go()
        return handler

    # Общий вход для паузы при переходах из главного окна.
    def pause(self):
        self.run.pause()

    # ------------------------------------------------------------------
    # Панели графиков
    # ------------------------------------------------------------------
    # Добавить панель с величиной SECOND_PANEL, заданной в начале файла.
    def add_next_panel(self):
        self.add_panel(*SECOND_PANEL)

    # Создать панель GraphPanel и подключить смену величины и закрытие к этой странице.
    def add_panel(self, obj, kind):
        if len(self.panels) >= MAX_PANELS:
            return
        panel = GraphPanel(obj, kind, closable=bool(self.panels))
        panel.show_instant_value(self.instant_action.isChecked(), self.exp)
        panel.quantity_changed.connect(self.on_experiment_changed)
        panel.close_clicked.connect(lambda: self.remove_panel(panel))
        self.panels.append(panel)
        self.panels_box.addWidget(panel, 1)
        self.on_experiment_changed()

    # Убрать панель из списка и компоновки, затем пересогласовать шкалы оставшихся графиков.
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
    # Новый Старт создаёт новый газ; для продолжения старого опыта используется Пауза/Продолжить.
    def on_start(self):
        self.exp.rebuild()  # новый опыт: газ заново, статистика с нуля
        self.on_experiment_changed()

    # Выбрать длительность кадра по темпу показа; температура уже учтена методом frame_duration().
    def on_tick(self, fast, factor):
        if self._frame_remaining is None:
            factor = settings.FAST_FRAME_FACTOR if fast else factor
            self._frame_remaining = self.exp.frame_duration(factor)
        self._continue_frame()

    # Досчитать кадр короткими порциями; не менять ради редактирования надписей или размеров.
    def _continue_frame(self):
        if self._frame_remaining is None:
            return
        self._frame_timer.stop()
        self._frame_remaining = self.exp.advance_duration(self._frame_remaining, seconds=FAST_BUDGET)
        if self._frame_remaining > 0 and self.run.state == "running":
            # Между порциями Qt обрабатывает паузу, ползунки и закрытие окна.
            self._frame_timer.start(1)
            return
        self._frame_remaining = None
        due = time.perf_counter() - self._last_plot_refresh >= settings.PLOT_REFRESH_MS / 1000.
        self.refresh(plots=due or self.run.state != "running",
                     force_stats=self.run.state != "running")
        self.run.finish_frame()

    # Снять отложенное продолжение старого кадра перед сменой параметров или остановкой.
    def _cancel_frame(self):
        pending = self._frame_remaining is not None
        self._frame_timer.stop()
        self._frame_remaining = None
        if pending:
            self.run.finish_frame()

    # При паузе/остановке сразу показать последнее рассчитанное состояние и полные подписи.
    def on_run_state_changed(self, state):
        if state != "running":
            self._cancel_frame()
            self.refresh()  # на паузе показываем последний фактически рассчитанный шаг

    # Скрытие страницы через любой переход также ставит расчёт на паузу.
    def hideEvent(self, event):
        self.run.pause()
        super().hideEvent(event)

    # При смене темпа очистить только историю времени; накопленные гистограммы остаются.
    def on_mode_changed(self, fast):
        self.exp.ensemble = self.run.ensemble_box.isChecked()
        self.exp.restart_history()
        self.on_experiment_changed()

    # Переключить способ набора статистики и обновить текущие подписи.
    def on_ensemble_changed(self, enabled):
        self.exp.ensemble = enabled
        self.refresh()

    # Применить значения GasPanel; начальное движение «Все одинаковые» имеет свои память и темп.
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

    # Щелчок выбирает молекулу в пределах CLICK_DISTANCE; which различает левую и правую кнопки.
    def on_box_clicked(self, x, y, which):
        k = self.exp.gas.nearest(x, y, max_dist=CLICK_DISTANCE)
        if k is not None:
            self._changed(self.exp.select, k, which)

    # Общий путь для смены температуры, пары, памяти и столбиков с последующим обновлением экрана.
    def _changed(self, action, *args):
        """Выполнить действие над экспериментом и перестроить графики."""
        action(*args)
        self.on_experiment_changed()

    # После изменения опыта синхронизировать поля, заново задать шкалы и перерисовать экран.
    def on_experiment_changed(self):
        """Изменились газ, выбор молекул или графики: заново настроить масштабы и подписи."""
        self._cancel_frame()
        self.gas.sync_with(self.exp)
        self.configure_plots()
        self.refresh()

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------
    # Найти показанные пары графиков для нижней строки сравнения с относительной скоростью.
    def _comparisons(self):
        """Пары графиков "молекула — относительная скорость" одного вида (только скорости)."""
        shown = [p.quantity for p in self.panels]
        return [(obj, kind) for obj, kind in shown
                if obj != PAIR and kind != tf.ENERGY and (PAIR, kind) in shown]

    # Настройка шкал и легенды; здесь также обновляются доступность и текст кнопки добавления.
    def configure_plots(self):
        exp = self.exp
        for panel in self.panels:
            obj, kind = panel.quantity
            # Графики одного вида — в общем масштабе, чтобы разницу (например, в √2) было видно на глаз.
            scales = ([exp.scale(p.quantity[0], kind) for p in self.panels if p.quantity[1] == kind]
                      if self.link_scales.isChecked() else [exp.scale(obj, kind)])
            low, high = tf.value_range(kind, max(scales))
            panel.configure(exp, low, high, max(tf.peak(kind, s) for s in scales))

        # Сохраняем масштаб стрелок при 300 К: нагрев увеличивает их длину.
        speed_scale = exp.max_speed_scale() * (settings.ANIMATION_REFERENCE_TEMPERATURE / exp.temperature) ** .5
        self.box.configure(exp.gas.box, speed_scale)
        self.vectors.set_radius(VECTOR_RADIUS * speed_scale)
        self.configure_projection()
        self.add_button.setEnabled(len(self.panels) < MAX_PANELS)
        # Для переименования кнопки менять и этот динамический шаблон, иначе надпись будет перезаписана.
        self.add_button.setText("+ График" if len(self.panels) < MAX_PANELS else "Графики: 2 / 2")
        if not self._comparisons():
            self.ratio.setText("")

    def configure_projection(self):
        """Флажок влияет только на рисунок; графики проекции всегда доступны."""
        selected = next((p.quantity[0] for p in self.panels if p.quantity[1] == tf.PROJECTION), None)
        available = selected is not None and self.vector_toggle.isChecked()
        self.projection_action.setEnabled(available)
        self.projection_action.setToolTip(
            "Проекция величины из первого графика проекции" if available else
            "Выберите v₁,x, v₂,x или vотн,x в графике и включите построение векторов")
        self.projection_of = selected if available and self.projection_action.isChecked() else None
        self.legend.setText(vector_legend(self.projection_of))

    def on_display_options_changed(self):
        """Только оформление: не отменяет кадр, не сбрасывает историю/гистограммы."""
        for panel in self.panels:
            panel.show_instant_value(self.instant_action.isChecked(), self.exp)
        self.configure_projection()
        self.refresh(plots=False)

    # Показать текущие данные; plots=False обновляет только сосуд и векторы для более частой анимации.
    def refresh(self, plots=True, force_stats=True):
        exp = self.exp
        self.box.update_view(exp, PAIR)
        self.vectors.match_pixel_scale(self.box.vector_pixel_scale())
        self.vectors.update_view(exp, self.projection_of)
        if not plots:
            return
        self._last_plot_refresh = time.perf_counter()
        # Здесь редактируется обновляемая надпись «История: до … пс», сохраняя подстановку числа.
        self.history_caption.setText("История: до %s пс" % style.fmt(exp.history_window, 1))
        self.history_caption.setToolTip("Последние 3τ: окно пропорционально параметру «Память».")
        for panel in self.panels:
            panel.refresh(exp, self.run.fast)
        # Пауза и изменение параметров обновляют числа сразу; при движении — не чаще 500 мс.
        now = time.perf_counter()
        if force_stats or now - self._last_stats_refresh >= settings.STATS_REFRESH_MS / 1000.:
            self._last_stats_refresh = now
            for panel in self.panels:
                panel.refresh_stats(exp)
            comparisons = self._comparisons()
            self.ratio.setText(ratio_text(exp, *comparisons[0]) if comparisons else "")
