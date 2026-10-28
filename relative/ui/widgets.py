"""Общие элементы интерфейса: готовые подписи, кнопки, движки, переключатели."""

from PyQt5 import QtCore, QtWidgets

import settings
from ui import style


# ----------------------------------------------------------------------
# Фабрики: одна строчка вместо пяти одинаковых настроек у каждого виджета
# ----------------------------------------------------------------------
def label(text="", size=None, bold=False, center=False, wrap=False, color=None, shrinkable=False):
    """Надпись. size — размер шрифта относительно базового (None — как у родителя)."""
    w = QtWidgets.QLabel(text)
    if size is not None:
        w.setFont(style.font(size, bold))
    if center:
        w.setAlignment(QtCore.Qt.AlignCenter)
    if wrap:
        w.setWordWrap(True)
    if color:
        w.setStyleSheet("color: %s;" % color)
    if shrinkable:
        # Длинная надпись может сжиматься и переноситься — окно не станет шире экрана.
        w.setWordWrap(True)
        w.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
    return w


def button(text, on_click=None, checkable=False, size=None, bold=False, name=None):
    """Кнопка, которая не перехватывает фокус клавиатуры (чтобы работали F11/Esc)."""
    b = QtWidgets.QPushButton(text)
    b.setFocusPolicy(QtCore.Qt.NoFocus)
    b.setCheckable(checkable)
    if size is not None:
        b.setFont(style.font(size, bold))
    if name:
        b.setObjectName(name)
    if on_click is not None:
        b.clicked.connect(on_click)
    return b


def hbox(*items, spacing=None, margins=(0, 0, 0, 0)):
    """Горизонтальный ряд. Элемент — виджет, layout или пара (элемент, растяжение)."""
    return _box(QtWidgets.QHBoxLayout(), items, spacing, margins)


def vbox(*items, spacing=None, margins=(0, 0, 0, 0)):
    """Вертикальный столбец (см. hbox)."""
    return _box(QtWidgets.QVBoxLayout(), items, spacing, margins)


def _box(layout, items, spacing, margins):
    layout.setContentsMargins(*margins)
    if spacing is not None:
        layout.setSpacing(spacing)
    for item in items:
        stretch = 0
        if isinstance(item, tuple):
            item, stretch = item
        if item is None:
            layout.addStretch(stretch or 1)
        elif isinstance(item, QtWidgets.QLayout):
            layout.addLayout(item, stretch)
        else:
            layout.addWidget(item, stretch)
    return layout


def card(*items, title=None, spacing=None):
    """Белая карточка со скруглёнными углами; внутри — элементы столбиком (как в vbox)."""
    frame = QtWidgets.QFrame()
    frame.setObjectName("card")
    head = [section_title(title)] if title else []
    m = style.px(settings.CARD_MARGIN)
    frame.setLayout(vbox(*(head + list(items)), spacing=spacing, margins=(m, m, m, m)))
    return frame


def section_title(text):
    w = label(text, 1.0)
    w.setObjectName("section")
    return w


def overlay_button(parent, text, tooltip, on_click):
    """Маленькая кнопка поверх виджета (например, графика); место задаёт place_overlay()."""
    b = QtWidgets.QToolButton(parent)
    b.setObjectName("overlay")
    b.setText(text)
    b.setToolTip(tooltip)
    b.setFocusPolicy(QtCore.Qt.NoFocus)
    b.clicked.connect(on_click)
    return b


def place_overlay(b, parent, corner_margin=None):
    """Поставить кнопку в правый верхний угол parent (вызывать из resizeEvent)."""
    m = style.px(0.3) if corner_margin is None else corner_margin
    b.adjustSize()
    b.move(parent.width() - b.width() - m, m)
    b.raise_()


def html_color(text, color, bold=True):
    weight = "bold" if bold else "normal"
    return '<span style="color:%s; font-weight:%s">%s</span>' % (color, weight, text)


def header_bar(title, back_callback, extra_buttons=()):
    """Верхняя полоса страницы: кнопка "На главную", заголовок, доп. кнопки."""
    bar = QtWidgets.QWidget()
    items = [button("◀  На главную", back_callback), (label(title, settings.HEADER_FONT, bold=True, center=True, shrinkable=True), 1)]
    items += [button(text, callback) for text, callback in extra_buttons]
    m = style.px(0.3)
    bar.setLayout(hbox(*items, margins=(m, style.px(0.2), m, style.px(0.2))))
    return bar


# ----------------------------------------------------------------------
# Составные элементы
# ----------------------------------------------------------------------
def _set_silently(widget, method, *args):
    """Вызвать метод виджета, не отправляя сигналов (чтобы не зациклить обновления)."""
    widget.blockSignals(True)
    getattr(widget, method)(*args)
    widget.blockSignals(False)


class ParamControl(QtWidgets.QWidget):
    """Параметр с "движком" и полем для точного ввода числа.

    Значение всегда остаётся в допустимом диапазоне [minimum, maximum].
    Сигнал changed отправляется с небольшой задержкой после последнего
    изменения, чтобы не перезапускать модель на каждом шаге движка.
    """

    changed = QtCore.pyqtSignal(int)

    def __init__(self, title, minimum, maximum, value, show_number=True, show_slider=True):
        super().__init__()
        self.label = label(title)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.spin = QtWidgets.QSpinBox()
        self.spin.setMinimumWidth(style.px(3.6))
        self.spin.setAlignment(QtCore.Qt.AlignRight)
        self.spin.setKeyboardTracking(False)  # число применяется после Enter
        self.spin.setVisible(show_number)
        self.slider.setVisible(show_slider)  # без движка — компактно: подпись и число в одну строку
        self.set_range(minimum, maximum)
        self.set_value_silently(value)

        self.slider.valueChanged.connect(lambda v: self._sync(self.spin, v))
        self.spin.valueChanged.connect(lambda v: self._sync(self.slider, v))

        self._delay = QtCore.QTimer(self)
        self._delay.setSingleShot(True)
        self._delay.setInterval(250)
        self._delay.timeout.connect(lambda: self.changed.emit(self.value()))

        self.setLayout(vbox(hbox((self.label, 1), self.spin), self.slider,
                            spacing=0, margins=(0, style.px(0.1), 0, style.px(0.1))))

    def value(self):
        return self.spin.value()

    def set_range(self, minimum, maximum):
        for w in (self.slider, self.spin):
            _set_silently(w, "setRange", minimum, maximum)

    def set_value_silently(self, value):
        for w in (self.slider, self.spin):
            _set_silently(w, "setValue", value)

    def _sync(self, other, value):
        _set_silently(other, "setValue", value)
        self._delay.start()


class Choice(QtWidgets.QWidget):
    """Подпись и ряд кнопок, из которых нажата ровно одна."""

    changed = QtCore.pyqtSignal(str)

    def __init__(self, title, options, tabs=False):
        """options — список пар (ключ, текст на кнопке); tabs=True — вид вкладок."""
        super().__init__()
        self.group = QtWidgets.QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        for key, text in options:
            b = button(text, lambda _checked, k=key: self.changed.emit(k), checkable=True)
            if tabs:
                b.setProperty("tab", True)
            self.group.addButton(b)
            self.buttons[key] = b
        row = hbox(*self.buttons.values(), spacing=0 if tabs else style.px(0.2))
        items = ([label(title)] if title else []) + [row]
        self.setLayout(vbox(*items, spacing=style.px(0.1), margins=(0, style.px(0.15), 0, style.px(0.15))))
        self.set_value(options[0][0])

    def value(self):
        for key, b in self.buttons.items():
            if b.isChecked():
                return key
        return None

    def set_value(self, key):
        self.buttons[key].setChecked(True)

    def set_enabled_options(self, keys):
        for key, b in self.buttons.items():
            b.setEnabled(key in keys)
