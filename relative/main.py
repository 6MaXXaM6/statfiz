"""
Презентация "Относительная скорость движения молекул идеального газа".
Запуск: python main.py   (F11 — полный экран / окно, Esc — выйти из полного экрана)
"""

import os
import sys

from PyQt5 import QtCore, QtWidgets

# Включаем масштабирование для экранов с увеличенным DPI (до создания приложения).
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import style  # noqa: E402
from pages.authors_page import AuthorsPage  # noqa: E402
from pages.demo import DemoPage  # noqa: E402
from pages.theory_page import TheoryPage  # noqa: E402
from pages.title_page import TitlePage  # noqa: E402


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Относительная скорость молекул")
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.title = TitlePage(self.show_demo, self.show_theory, self.show_authors, self.close)
        self.demo = DemoPage(self.show_title, self.show_theory)
        self.theory = TheoryPage(self.show_title, self.show_demo)
        self.authors = AuthorsPage(self.show_title)
        for page in (self.title, self.demo, self.theory, self.authors):
            self.stack.addWidget(page)

    def show_title(self):
        self.stack.setCurrentWidget(self.title)

    def show_demo(self):
        self.stack.setCurrentWidget(self.demo)

    def show_theory(self):
        self.demo.pause()
        self.stack.setCurrentWidget(self.theory)

    def show_authors(self):
        self.stack.setCurrentWidget(self.authors)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F11:
            if self.isFullScreen():
                self.showMaximized()
            else:
                self.showFullScreen()
        elif event.key() == QtCore.Qt.Key_Escape and self.isFullScreen():
            self.showMaximized()
        else:
            super().keyPressEvent(event)


def smoke_test(app, window, report_path):
    """Проверка собранной программы: открыть все страницы, посчитать несколько секунд
    в быстром режиме с четырьмя графиками и записать результат в файл report_path."""
    def finish():
        print("DBG finish", flush=True)
        demo = window.demo
        ok = demo.exp.gas.collisions > 0 and all(p.quantity for p in demo.panels)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("OK collisions=%d panels=%d\n" % (demo.exp.gas.collisions, len(demo.panels)) if ok else "FAIL\n")
        app.quit()

    def start():
        print("DBG start", flush=True)
        for show in (window.show_theory, window.show_authors, window.show_title, window.show_demo):
            show()
        for _ in range(3):
            window.demo.add_next_panel()
        window.demo.run.mode.buttons["fast"].click()
        window.demo.run.btn_start.click()
        print("DBG start done", flush=True)
        QtCore.QTimer.singleShot(4000, finish)

    QtCore.QTimer.singleShot(500, start)


def main():
    app = QtWidgets.QApplication(sys.argv)
    style.init_style(app)
    window = MainWindow()
    if "--window" in sys.argv or "--smoke-test" in sys.argv:
        window.resize(1024, 768)
        window.show()
    else:
        window.showFullScreen()
    if "--smoke-test" in sys.argv:
        smoke_test(app, window, sys.argv[sys.argv.index("--smoke-test") + 1])
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
