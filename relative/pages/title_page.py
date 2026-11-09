"""Титульная страница: название, эмблемы факультетов и четыре кнопки."""

import settings

from PyQt5 import QtCore, QtGui, QtWidgets

from ui import style
from ui.images import load_pixmap
from ui.widgets import button, hbox, label, vbox

# Название и подзаголовок главной; \n в TITLE задаёт перенос строки.
TITLE = "Относительная скорость движения\nмолекул идеального газа"
SUBTITLE = "Компьютерная презентация по статистической физике"


# Запасная эмблема: здесь меняются подпись, цвет и пунктир при отсутствии картинки.
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


# Создаёт виджет эмблемы; размер берётся из settings.EMBLEM_SIZE, файл — из assets/.
def emblem(filename):
    size = style.px(settings.EMBLEM_SIZE)
    w = QtWidgets.QLabel()
    w.setAlignment(QtCore.Qt.AlignCenter)
    w.setPixmap(load_pixmap(filename, size, size) or emblem_placeholder(size))
    return w


# Главный экран: названия и кнопки здесь, сами переходы передаются из main.py.
class TitlePage(QtWidgets.QWidget):
    # Собирает заголовок, эмблемы и четыре кнопки; порядок и отступы задаются ниже.
    def __init__(self, on_demo, on_theory, on_authors, on_exit):
        super().__init__()
        title = label(TITLE, settings.TITLE_FONT, bold=True, center=True, color="#1c3f7a", shrinkable=True)
        self.heading = title
        title.setMinimumHeight(style.px(6))
        subtitle = label(SUBTITLE, settings.SUBTITLE_FONT, center=True, wrap=True)
        self.subtitle = subtitle
        buttons = vbox(spacing=style.px(0.6))
        self.menu = QtWidgets.QWidget()
        self.menu.setLayout(buttons)
        self.rescale_fonts()
        # Текст кнопок меняется в парах ниже, callback оставляет прежнее действие.
        for text, callback in (("Презентация", on_demo), ("Теория по теме", on_theory),
                               ("Авторы", on_authors), ("Выход", on_exit)):
            b = button(text, callback, name="big")
            # При переименовании «Презентация» согласовать сравнение, чтобы сохранить синюю заливку.
            b.setProperty("primary", text == "Презентация")
            buttons.addWidget(b)
        m = style.px(2)
        # Эмблемы лежат в assets/; hbox — строка, vbox — колонка, margins — отступы.
        self.setLayout(vbox(
            hbox(emblem("emblem_left.png"), (title, 1), emblem("emblem_right.png")),
            subtitle, (None, 1), hbox(None, self.menu, None), (None, 2),
            margins=(m, style.px(1.5), m, style.px(1.5)),
        ))

    # Настраивает размеры меню и текста; пределы min/max могут ограничить эффект TITLE_FONT.
    def rescale_fonts(self):
        self.menu.setFixedWidth(min(380, max(280, style.px(22))))
        heading = style.font(settings.TITLE_FONT, bold=True)
        heading.setPixelSize(max(30, min(48, heading.pixelSize())))
        self.heading.setFont(heading)
        subtitle = style.font(settings.SUBTITLE_FONT)
        subtitle.setPixelSize(max(15, min(23, subtitle.pixelSize())))
        self.subtitle.setFont(subtitle)
