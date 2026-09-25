"""
Страница "Теория по теме": HTML из assets/theory/theory.html.
Формулы — картинки, заранее нарисованные скриптом tools/render_formulas.py
в тройном разрешении; здесь их размер подгоняется под размер шрифта.
"""

import os
import re

from PyQt5 import QtGui, QtWidgets

from ui import style
from ui.widgets import header_bar

RENDER_SCALE = 3.0   # во сколько раз формулы нарисованы крупнее, чем нужно при шрифте 20 px
DESIGN_FONT = 20.0


class TheoryPage(QtWidgets.QWidget):
    def __init__(self, go_home, go_demo):
        super().__init__()
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(header_bar("Теория по теме", go_home, [("Презентация ▶", go_demo)]))

        self.browser = QtWidgets.QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.document().setDefaultFont(style.font(1.0))
        self.browser.document().setDocumentMargin(style.px(1.5))
        folder = style.resource_path("theory")
        self.browser.setSearchPaths([folder])
        self.browser.setHtml(self._load_html(folder))
        lay.addWidget(self.browser, 1)

    def _load_html(self, folder):
        with open(os.path.join(folder, "theory.html"), encoding="utf-8") as f:
            html = f.read()
        zoom = style.BASE / DESIGN_FONT / RENDER_SCALE

        def sized(match):
            name = match.group(1)
            size = QtGui.QImageReader(os.path.join(folder, name)).size()
            if not size.isValid():
                return match.group(0)
            return '<img src="%s" width="%d" height="%d"' % (
                name, round(size.width() * zoom), round(size.height() * zoom))

        return re.sub(r'<img src="([^"]+)"', sized, html)
