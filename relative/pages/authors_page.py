"""Страница "Авторы": имена и фотографии из assets/authors.json."""

import json

from PyQt5 import QtCore, QtGui, QtWidgets

from ui import style
from ui.images import load_pixmap
from ui.widgets import hbox, header_bar, label, vbox


def load_authors():
    with open(style.resource_path("authors.json"), encoding="utf-8") as f:
        return json.load(f)


def photo_placeholder(size):
    """Серый силуэт — пока нет фотографии."""
    pix = QtGui.QPixmap(int(size * 0.8), size)
    pix.fill(QtGui.QColor("#e4e8f0"))
    p = QtGui.QPainter(pix)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setPen(QtCore.Qt.NoPen)
    p.setBrush(QtGui.QColor("#b0bac9"))
    w = pix.width()
    p.drawEllipse(QtCore.QRectF(w * 0.3, size * 0.15, w * 0.4, w * 0.4))
    p.drawEllipse(QtCore.QRectF(w * 0.1, size * 0.6, w * 0.8, size * 0.6))
    p.end()
    return pix


def person_card(person, size):
    photo = QtWidgets.QLabel()
    photo.setAlignment(QtCore.Qt.AlignCenter)
    photo.setPixmap(load_pixmap(person.get("photo"), size, size) or photo_placeholder(size))
    items = [photo, label(person.get("name", ""), 1.2, bold=True, center=True, wrap=True)]
    if person.get("info"):
        items.append(label(person["info"], center=True, wrap=True))
    card = QtWidgets.QWidget()
    card.setLayout(vbox(*items))
    return card


class AuthorsPage(QtWidgets.QWidget):
    def __init__(self, go_home):
        super().__init__()
        data = load_authors()
        cards = [person_card(p, style.px(11)) for p in data.get("authors", [])]
        items = [header_bar("Авторы", go_home), (None, 1), hbox(None, *cards, None)]
        sup = data.get("supervisor")
        if sup:
            info = ", " + sup["info"] if sup.get("info") else ""
            items.append(label("Преподаватель: <b>%s</b>%s" % (sup.get("name", ""), info),
                               1.2, center=True, wrap=True))
        items += [label(note, center=True, wrap=True, color="#555555") for note in data.get("notes", [])]
        items.append((None, 2))
        self.setLayout(vbox(*items, spacing=style.px(0.5), margins=(0, 0, 0, style.px(1))))
