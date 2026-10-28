"""Выдвижное меню разделов: анимация, затемнение и закрытие по Esc."""
from PyQt5 import QtCore, QtWidgets
from ui import style


class Drawer(QtWidgets.QFrame):
    def __init__(self, host, content, width=17):
        super().__init__(host)
        self.host, self.top, self.is_open = host, 0, False
        self.shade = QtWidgets.QPushButton(host)
        self.shade.setStyleSheet("background: rgba(20,30,50,90); border: none; border-radius: 0;")
        self.shade.clicked.connect(self.close)
        self.shade.hide()
        self.setObjectName("drawer")
        self.setStyleSheet("QFrame#drawer { background: white; border-right: 2px solid #8a9bb8; }")
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        layout = QtWidgets.QVBoxLayout(self)
        m = style.px(.5)
        layout.setContentsMargins(m, m, m, m)
        layout.addWidget(content)
        self.setFixedWidth(style.px(width))
        self.slide = QtCore.QPropertyAnimation(self, b"pos", self)
        self.slide.setDuration(180)
        self.slide.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.slide.finished.connect(self._finished)
        self.hide()
        host.installEventFilter(self)

    def place(self):
        self.resize(self.width(), max(1, self.host.height() - self.top))
        self.shade.setGeometry(0, self.top, self.host.width(), self.height())
        self.move(0 if self.is_open else -self.width(), self.top)

    def set_top(self, top):
        self.top = top
        self.place()

    def toggle(self):
        self.close() if self.is_open else self.open()

    def open(self):
        if self.is_open:
            return
        self.place()
        self.is_open = True
        self.shade.show()
        self.shade.raise_()
        self.show()
        self.raise_()
        self.setFocus()
        self._animate(0)

    def close(self):
        self.is_open = False
        self._animate(-self.width())

    def _animate(self, x):
        self.slide.stop()
        self.slide.setStartValue(self.pos())
        self.slide.setEndValue(QtCore.QPoint(x, self.top))
        self.slide.start()

    def _finished(self):
        if not self.is_open:
            self.hide()
            self.shade.hide()

    def eventFilter(self, watched, event):
        if watched is self.host and event.type() == QtCore.QEvent.Resize:
            self.place()
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
