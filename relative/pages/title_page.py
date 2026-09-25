"""Титульная страница: название, эмблемы факультетов и четыре кнопки."""

from PyQt5 import QtCore, QtGui, QtWidgets

from ui import style
from ui.images import load_pixmap
from ui.widgets import button, hbox, label, vbox

TITLE = "Относительная скорость движения\nмолекул идеального газа"
SUBTITLE = "Компьютерная презентация по статистической физике"


def emblem_placeholder(size):
    """Пунктирный круг с подписью — пока нет настоящей эмблемы."""
    pix = QtGui.QPixmap(size, size)
    pix.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pix)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setPen(QtGui.QPen(QtGui.QColor("#8a9bb8"), 4, QtCore.Qt.DashLine))
    p.drawEllipse(4, 4, size - 8, size - 8)
    p.setFont(style.font(0.8))
    p.drawText(pix.rect(), QtCore.Qt.AlignCenter, "эмблема\nфакультета")
    p.end()
    return pix


def emblem(filename):
    size = style.px(6)
    w = QtWidgets.QLabel()
    w.setAlignment(QtCore.Qt.AlignCenter)
    w.setPixmap(load_pixmap(filename, size, size) or emblem_placeholder(size))
    return w


class TitlePage(QtWidgets.QWidget):
    def __init__(self, on_demo, on_theory, on_authors, on_exit):
        super().__init__()
        title = label(TITLE, 2.1, bold=True, center=True, color="#1c3f7a", shrinkable=True)
        title.setMinimumHeight(style.px(6))
        subtitle = label(SUBTITLE, 1.2, center=True, wrap=True)
        buttons = vbox(spacing=style.px(0.8))
        for text, callback in (("Презентация", on_demo), ("Теория по теме", on_theory),
                               ("Авторы", on_authors), ("Выход", on_exit)):
            b = button(text, callback, name="big")
            b.setMinimumWidth(style.px(16))
            buttons.addWidget(b, 0, QtCore.Qt.AlignHCenter)
        m = style.px(2)
        self.setLayout(vbox(
            hbox(emblem("emblem_left.png"), (title, 1), emblem("emblem_right.png")),
            subtitle, (None, 1), buttons, (None, 2),
            margins=(m, style.px(1.5), m, style.px(1.5)),
        ))
