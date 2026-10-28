"""Теория: интерактивные разделы и источники с сопоставлением 2D/3D."""
from pathlib import Path
from PyQt5 import QtWidgets
import settings
from ui import style
from ui.drawer import Drawer
from ui.widgets import button, card, header_bar, hbox, label, section_title, vbox
from pages.theory.formula_browser import FormulaBrowser
from pages.theory.curve_demo import CurveDemo
from pages.theory.sampling_demo import SamplingDemo
from pages.theory.collision_sketch import CollisionSketch

SECTIONS = [
    ("1. Модель газа", "01_model.html", CollisionSketch),
    ("2. Проекция скорости", "02_projection.html", lambda: CurveDemo("projection")),
    ("3. Модуль скорости", "03_modulus.html", lambda: CurveDemo("modulus")),
    ("4. Относительная скорость", "04_relative.html", lambda: CurveDemo("relative")),
    ("5. Кинетическая энергия", "05_energy.html", lambda: CurveDemo("energy")),
    ("6. Смесь газов", "06_mixture.html", lambda: CurveDemo("mixture")),
    ("7. Как устроен опыт", "07_experiment.html", SamplingDemo),
    ("8. Источники · 2D / 3D", "08_sources.html", None),
]


class TheoryPage(QtWidgets.QWidget):
    def __init__(self, go_home, go_demo):
        super().__init__()
        self.stack = QtWidgets.QStackedWidget()
        self.nav = []
        self.group = QtWidgets.QButtonGroup(self)
        nav = vbox(section_title("Разделы"), spacing=style.px(.3))
        for index, (title, filename, factory) in enumerate(SECTIONS):
            text = FormulaBrowser(Path(style.resource_path("theory", filename)).read_text(encoding="utf-8"))
            section = QtWidgets.QWidget()
            section.demo = factory() if factory else None
            items = [(text, 1)]
            if section.demo is not None:
                items.append((card(section.demo), 1))
            section.setLayout(hbox(*items, spacing=style.px(.5)))
            self.stack.addWidget(section)
            b = button(title, lambda _checked, i=index: self._choose(i), checkable=True)
            b.setStyleSheet("text-align: left; padding-left: 0.5em;")
            self.group.addButton(b)
            self.nav.append(b)
            nav.addWidget(b)
        nav.addStretch(1)
        content = QtWidgets.QWidget()
        content.setLayout(nav)
        menu = button("☰  Разделы", lambda: self.drawer.toggle())
        self.back = button("◀ Назад", lambda: self.show_section(self.stack.currentIndex() - 1))
        self.next = button("Далее ▶", lambda: self.show_section(self.stack.currentIndex() + 1))
        self.caption = label(size=1., bold=True, center=True, shrinkable=True)
        self.header = header_bar("Теория по теме", go_home, [("Презентация ▶", go_demo)])
        m = style.px(.4)
        body = vbox((self.stack, 1), hbox(menu, self.back, (self.caption, 1), self.next,
                    spacing=m), spacing=m, margins=(m, 0, m, m))
        self.setLayout(vbox(self.header, (body, 1), spacing=0))
        self.drawer = Drawer(self, content, settings.DRAWER_WIDTH)
        self.show_section(0)

    def _choose(self, index):
        self.show_section(index)
        self.drawer.close()

    def show_section(self, index):
        if not 0 <= index < self.stack.count():
            return
        self.stack.setCurrentIndex(index)
        self.nav[index].setChecked(True)
        self.back.setEnabled(index > 0)
        self.next.setEnabled(index + 1 < self.stack.count())
        self.caption.setText(f"{index + 1} / {self.stack.count()} · {SECTIONS[index][0].split('. ', 1)[1]}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.drawer.set_top(self.header.height())
