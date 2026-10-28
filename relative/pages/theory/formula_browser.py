"""Текст теории с заранее набранными формулами, без браузера и сети."""
import hashlib
import html
import re
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtSvg, QtWidgets

import settings
from ui import style


class FormulaBrowser(QtWidgets.QTextBrowser):
    def __init__(self, source):
        super().__init__()
        self.source = source
        self.formulas = {}
        self.setOpenExternalLinks(True)
        self.document().setDefaultFont(style.font(settings.THEORY_TEXT_FONT))
        self.document().setDocumentMargin(style.px(.8))
        self.document().setDefaultStyleSheet(
            'h2 { color: #1c3f7a; } .note { color: #555555; } '
            '.try { color: #1f4fd1; }')
        self._render()

    def _render(self):
        # SVG содержит контуры букв: результат не зависит от установленных шрифтов.
        # Тройное разрешение сохраняет чёткость и на экранах Retina.
        max_width = max(80, self.viewport().width() - 2*self.document().documentMargin() - 12)
        table_fraction = [1.]
        display = [False]

        def replace(match):
            token = match.group(0)
            if token.startswith('<table'):
                row = re.search(r'<tr>(.*?)</tr>', self.source[match.end():], re.S)
                columns = len(re.findall(r'<t[dh]\b', row.group(1))) if row else 3
                table_fraction[0] = .60 if columns == 2 else .36
                return token
            if token == '</table>':
                table_fraction[0] = 1.
                return token
            if token.startswith('<p'):
                display[0] = 'class="f"' in token
                return token
            expr = match.group(1)
            name = hashlib.sha256(expr.encode('utf-8')).hexdigest()[:20]
            if name not in self.formulas:
                path = Path(style.resource_path('theory', 'formulas', name + '.svg'))
                svg = QtSvg.QSvgRenderer(str(path))
                if not svg.isValid():
                    raise ValueError('Не удалось прочитать формулу: ' + str(path))
                rect = svg.viewBoxF()
                self.formulas[name] = svg, rect
            svg, rect = self.formulas[name]
            font_size = style.px(settings.THEORY_FORMULA_FONT if display[0]
                                 else settings.THEORY_TEXT_FONT)
            scale = font_size / 10.
            limit = max_width * table_fraction[0]
            width = min(rect.width()*scale, limit)
            height = width * rect.height() / rect.width()
            image = QtGui.QImage(max(1, int(width*3)), max(1, int(height*3)),
                                 QtGui.QImage.Format_ARGB32_Premultiplied)
            image.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(image)
            svg.render(painter)
            painter.end()
            url = QtCore.QUrl('formula:' + name)
            self.document().addResource(QtGui.QTextDocument.ImageResource, url, image)
            return ('<img src="%s" width="%.2f" height="%.2f" '
                    'style="vertical-align: middle;" alt="%s" />'
                    % (url.toString(), width, height, html.escape(expr, quote=True)))

        scroll = self.verticalScrollBar().value()
        markup = re.sub(r'<math>(.*?)</math>|<table\b[^>]*>|</table>|<p\b[^>]*>',
                        replace, self.source, flags=re.S)
        self.setHtml(markup)
        self.verticalScrollBar().setValue(scroll)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()


class FormulaReadout(FormulaBrowser):
    """Компактная подпись к графику с тем же набором формул."""
    def __init__(self):
        super().__init__('')
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

    def setText(self, text):
        self.source = text
        self._render()

    def text(self):
        return self.source

    def _render(self):
        super()._render()
        self.setFixedHeight(int(self.document().size().height()) + 2)
