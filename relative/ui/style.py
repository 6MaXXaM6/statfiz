"""
Общий стиль: размеры шрифтов и линий зависят от разрешения экрана,
чтобы презентация одинаково читалась на ноутбуке и на проекторе.
"""
# Для изменения всей программы начинать с settings.py; правила ниже нужны для отдельных типов элементов.

import os

import settings
import sys

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

# Базовый размер шрифта в пикселях. Пересчитывается в init_style().
BASE = 20

# Цвета (яркие и контрастные — для проектора)
MOL1 = settings.COLOR_MOL1       # молекула 1 и её скорость — красный
MOL2 = settings.COLOR_MOL2       # молекула 2 и её скорость — синий
REL = settings.COLOR_REL        # относительная скорость — чёрный
GAS_A = settings.COLOR_GAS_A      # молекулы газа A — серо-синий
GAS_B = settings.COLOR_GAS_B      # молекулы газа B — зелёный
THEORY = settings.COLOR_THEORY     # теоретическая кривая
HILITE = settings.COLOR_HILITE     # подсветка текущего значения — оранжевый
BAR = settings.COLOR_BAR        # столбики гистограммы
BAR_EDGE = settings.COLOR_BAR_EDGE   # края столбиков — светлее, чтобы узкие столбики не сливались в полосы
PROJ = settings.COLOR_PROJ       # проекция — фиолетовый
PAGE_BG = settings.COLOR_PAGE    # фон страниц (карточки на нём — белые)


# Имена картинок/HTML передаются страницами; функция находит их и рядом с исходниками, и внутри сборки.
def resource_path(*parts):
    """Путь к файлу из папки assets — работает и из исходников, и из собранного exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "assets", *parts)


# Все размеры через px масштабируются вместе с окном; k — коэффициент относительно базового шрифта.
def px(k=1.0):
    """Размер в пикселях, пропорциональный базовому шрифту."""
    return max(1, int(round(BASE * k)))


# Шрифт для отдельной надписи: k меняет размер, bold — жирность.
def font(k=1.0, bold=False):
    f = QtGui.QFont()
    f.setPixelSize(px(k))
    f.setBold(bold)
    return f


# Здесь меняются общие цвета полей, списков и подсказок, включая отключённые элементы.
def light_palette():
    """Светлая палитра для всех виджетов (поля ввода, списки, подсказки)."""
    colors = {
        QtGui.QPalette.Window: PAGE_BG, QtGui.QPalette.WindowText: "#111111",
        QtGui.QPalette.Base: "#ffffff", QtGui.QPalette.AlternateBase: "#f3f5f9",
        QtGui.QPalette.Text: "#111111", QtGui.QPalette.PlaceholderText: "#b8c0cc",
        QtGui.QPalette.Button: "#eef2f8", QtGui.QPalette.ButtonText: "#111111",
        QtGui.QPalette.Highlight: "#2d5fb3", QtGui.QPalette.HighlightedText: "#ffffff",
        QtGui.QPalette.ToolTipBase: "#ffffe8", QtGui.QPalette.ToolTipText: "#111111",
        QtGui.QPalette.Light: "#ffffff", QtGui.QPalette.Midlight: "#e4e8f0",
        QtGui.QPalette.Mid: "#b0bac9", QtGui.QPalette.Dark: "#8a9bb8", QtGui.QPalette.Shadow: "#5a6a8a",
    }
    palette = QtGui.QPalette()
    for role, color in colors.items():
        palette.setColor(role, QtGui.QColor(color))
        palette.setColor(QtGui.QPalette.Disabled, role, QtGui.QColor(color))
    for role in (QtGui.QPalette.WindowText, QtGui.QPalette.Text, QtGui.QPalette.ButtonText):
        palette.setColor(QtGui.QPalette.Disabled, role, QtGui.QColor("#999999"))
    return palette


# Общий масштаб текста: настройки FONT_SCALE, LINES_PER_SCREEN и COLUMNS_PER_SCREEN находятся в settings.py.
def base_for_size(width, height):
    """Логические пиксели Qt уже учитывают масштаб Windows (125%, 150% и т.д.)."""
    return min(settings.FONT_MAX, max(settings.FONT_MIN, int(round(
        min(height / settings.LINES_PER_SCREEN,
            width / settings.COLUMNS_PER_SCREEN) * settings.FONT_SCALE))))


# Оформление всего приложения: палитра, фон графиков и правила для кнопок, рамок, полей и ползунков.
def init_style(app, size=None):
    """Подбирает размер шрифта под экран и настраивает Qt и pyqtgraph."""
    global BASE
    screen = app.primaryScreen().availableGeometry()
    width, height = screen.width(), screen.height()
    # Для снимков экрана в tools/screenshot.py можно задать размер "экрана" вручную.
    if os.environ.get("RELATIVE_SCREEN"):
        width, height = map(int, os.environ["RELATIVE_SCREEN"].split("x"))
    if size is not None:
        width, height = size.width(), size.height()
    BASE = base_for_size(width, height)

    f = app.font()
    f.setPixelSize(BASE)
    app.setFont(f)
    app.setStyle("Fusion")
    app.setPalette(light_palette())  # своя светлая палитра: тёмная тема системы не должна "протекать"

    pg.setConfigOptions(antialias=True, background="w", foreground="k")

    # КАРТА КНОПОК (тексты и действия задаются на страницах, здесь только оформление):
    # QPushButton — общая основа: навигация, Пауза/Стоп, Связать шкалы, Добавить график и т.д.
    # #primary — зелёный Старт в опыте: DemoPage вызывает btn_start.setObjectName("primary").
    # #big — четыре кнопки главного меню: TitlePage создаёт button(..., name="big").
    # #big[primary="true"] — синяя Презентация: setProperty("primary", True), это не имя #primary.
    # [tab="true"] — вариант Choice(..., tabs=True), если такой переключатель используется.
    # QToolButton#overlay — Повернуть распределение: имя задано в ui/widgets.overlay_button().
    # QToolButton#displayOptions — Вид: рамка и отступы совпадают с QPushButton.
    # Правило #overlay её не выбирает; DemoPage выравнивает высоту, ширина — по тексту.
    # Кнопка разворота графиков — QPushButton с иконкой: общие правила и состояние :checked.
    # #имя выбирает objectName; [свойство="значение"] — setProperty; :состояние — состояние Qt.
    # Обычное нажатие само по себе не даёт :checked: нужен setCheckable(True).
    # Более конкретные правила дополняют/переопределяют общие свойства того же элемента.
    # Внутри строки QSS комментарии пишутся как /* ... */, а не через Python-символ #.
    # Общие стили: QPushButton — кнопки, QFrame#card — карточки, QSlider — ползунки; изменения видны на всех страницах.
    app.setStyleSheet(
        """
        QMainWindow { background: %(page)s; }
        QWidget { color: #111111; }
        QWidget#experimentHeader { background: #203b5b; border-radius: %(rc)dpx; }
        QWidget#experimentHeader QLabel, QWidget#experimentHeader QCheckBox { color: white; }
        QFrame#plotHeader { background: #edf2f7; border-radius: %(r)dpx; }
        QFrame#card { background: #ffffff; border: 1px solid #d3dae6; border-radius: %(rc)dpx; }
        QFrame#runControls { background: #ffffff; border: 1px solid #d3dae6; border-radius: %(rc)dpx; }
        QLabel#section { color: #1c3f7a; font-weight: bold; }
        /* Общий вид обычных кнопок на всех страницах.
           background — заливка; border — толщина, тип и цвет рамки;
           border-radius — скругление; padding — внутреннее пространство вокруг текста.
           Два значения padding: сверху/снизу и слева/справа. */
        /* Меню Вид получает те же рамку и отступы, что соседняя кнопка Связать шкалы. */
        QPushButton, QToolButton#displayOptions {
            background: #eef2f8; border: 2px solid #8a9bb8; border-radius: %(r)dpx;
            padding: %(p)dpx %(p2)dpx;
        }
        /* Мышь над кнопкой: светлее фон. Это не нажатие и не изменение её действия. */
        QPushButton:hover, QToolButton#displayOptions:hover { background: #dde6f5; }
        /* У управления опытом слева больше внутренние отступы и удобнее область нажатия. */
        QFrame#runControls QPushButton { padding: %(run_p)dpx %(run_p2)dpx; }
        /* Включённая кнопка-переключатель: выбранный газ/режим, Связать шкалы,
           разворот графиков. Цвет текста — color, цвет рамки — border-color. */
        QPushButton:checked { background: #2d5fb3; color: white; border-color: #1c3f7a; }
        /* Недоступная кнопка, отключённая через setEnabled(False), например Старт при расчёте. */
        QPushButton:disabled { color: #999999; border-color: #cccccc; }
        /* Оформление кнопок Choice в режиме tabs=True: вместо полной рамки — нижняя линия.
           Сам механизм единственного выбора обеспечивает QButtonGroup в ui/widgets.py. */
        QPushButton[tab="true"] {
            background: transparent; border: none; border-radius: 0; color: #4a5568;
            border-bottom: %(tb)dpx solid #d3dae6; font-weight: bold; padding: %(p)dpx %(p)dpx;
        }
        /* Наведение на кнопку-вкладку. */
        QPushButton[tab="true"]:hover { background: #eef2f8; }
        /* Выбранная вкладка: синий текст, светлый фон, синяя нижняя граница. */
        QPushButton[tab="true"]:checked { color: #1c3f7a; background: #e3ebf8; border-bottom-color: #2d5fb3; }
        /* Служебная кнопка Повернуть у гистограммы, включая кнопку в шапке GraphPanel.
           QToolButton — другой тип кнопки, поэтому правила QPushButton её не оформляют.
           rgba(..., 220) задаёт почти непрозрачный белый фон; font-size — размер текста. */
        QToolButton#overlay {
            background: rgba(255, 255, 255, 220); border: 2px solid #8a9bb8; border-radius: %(r)dpx;
            font-size: %(ob)dpx; font-weight: bold; padding: 0px %(p)dpx;
        }
        /* Наведение на служебную кнопку Повернуть. */
        QToolButton#overlay:hover { background: #dde6f5; }
        /* Презентация, Теория по теме, Авторы, Выход на главной странице.
           big — итоговый размер текста, bp — внутренний отступ, br — радиус углов.
           Границы размера 18–26 px и значения bp/br вычисляются в dict ниже.
           Размер/ширину самого меню дополнительно ограничивает TitlePage.rescale_fonts(). */
        QPushButton#big {
            font-size: %(big)dpx; font-weight: bold; padding: %(bp)dpx;
            border-width: 1px; border-radius: %(br)dpx;
        }
        /* Только Старт в опыте: objectName равен primary. Меняй эти цвета,
           чтобы перекрасить Старт, сохранив цвет основной кнопки главного меню. */
        QPushButton#primary { background: #197c78; color: white; border-color: #197c78; }
        /* Более тёмный зелёный при наведении на Старт. */
        QPushButton#primary:hover { background: #12635f; }
        /* Только Презентация на главной: имя big И свойство primary=True.
           Остальные три кнопки имеют имя big, но это свойство у них False. */
        QPushButton#big[primary="true"] { background: #2859a3; color: white; border-color: #2859a3; }
        /* Более тёмный синий при наведении на Презентацию. */
        QPushButton#big[primary="true"]:hover { background: #1d4786; }
        QSpinBox, QDoubleSpinBox, QComboBox {
            border: 2px solid #8a9bb8; border-radius: %(r)dpx; padding: 2px; background: #ffffff; color: #111111;
        }
        QSlider::groove:horizontal { height: %(gh)dpx; background: #d0d8e8; border-radius: %(gr)dpx; }
        QSlider::handle:horizontal {
            background: #2d5fb3; width: %(hw)dpx; margin: -%(hm)dpx 0; border-radius: %(hr)dpx;
        }
        QCheckBox::indicator { width: %(cb)dpx; height: %(cb)dpx; }
        QScrollArea { border: none; }
        QTextBrowser { border: none; }
        """
        # Подстановки для QSS: r — радиус, p/p2 — отступы, big — шрифт меню,
        # bp/br — отступ/радиус кнопок меню, tb — линия вкладки, ob — шрифт Повернуть.
        # px(...) умножает долю на BASE. Литералы вроде br=8 уже заданы в пикселях.
        % dict(
            r=px(0.3), p=px(0.25), p2=px(0.5),
            run_p=px(.45), run_p2=px(.65),
            big=max(18, min(26, px(settings.MENU_BUTTON_FONT))), bp=min(10, px(0.45)), br=8,
            gh=px(0.4), gr=px(0.2), hw=px(1.0), hm=px(0.35), hr=px(0.5),
            cb=px(0.9), rc=px(0.4), tb=px(0.2), ob=px(0.9),
            page=PAGE_BG,
        )
    )


# Надстрочные цифры для обозначений масштаба осей, например 10⁻³.
def sup(n):
    """Число n верхним индексом: -3 -> '⁻³'."""
    table = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return str(n).translate(table)


# Единое оформление чисел; digits задаёт знаки после запятой, отсутствующее значение показывается тире.
def fmt(x, digits=0):
    """Число с разделением разрядов пробелом: 134000 -> '134 000'."""
    if x != x:  # NaN
        return "—"
    s = ("{:,.%df}" % digits).format(x).replace(",", " ")
    return s.replace("-", "−")


# Следит за изменением окна/F11 и масштабирует уже существующие страницы.
class WindowFontScale(QtCore.QObject):
    """Меняет относительные шрифты без пересоздания страниц и сброса опыта."""

    # Задержка 60 мс объединяет частые события изменения размера перед пересчётом интерфейса.
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.base = BASE
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(60)
        self.timer.timeout.connect(self.apply)
        window.installEventFilter(self)

    # Пересчёт нужен при показе/изменении окна; при закрытии отложенный пересчёт отменяется.
    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show):
            self.timer.start()
        elif event.type() == QtCore.QEvent.Close:
            self.timer.stop()
        return super().eventFilter(watched, event)

    # Обновляет шрифты, отступы и ограничения размеров без создания нового эксперимента.
    def apply(self):
        target = base_for_size(self.window.width(), self.window.height())
        if target == self.base:
            return
        widgets = [self.window] + self.window.findChildren(QtWidgets.QWidget)
        requested_size = self.window.size()
        ratio = target / self.base
        # Масштабируются и ограничения размеров: иначе увеличенный текст
        # попадает в старые фиксированные колонки и строки.
        for widget in widgets[1:]:
            minimum, maximum = widget.minimumSize(), widget.maximumSize()
            # Пересчитывает конечные ограничения размеров; специальное значение «без ограничения» оставляет прежним.
            def scaled(size):
                return QtCore.QSize(*(round(value * ratio) if value < 16777215 else value
                                      for value in (size.width(), size.height())))
            widget.setMinimumSize(scaled(minimum))
            widget.setMaximumSize(scaled(maximum))
            icon = widget.iconSize() if isinstance(widget, QtWidgets.QAbstractButton) else None
            if icon is not None:
                widget.setIconSize(scaled(icon))
        for layout in self.window.findChildren(QtWidgets.QLayout):
            margins = layout.contentsMargins()
            layout.setContentsMargins(*(round(value * ratio) for value in
                                        (margins.left(), margins.top(), margins.right(), margins.bottom())))
            if layout.spacing() >= 0:
                layout.setSpacing(round(layout.spacing() * ratio))
        # Запоминаем коэффициенты до смены общего шрифта приложения.
        for widget in widgets:
            if not hasattr(widget, '_relative_font'):
                f = widget.font()
                size = f.pixelSize() if f.pixelSize() > 0 else QtGui.QFontInfo(f).pixelSize()
                widget._relative_font = (size / self.base, f)
        init_style(QtWidgets.QApplication.instance(), self.window.size())
        self.base = target
        for widget in widgets:
            factor, original = widget._relative_font
            f = QtGui.QFont(original)
            f.setPixelSize(px(factor))
            widget.setFont(f)
        for widget in widgets:
            if hasattr(widget, 'rescale_fonts'):
                widget.rescale_fonts()
        for widget in reversed(widgets):
            if hasattr(widget, 'rescale_layout'):
                widget.rescale_layout()
        self.window.layout().activate()
        self.window.resize(requested_size)
        self.window.update()
