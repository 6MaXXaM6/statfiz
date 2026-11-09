"""Страница "Авторы": имена и фотографии из assets/authors.json."""

import json

from PyQt5 import QtCore, QtGui, QtWidgets

from ui import style
from ui.images import load_pixmap
from ui.widgets import hbox, header_bar, label, vbox


# Имена, группы, пути фотографий и примечания редактируются в assets/authors.json.
def load_authors():
    with open(style.resource_path("authors.json"), encoding="utf-8") as f:
        return json.load(f)


# Рисует силуэт вместо недоступной фотографии; здесь можно изменить его вид.
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


# Одна карточка человека: имя и info из JSON, дополнительная роль — из вызова ниже.
class PersonCard(QtWidgets.QFrame):
    """Фотография и подпись; картинки пересчитываются только при смене масштаба."""

    # Создаёт фото и подписи; коэффициенты 1.1 и .95 задают размеры их шрифтов.
    def __init__(self, person, role=None):
        super().__init__()
        self.person = person
        self.setObjectName("card")
        self.photo = QtWidgets.QLabel()
        self.photo.setAlignment(QtCore.Qt.AlignCenter)
        self.name = label(person.get("name", ""), 1.1, bold=True,
                          center=True, wrap=True, shrinkable=True)
        info = person.get("info", "")
        if role:
            info = role + ("\n" + info if info else "")
        self.info = label(info, .95, center=True, wrap=True)
        self.setLayout(vbox(self.photo, self.name, self.info,
                            spacing=style.px(.4)))
        self.rescale_layout()

    # Здесь менять размеры фото/карточки и число строк, отведённых имени и подписи.
    def rescale_layout(self):
        side = max(100, min(220, style.px(11)))
        self.photo.setFixedSize(side, side)
        # Путь photo считается от assets/; можно заменить картинку, сохранив имя файла.
        self.photo.setPixmap(load_pixmap(self.person.get("photo"), side, side)
                             or photo_placeholder(side))
        # Высота ограничивает число строк: увеличить при длинных ФИО или пояснениях.
        self.name.setFixedHeight(3 * self.name.fontMetrics().lineSpacing())
        self.info.setFixedHeight(2 * self.info.fontMetrics().lineSpacing())
        self.setMaximumWidth(min(340, style.px(20)))
        margin = style.px(.7)
        self.layout().setContentsMargins(margin, margin, margin, margin)
        self.layout().setAlignment(self.photo, QtCore.Qt.AlignHCenter)


# Страница автоматически создаёт карточки по списку authors в JSON.
class AuthorsPage(QtWidgets.QWidget):
    # Здесь меняются шапка, надпись «Преподаватель» и расположение карточек.
    def __init__(self, go_home):
        super().__init__()
        data = load_authors()
        cards = [PersonCard(p) for p in data.get("authors", [])]
        sup = data.get("supervisor")
        if sup:
            # Слово роли задано здесь, а имя и кафедра преподавателя — в JSON.
            cards.append(PersonCard(sup, "Преподаватель"))
        items = [header_bar("Авторы", go_home), (None, 1),
                 hbox(None, *((card, 1) for card in cards), None, spacing=style.px(.8))]
        items += [label(note, center=True, wrap=True, color="#555555") for note in data.get("notes", [])]
        items.append((None, 2))
        margin = style.px(.7)
        self.setLayout(vbox(*items, spacing=style.px(.5),
                            margins=(margin, 0, margin, style.px(1))))
