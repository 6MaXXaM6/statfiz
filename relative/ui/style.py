"""
Общий стиль: размеры шрифтов и линий зависят от разрешения экрана,
чтобы презентация одинаково читалась на ноутбуке и на проекторе.
"""

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


def resource_path(*parts):
    """Путь к файлу из папки assets — работает и из исходников, и из собранного exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "assets", *parts)


def px(k=1.0):
    """Размер в пикселях, пропорциональный базовому шрифту."""
    return max(1, int(round(BASE * k)))


def font(k=1.0, bold=False):
    f = QtGui.QFont()
    f.setPixelSize(px(k))
    f.setBold(bold)
    return f


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


def base_for_size(width, height):
    """Логические пиксели Qt уже учитывают масштаб Windows (125%, 150% и т.д.)."""
    return min(settings.FONT_MAX, max(settings.FONT_MIN, int(round(
        min(height / settings.LINES_PER_SCREEN,
            width / settings.COLUMNS_PER_SCREEN) * settings.FONT_SCALE))))


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

    app.setStyleSheet(
        """
        QMainWindow { background: %(page)s; }
        QWidget { color: #111111; }
        QFrame#card { background: #ffffff; border: 1px solid #d3dae6; border-radius: %(rc)dpx; }
        QLabel#section { color: #1c3f7a; font-weight: bold; }
        QPushButton {
            background: #eef2f8; border: 2px solid #8a9bb8; border-radius: %(r)dpx;
            padding: %(p)dpx %(p2)dpx;
        }
        QPushButton:hover { background: #dde6f5; }
        QPushButton:checked { background: #2d5fb3; color: white; border-color: #1c3f7a; }
        QPushButton:disabled { color: #999999; border-color: #cccccc; }
        QPushButton[tab="true"] {
            background: transparent; border: none; border-radius: 0; color: #4a5568;
            border-bottom: %(tb)dpx solid #d3dae6; font-weight: bold; padding: %(p)dpx %(p)dpx;
        }
        QPushButton[tab="true"]:hover { background: #eef2f8; }
        QPushButton[tab="true"]:checked { color: #1c3f7a; background: #e3ebf8; border-bottom-color: #2d5fb3; }
        QToolButton#overlay {
            background: rgba(255, 255, 255, 220); border: 2px solid #8a9bb8; border-radius: %(r)dpx;
            font-size: %(ob)dpx; font-weight: bold; padding: 0px %(p)dpx;
        }
        QToolButton#overlay:hover { background: #dde6f5; }
        QPushButton#big {
            font-size: %(big)dpx; font-weight: bold; padding: %(bp)dpx;
            border-width: 1px; border-radius: %(br)dpx;
        }
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
        % dict(
            r=px(0.3), p=px(0.25), p2=px(0.5),
            big=min(22, px(settings.MENU_BUTTON_FONT)), bp=px(0.35), br=px(0.3),
            gh=px(0.4), gr=px(0.2), hw=px(1.0), hm=px(0.35), hr=px(0.5),
            cb=px(0.9), rc=px(0.4), tb=px(0.2), ob=px(0.9),
            page=PAGE_BG,
        )
    )


def sup(n):
    """Число n верхним индексом: -3 -> '⁻³'."""
    table = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return str(n).translate(table)


def fmt(x, digits=0):
    """Число с разделением разрядов пробелом: 134000 -> '134 000'."""
    if x != x:  # NaN
        return "—"
    s = ("{:,.%df}" % digits).format(x).replace(",", " ")
    return s.replace("-", "−")


class WindowFontScale(QtCore.QObject):
    """Меняет относительные шрифты без пересоздания страниц и сброса опыта."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.base = BASE
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(60)
        self.timer.timeout.connect(self.apply)
        window.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show):
            self.timer.start()
        elif event.type() == QtCore.QEvent.Close:
            self.timer.stop()
        return super().eventFilter(watched, event)

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
