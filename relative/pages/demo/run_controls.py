"""Кнопки Старт / Пауза / Стоп, режимы "медленно / быстро" и таймер кадров."""

import time

from PyQt5 import QtCore, QtWidgets

from ui import style
from ui.widgets import Choice, ParamControl, button, hbox, vbox
import settings

FRAME_MS = settings.FRAME_MS  # ~60 кадров в секунду
# После каждого кадра цикл событий хотя бы столько миллисекунд свободен. На Windows обычные
# таймеры Qt (например, задержка движков) срабатывают, только когда очередь событий пуста;
# без паузы при долгом кадре (быстрый режим) они не срабатывали бы никогда.
MIN_IDLE_MS = settings.MIN_IDLE_MS

# Медленный режим: сколько шагов dt моделируется за кадр при положениях движка 1..10
SLOW_FACTORS = settings.SLOW_FACTORS

STOPPED, RUNNING, PAUSED = "stopped", "running", "paused"


class RunControls(QtWidgets.QWidget):
    """Управляет ходом расчёта.

    started — нажата "Старт" (нужно начать новый опыт);
    mode_changed(fast) — переключён режим "медленно / быстро";
    tick(fast, factor) — пора сделать очередной кадр: в быстром режиме считать сколько
    успеем, в медленном — смоделировать factor шагов dt.
    """

    started = QtCore.pyqtSignal()
    tick = QtCore.pyqtSignal(bool, float)
    mode_changed = QtCore.pyqtSignal(bool)
    ensemble_changed = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.state = STOPPED
        self.timer = QtCore.QTimer(self)
        self.timer.setTimerType(QtCore.Qt.PreciseTimer)
        self.timer.setSingleShot(True)  # следующий кадр планируется после окончания текущего
        self.timer.timeout.connect(self._on_timer)

        self.btn_start = button("▶  Старт", self.start, size=settings.RUN_BUTTON_FONT, bold=True)
        self.btn_pause = button("❚❚  Пауза", self.toggle_pause, size=settings.RUN_BUTTON_FONT, bold=True)
        self.btn_stop = button("■  Стоп", self.stop, size=settings.RUN_BUTTON_FONT, bold=True)
        self.mode = Choice(None, [("slow", "Медленно"), ("fast", "Быстро")])
        self.mode.changed.connect(self._on_mode)
        self.speed = ParamControl("Скорость", 1, len(SLOW_FACTORS), settings.START_SPEED, show_number=False)

        self.ensemble_box = QtWidgets.QCheckBox("Статистика по всем молекулам")
        self.ensemble_box.setChecked(settings.START_ENSEMBLE)
        self.ensemble_box.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ensemble_box.setToolTip("Гистограммы по всем молекулам того же сорта; иначе — только по выбранной паре.")
        self.ensemble_box.toggled.connect(self.ensemble_changed)
        self.setLayout(vbox(
            hbox(self.btn_start, self.btn_pause, self.btn_stop),
            hbox((self.mode, 2), (self.speed, 3)), self.ensemble_box,
            spacing=style.px(0.2)))
        self._update_buttons()

    @property
    def fast(self):
        return self.mode.value() == "fast"

    def start(self):
        self.started.emit()
        self._set_state(RUNNING)

    def toggle_pause(self):
        if self.state == RUNNING:
            self._set_state(PAUSED)
        elif self.state == PAUSED:
            self._set_state(RUNNING)

    def pause(self):
        if self.state == RUNNING:
            self._set_state(PAUSED)

    def stop(self):
        self._set_state(STOPPED)

    def _set_state(self, state):
        self.state = state
        if state == RUNNING:
            self.timer.start(FRAME_MS)
        else:
            self.timer.stop()
        self._update_buttons()

    def _update_buttons(self):
        self.btn_start.setEnabled(self.state == STOPPED)
        self.btn_pause.setEnabled(self.state != STOPPED)
        self.btn_pause.setText("▶  Продолжить" if self.state == PAUSED else "❚❚  Пауза")
        self.btn_stop.setEnabled(self.state != STOPPED)
        self.speed.setEnabled(not self.fast)
        self.ensemble_box.setEnabled(not self.fast)

    def _on_mode(self, _key):
        if self.fast:
            self.ensemble_box.setChecked(True)
        self._update_buttons()
        self.mode_changed.emit(self.fast)

    def _on_timer(self):
        started = time.perf_counter()
        self.tick.emit(self.fast, SLOW_FACTORS[self.speed.value() - 1])
        if self.state == RUNNING:
            spent_ms = int((time.perf_counter() - started) * 1000)
            self.timer.start(max(MIN_IDLE_MS, FRAME_MS - spent_ms))
