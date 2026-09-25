"""
Проверка компоновки: окно фиксированного размера (как на весь экран), по очереди нажимаются
кнопки страницы "Презентация", после каждого действия проверяется, что
  * минимальный размер страницы не больше экрана (иначе Qt обрежет край),
  * все видимые кнопки, списки и движки целиком внутри окна.

Запуск: python tools/layout_check.py 1024x768   (без аргумента — несколько разрешений)
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PyQt5 import QtCore, QtWidgets  # noqa: E402

SCREENS = ["1024x768", "1366x768", "1920x1080"]
CONTROLS = (QtWidgets.QAbstractButton, QtWidgets.QComboBox, QtWidgets.QSlider, QtWidgets.QSpinBox)


def problems(win):
    """Список нарушений компоновки в текущем состоянии окна."""
    found = []
    page = win.demo
    hint = page.minimumSizeHint()
    if hint.width() > page.width() or hint.height() > page.height():
        found.append("страница требует %dx%d, а есть %dx%d" % (hint.width(), hint.height(), page.width(), page.height()))
    area = QtCore.QRect(0, 0, win.width(), win.height())
    for w in page.findChildren(QtWidgets.QWidget):
        if not isinstance(w, CONTROLS) or not w.isVisibleTo(win):
            continue
        rect = QtCore.QRect(w.mapTo(win, QtCore.QPoint(0, 0)), w.size())
        if not area.contains(rect):
            text = w.text() if hasattr(w, "text") else type(w).__name__
            found.append("за краем: %s %s" % (text.strip()[:25], (rect.x(), rect.y(), rect.width(), rect.height())))
    return found


def plot_areas(page):
    """Где на экране области данных всех графиков (чтобы заметить, если они "ездят")."""
    areas = []
    for panel in page.panels:
        for plot in (panel.time_plot, panel.hist_plot):
            vb = plot.getViewBox()
            r = vb.mapRectToScene(vb.boundingRect()).toRect()
            areas.append((plot.mapTo(page, QtCore.QPoint(0, 0)), r))
    return areas


def run_frames(app, page, n=30):
    """Кадры расчёта; возвращает True, если области графиков сдвигались между кадрами."""
    before = plot_areas(page)
    moved = False
    for _ in range(n):
        page.run._on_timer()
        page.run.timer.stop()  # кадры считаем вручную
        app.processEvents()
        now = plot_areas(page)
        moved = moved or now != before
        before = now
    return moved


def scenario(page):
    """Действия пользователя: (описание, функция)."""
    from model import theory as tf
    from model.experiment import GAS_MIX, GAS_PURE, PAIR, SINGLE
    run = page.run

    def click(button):
        return lambda: button.click()

    def panel(n):
        return lambda: page.panels[n]

    return [
        ("Старт", click(run.btn_start)),
        ("Быстро", click(run.mode.buttons["fast"])),
        ("Медленно", click(run.mode.buttons["slow"])),
        ("Пауза", click(run.btn_pause)),
        ("Продолжить", click(run.btn_pause)),
        ("↻ график 1", lambda: page.panels[0].hist_plot.rotate_button.click()),
        ("↻ график 1 обратно", lambda: page.panels[0].hist_plot.rotate_button.click()),
        ("Добавить график 2", click(page.add_button)),
        ("↻ график 2", lambda: page.panels[1].hist_plot.rotate_button.click()),
        ("график 2: v₂,x", lambda: page.panels[1].selector.setCurrentIndex(5)),
        ("Смесь", click(page.gas.gas_mode.buttons[GAS_MIX])),
        ("Пара A–B", click(page.gas.pair.buttons["AB"])),
        ("Добавить график 3", click(page.add_button)),
        ("Добавить график 4", click(page.add_button)),
        ("↻ график 4", lambda: page.panels[3].hist_plot.rotate_button.click()),
        ("Быстро (4 графика)", click(run.mode.buttons["fast"])),
        ("Один газ (4 графика)", click(page.gas.gas_mode.buttons[GAS_PURE])),
        ("✕ график 4", lambda: page.remove_panel(page.panels[3])),
        ("✕ график 3", lambda: page.remove_panel(page.panels[2])),
        ("Медленно (2 графика)", click(run.mode.buttons["slow"])),
        ("Стоп", click(run.btn_stop)),
        ("Старт снова", click(run.btn_start)),
    ] + extremes(page), (tf, PAIR, SINGLE, panel)


def set_param(control, value):
    """Как будто пользователь ввёл число: значение + сигнал без задержки."""
    return lambda: (control.spin.setValue(value), control.changed.emit(value))


def extremes(page):
    """Крайние значения параметров, выбор молекул мышью и все величины в списках графиков."""
    from model.experiment import GAS_MIX
    gas = page.gas
    steps = [
        ("T = 1500", set_param(gas.temperature, 1500)),
        ("m_A = 1", set_param(gas.mass_a, 1)),
        ("N = 300", set_param(gas.n_total, 300)),
        ("m_A = 200", set_param(gas.mass_a, 200)),
        ("T = 50", set_param(gas.temperature, 50)),
        ("Смесь, m_B = 1", lambda: (gas.gas_mode.buttons[GAS_MIX].click(), set_param(gas.mass_b, 1)())),
        ("N_B = 1 (одна чужая)", set_param(gas.n_b, 1)),
        ("щелчок: молекула 1", lambda: page.on_box_clicked(20, 20, 1)),
        ("щелчок: молекула 2", lambda: page.on_box_clicked(80, 80, 2)),
        ("N = 2", set_param(gas.n_total, 2)),
    ]
    for n in range(6):
        steps.append(("график 1: величина %d" % n, lambda n=n: page.panels[0].selector.setCurrentIndex(n)))
        steps.append(("график 2: величина %d" % n, lambda n=n: page.panels[1].selector.setCurrentIndex(n)))
    return steps


def check(screen):
    import main
    from ui import style
    w, h = map(int, screen.split("x"))
    os.environ["RELATIVE_SCREEN"] = screen
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    style.init_style(app)
    win = main.MainWindow()
    win.setFixedSize(w, h)  # как на весь экран: окно больше экрана не станет
    win.show()
    win.show_demo()
    app.processEvents()
    page = win.demo
    bad = 0
    actions, _ = scenario(page)
    for name, action in actions:
        action()
        page.run.timer.stop()
        for _ in range(3):  # отложенные перекладки виджетов, как в настоящем цикле событий
            QtWidgets.QApplication.sendPostedEvents()
            app.processEvents()
        found = []
        if page.run.state == "running" and run_frames(app, page):
            found.append("графики сдвигаются во время расчёта")
        found += problems(win)
        if found:
            bad += 1
            print("  [%s] %s:" % (screen, name))
            for f in found[:8]:
                print("      ", f)
    print("%s: %s" % (screen, "OK" if not bad else "проблем после %d действий" % bad))
    win.close()
    return bad


if __name__ == "__main__":
    screens = sys.argv[1:] or SCREENS
    total = sum(check(s) for s in screens)
    sys.exit(1 if total else 0)
