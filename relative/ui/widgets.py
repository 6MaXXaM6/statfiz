"""Общие элементы интерфейса: готовые подписи, кнопки, движки, переключатели."""
# Общие заготовки интерфейса: текст одной кнопки менять на странице, общий внешний вид — здесь или в ui/style.py.

from PyQt5 import QtCore, QtWidgets

import settings
from ui import style


# ----------------------------------------------------------------------
# Фабрики: одна строчка вместо пяти одинаковых настроек у каждого виджета
# ----------------------------------------------------------------------
# Текст конкретной надписи задаётся на странице при вызове label; здесь меняется общий вид надписей.
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


# Первый аргумент — видимый текст, on_click — действие; для переименования менять текст в месте вызова.
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


# Расположение в строку: порядок аргументов задаёт порядок блоков, spacing — расстояние между ними.
def hbox(*items, spacing=None, margins=(0, 0, 0, 0)):
    """Горизонтальный ряд. Элемент — виджет, layout или пара (элемент, растяжение)."""
    return _box(QtWidgets.QHBoxLayout(), items, spacing, margins)


# Расположение в столбец: порядок аргументов задаёт порядок сверху вниз.
def vbox(*items, spacing=None, margins=(0, 0, 0, 0)):
    """Вертикальный столбец (см. hbox)."""
    return _box(QtWidgets.QVBoxLayout(), items, spacing, margins)


# Общая сборка ряда/столбца; пара (элемент, число) задаёт долю свободного места.
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


# Отступ белой карточки регулируется CARD_MARGIN; фон и рамка — стилем QFrame#card в ui/style.py.
def card(*items, title=None, spacing=None):
    """Белая карточка со скруглёнными углами; внутри — элементы столбиком (как в vbox)."""
    frame = QtWidgets.QFrame()
    frame.setObjectName("card")
    head = [section_title(title)] if title else []
    m = style.px(settings.CARD_MARGIN)
    frame.setLayout(vbox(*(head + list(items)), spacing=spacing, margins=(m, m, m, m)))
    return frame


# Оформляет заголовок небольшого блока; общий цвет задаётся стилем QLabel#section.
def section_title(text):
    w = label(text, 1.0)
    w.setObjectName("section")
    return w


# Надпись и подсказка приходят от вызывающего виджета; здесь можно менять общий вид маленькой кнопки.
def overlay_button(parent, text, tooltip, on_click):
    """Маленькая кнопка поверх виджета (например, графика); место задаёт place_overlay()."""
    b = QtWidgets.QToolButton(parent)
    b.setObjectName("overlay")
    b.setText(text)
    b.setToolTip(tooltip)
    b.setFocusPolicy(QtCore.Qt.NoFocus)
    b.clicked.connect(on_click)
    return b


# Правый верхний угол кнопки: corner_margin меняет расстояние от края графика.
def place_overlay(b, parent, corner_margin=None):
    """Поставить кнопку в правый верхний угол parent (вызывать из resizeEvent)."""
    m = style.px(0.3) if corner_margin is None else corner_margin
    b.adjustSize()
    b.move(parent.width() - b.width() - m, m)
    b.raise_()


# Собирает цветной фрагмент подписи; используется, например, в легенде vотн = v1 − v2.
def html_color(text, color, bold=True):
    weight = "bold" if bold else "normal"
    return '<span style="color:%s; font-weight:%s">%s</span>' % (color, weight, text)


# Общая шапка страниц: текст «На главную» меняется здесь сразу для всех использующих её экранов.
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
# Служебное изменение поля без повторного вызова обработчиков; сохраняет согласованность элементов.
def _set_silently(widget, method, *args):
    """Вызвать метод виджета, не отправляя сигналов (чтобы не зациклить обновления)."""
    widget.blockSignals(True)
    getattr(widget, method)(*args)
    widget.blockSignals(False)


# Готовый параметр: подпись, числовое поле и ползунок; названия и пределы задаёт страница.
class ParamControl(QtWidgets.QWidget):
    """Параметр с "движком" и полем для точного ввода числа.

    Значение всегда остаётся в допустимом диапазоне [minimum, maximum].
    Сигнал changed отправляется с небольшой задержкой после последнего
    изменения, чтобы не перезапускать модель на каждом шаге движка.
    """

    changed = QtCore.pyqtSignal(int)

    # Для отдельного поля менять title/minimum/maximum/value в месте создания на странице.
    def __init__(self, title, minimum, maximum, value, show_number=True, show_slider=True):
        super().__init__()
        self.label = label(title)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setTracking(False)  # перестраивать опыт после отпускания движка
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
        self._delay.setInterval(40)
        self._delay.timeout.connect(lambda: self.changed.emit(self.value()))

        self.setLayout(vbox(hbox((self.label, 1), self.spin), self.slider,
                            spacing=0, margins=(0, style.px(0.1), 0, style.px(0.1))))

    # Читает подтверждённое число поля; именно его получает обработчик параметра.
    def value(self):
        return self.spin.value()

    # Одновременно меняет допустимые пределы и для числа, и для ползунка.
    def set_range(self, minimum, maximum):
        for w in (self.slider, self.spin):
            _set_silently(w, "setRange", minimum, maximum)

    # Показывает новое значение без запуска расчёта; удобно при синхронизации с моделью.
    def set_value_silently(self, value):
        for w in (self.slider, self.spin):
            _set_silently(w, "setValue", value)

    # Связывает движение ползунка и ввод числа; задержка объединяет частые изменения в одно.
    def _sync(self, other, value):
        _set_silently(other, "setValue", value)
        self._delay.start()


# Группа взаимоисключающих кнопок, например «Один газ / Смесь» или «Медленно / Быстро».
class Choice(QtWidgets.QWidget):
    """Подпись и ряд кнопок, из которых нажата ровно одна."""

    changed = QtCore.pyqtSignal(str)

    # В options менять видимый текст пары (ключ, текст); внутренние ключи используются обработчиками.
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

    # Возвращает внутренний ключ выбранного варианта, а не надпись кнопки.
    def value(self):
        for key, b in self.buttons.items():
            if b.isChecked():
                return key
        return None

    # Выделяет кнопку по ключу; сам по себе не имитирует пользовательское нажатие.
    def set_value(self, key):
        self.buttons[key].setChecked(True)

    # Отключает недоступные варианты, например пары B–B при недостаточном числе частиц B.
    def set_enabled_options(self, keys):
        for key, b in self.buttons.items():
            b.setEnabled(key in keys)
