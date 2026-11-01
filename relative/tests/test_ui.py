"""Проверки перенесённых сценариев C++ без окна на экране."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from PyQt5 import QtWidgets  # noqa: E402
from main import MainWindow  # noqa: E402
from model import theory as tf  # noqa: E402
from ui import style  # noqa: E402


@pytest.fixture(scope="module")
def app():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    os.environ["RELATIVE_SCREEN"] = "1024x768"
    style.init_style(app)
    yield app


def test_demo_controls(app):
    win = MainWindow()
    win.resize(1024, 768)
    win.show()
    win.show_demo()
    app.processEvents()
    d = win.demo
    d.run.timer.stop()
    assert len(d.panels) == 2 and d.run.state == "running"
    assert not d.exp.ensemble
    d.run.ensemble_box.click()
    assert d.exp.ensemble
    d.gas.start.buttons["beam"].click()
    assert d.exp.start == "beam" and d.exp.memory_collisions == 3
    assert d.run.speed.value() == 11
    assert np.allclose(d.exp.gas.vel, d.exp.gas.vel[0])
    gas = d.exp.gas
    d.gas.collisions.click()
    assert d.exp.gas is gas and not gas.collisions_enabled
    d.exp.advance(10)
    total = d.exp.hist["pair", tf.MODULUS].total
    d.run.mode.buttons["fast"].click()
    assert d.exp.ensemble and not d.run.ensemble_box.isEnabled()
    assert d.exp.series["pair", tf.MODULUS].count == 0
    assert d.exp.hist["pair", tf.MODULUS].total == total
    d.run.mode.buttons["slow"].click()
    assert d.run.ensemble_box.isEnabled()
    win.show_theory()
    assert d.run.state == "paused"
    win.close()


def test_theory_navigation_and_interactive_examples(app):
    win = MainWindow()
    win.resize(1024,768)
    win.show()
    win.show_theory()
    page = win.theory
    assert page.stack.count() == 8
    for i in range(8):
        page.show_section(i)
        app.processEvents()
        assert page.nav[i].isChecked()
        assert page.back.isEnabled() == (i > 0)
        assert page.next.isEnabled() == (i < 7)
        section = page.stack.widget(i)
        assert section.minimumSizeHint().width() <= page.stack.width()
        if 1 <= i <= 5:
            demo = section.demo
            old = demo.readout.text()
            demo.temperature.spin.setValue(600)
            assert demo.readout.text() != old
            demo.fit_axis()
            demo.reset()
            assert demo.temperature.value() == 300
    energy = page.stack.widget(4).demo
    before = energy.items[1].getData()[1].copy()
    energy.mass_1.spin.setValue(100)
    assert np.array_equal(before,energy.items[1].getData()[1])
    sampling = page.stack.widget(6).demo
    sampling.rng = np.random.default_rng(42)
    sampling.add_samples(10000)
    assert sampling.hist.total == 10000
    assert abs(sampling.hist.mean()/tf.mean(tf.MODULUS,sampling.sigma)-1) < .03
    sampling.reset()
    assert sampling.hist.total == 0
    page.drawer.open()
    page.drawer.slide.setCurrentTime(180)
    assert page.drawer.isVisible()
    page._choose(2)
    page.drawer.slide.setCurrentTime(180)
    assert not page.drawer.isVisible() and page.stack.currentIndex() == 2
    sources = page.stack.widget(7).findChild(QtWidgets.QTextBrowser).toPlainText()
    assert "Пример 8.5" in sources and "95–96" in sources
    assert "Пример 8.6" in sources and "96–97" in sources
    assert "374" in sources
    from pages.theory.formula_browser import FormulaBrowser
    browser = page.stack.widget(7).findChild(FormulaBrowser)
    assert r"\frac{3kT}{2}" in browser.source
    assert browser.formulas
    win.close()


def assert_arrow(arrow, start, vector):
    path = arrow.path()
    if np.linalg.norm(vector) == 0:
        assert path.isEmpty()
        return
    points = np.array([(path.elementAt(i).x, path.elementAt(i).y)
                       for i in range(path.elementCount())])
    np.testing.assert_allclose(points[0], start, atol=1e-10)
    tip = np.asarray(start) + vector
    assert np.any(np.linalg.norm(points - tip, axis=1) < 1e-8)


def make_fixed_demo(app):
    win = MainWindow()
    win.resize(1024, 768)
    win.show()
    win.show_demo()
    win.demo.run.pause()
    d = win.demo
    d.exp.configure_gas("pure", 28, 28, 2, 1, collisions=False)
    d.exp.gas.pos[:] = [[25, 25], [75, 75]]
    d.exp.gas.vel[:] = [[300, 400], [-100, 200]]
    d.exp.reset_stats()
    d.on_experiment_changed()
    app.processEvents()
    return win


def assert_display(d, panel, expected):
    from ui import labels
    kind = panel.quantity[1]
    digits = 1 if kind == tf.ENERGY else 0
    assert panel.value.text() == f"= <b>{style.fmt(expected, digits)}</b> {labels.unit(kind)}"
    np.testing.assert_allclose(panel.hist_plot.current.value(), expected)
    if panel.time_plot.isVisible():
        times, values = panel.time_plot.dot.getData()
        np.testing.assert_allclose(times, [d.exp.gas.time])
        np.testing.assert_allclose(values, [expected])
        np.testing.assert_allclose(panel.time_plot.current.value(), expected)


@pytest.mark.parametrize("velocities", [
    [[3, 4], [-1, 2]], [[300, 400], [-100, 200]],
    [[-300, 400], [100, -200]], [[300, 400], [300, 400]],
])
@pytest.mark.parametrize("obj,kind", [
    ("pair", "modulus"), ("pair", "projection"),
    ("single", "modulus"), ("second", "projection"), ("single", "energy"),
])
def test_frame_synchronizes_arrows_values_time_and_histogram(app, velocities, obj, kind):
    from model.physics import AMU
    from ui.plots.box_view import ARROW_LENGTH
    win = make_fixed_demo(app)
    d = win.demo
    panel = d.panels[0]
    panel.show_quantity(obj, kind)
    d.exp.gas.vel[:] = velocities
    d.exp.reset_stats()
    d.on_experiment_changed()
    # Один настоящий физический шаг без столкновений; позиции далеки от стенок.
    d.on_tick(False, .05)
    v1, v2 = np.asarray(velocities, dtype=float)
    vector = {"pair": v1-v2, "single": v1, "second": v2}[obj]
    expected = (np.linalg.norm(vector) if kind == "modulus" else vector[0]
                if kind == "projection" else .5*28*AMU*np.dot(vector,vector)/1e-21)
    assert_arrow(d.vectors.v1, [0,0], v1)
    assert_arrow(d.vectors.v2, [0,0], v2)
    assert_arrow(d.vectors.rel, v2, v1-v2)
    if kind == "projection":
        assert_arrow(d.vectors.proj, [0,0], [vector[0],0])
    scale = ARROW_LENGTH/d.box.speed_scale
    for i in range(2):
        assert_arrow(d.box.arrows[i], d.exp.gas.pos[i], d.exp.gas.vel[i]*scale)
    assert_display(d, panel, expected)
    assert d.exp.series[obj, kind].last()[1] == pytest.approx(expected)
    hist = d.exp.hist[obj, kind]
    k = hist.bin_of(expected)
    assert k is not None
    assert hist.counts[k] == pytest.approx(1)
    assert panel.hist_plot.flash[k] == 1
    assert np.count_nonzero(panel.hist_plot.flash) == 1
    win.close()


def test_paused_parameter_changes_and_rotation_stay_synchronized(app):
    win = make_fixed_demo(app)
    d = win.demo
    d.on_tick(False, .05)
    panel = d.panels[0]
    d._changed(d.exp.set_temperature, 600)
    expected = np.linalg.norm(d.exp.gas.vel[0]-d.exp.gas.vel[1])
    assert_display(d, panel, expected)
    d._changed(d.exp.set_masses, 56, d.exp.mass_b)
    expected = np.linalg.norm(d.exp.gas.vel[0]-d.exp.gas.vel[1])
    hist = d.exp.hist[panel.quantity]
    total, counts = hist.total, hist.counts.copy()
    assert_display(d, panel, expected)
    assert np.count_nonzero(panel.hist_plot.flash) == 0
    # Изменение параметра не является новым измерением для статистики.
    assert hist.total == 1
    assert d.exp.series[panel.quantity].count == 1
    # Поворот на паузе должен сразу нарисовать столбики, без нового шага.
    panel.rotate()
    app.processEvents()
    assert_display(d, panel, expected)
    np.testing.assert_allclose(panel.hist_plot.bars.opts['height'],
                               np.minimum(hist.density()*panel.hist_plot._density_factor(),panel.hist_plot.top))
    panel.rotate()
    app.processEvents()
    assert_display(d, panel, expected)
    assert hist.total == total
    np.testing.assert_array_equal(hist.counts, counts)
    # Выбор другой молекулы сбрасывает статистику, но текущие величины известны.
    panel.show_quantity("single", "modulus")
    d._changed(d.exp.select, 1, 1)
    assert_display(d, panel, np.linalg.norm(d.exp.gas.vel[1]))
    assert d.exp.hist[panel.quantity].total == 0
    win.close()


def test_fonts_follow_window_without_resetting_experiment(app):
    from PyQt5 import QtCore
    from pages.authors_page import load_authors
    style.init_style(app, QtCore.QSize(1366, 768))
    win = MainWindow()
    win.resize(1366, 768)
    win.show()
    win.show_demo()
    app.processEvents()
    win.demo.run.timer.stop()
    gas = win.demo.exp.gas
    large = win.demo.run.btn_start.font().pixelSize()
    win.resize(1093, 614)  # 1366x768 при масштабе Windows 125%
    win.font_scale.apply()
    app.processEvents()
    assert win.demo.run.btn_start.font().pixelSize() < large
    assert win.demo.exp.gas is gas
    assert win.theory.stack.widget(0).minimumSizeHint().width() <= win.width()
    assert win.demo.minimumSizeHint().height() <= win.height()
    win.resize(1366, 768)
    win.font_scale.apply()
    assert win.demo.run.btn_start.font().pixelSize() == large
    assert load_authors()['authors'][1]['name'] == 'Мухтаров Азамат Фарходович'
    win.close()


def test_axis_captions_stay_inside_small_plot(app):
    from PyQt5 import QtCore
    from ui.plots.base import StaticPlot
    style.init_style(app, QtCore.QSize(1093, 614))
    plot = StaticPlot('f, 10⁻³ с/м', '|v<sub>отн,x</sub>|, м/с')
    plot.resize(260, 180)
    plot.setXRange(0, 3000, padding=0)
    plot.setYRange(-10000, 10000, padding=0)
    plot.show()
    for _ in range(3):
        app.processEvents()
        plot.grab()
    visible = plot.mapToScene(plot.viewport().rect()).boundingRect()
    for name in ('left', 'bottom'):
        axis = plot.getAxis(name)
        assert visible.contains(axis.label.sceneBoundingRect()), name
    plot.close()


def test_fullscreen_round_trip_rescales_layout(app):
    from PyQt5 import QtCore
    from PyQt5.QtTest import QTest
    from tools.layout_check import problems
    style.init_style(app, QtCore.QSize(1093, 614))
    win = MainWindow()
    win.show()
    win.show_demo()
    win.demo.pause()
    gas = win.demo.exp.gas
    for width, height in ((1093, 614), (1920, 1080), (1093, 614), (1366, 768), (1024, 640)):
        win.resize(width, height)
        win.font_scale.apply()
        QTest.qWait(100)
        assert win.size() == QtCore.QSize(width, height)
        assert not problems(win)
        for panel in win.demo.panels:
            assert panel.stats.height() >= 2 * panel.stats.fontMetrics().lineSpacing()
        assert win.demo.exp.gas is gas
    win.demo.zoom_button.click()
    for width, height in ((1920, 1080), (1093, 614)):
        win.resize(width, height)
        win.font_scale.apply()
        QTest.qWait(100)
        assert win.size() == QtCore.QSize(width, height)
        assert not problems(win)
    QTest.keyClick(win, QtCore.Qt.Key_F11)
    QTest.qWait(150)
    assert win.isFullScreen()
    assert not problems(win)
    QTest.keyClick(win, QtCore.Qt.Key_F11)
    QTest.qWait(150)
    assert not win.isFullScreen()
    assert not problems(win)
    win.close()


def test_running_plots_are_throttled_but_pause_refreshes(app, monkeypatch):
    win = make_fixed_demo(app)
    d = win.demo
    calls = []
    original = d.panels[0].refresh
    monkeypatch.setattr(d.panels[0], 'refresh', lambda *args: (calls.append(True), original(*args))[-1])
    d.run.toggle_pause()
    d.on_tick(False, .05)
    d.on_tick(False, .05)
    assert not calls  # статистика записывается, дорогая отрисовка ещё не нужна
    assert d.exp.steps_since_reset == 2
    d.run.pause()
    assert len(calls) == 1
    assert_display(d, d.panels[0], d.exp.current_value(*d.panels[0].quantity))
    win.close()


def test_parameter_changes_coalesce_and_apply_without_old_delay(app, monkeypatch):
    from PyQt5.QtTest import QSignalSpy
    win = make_fixed_demo(app)
    calls = []
    changed = QSignalSpy(win.demo.gas.temperature.changed)
    original = win.demo.exp.set_temperature
    monkeypatch.setattr(win.demo.exp, 'set_temperature', lambda value: (calls.append(value), original(value))[-1])
    for value in (350, 375, 400):
        win.demo.gas.temperature.spin.setValue(value)
    assert not calls
    assert changed.wait(1000)
    assert calls == [400]
    assert win.demo.exp.temperature == 400
    win.close()


def test_long_history_plot_is_bounded_and_not_rebuilt_on_pause(app, monkeypatch):
    import settings
    from model.stats import TimeSeries
    from ui.plots.time_plot import TimePlot
    series = TimeSeries()
    for t in range(20000):
        series.add(t, 9000. if t == 17777 else float(t % 100))
    plot = TimePlot()
    plot.resize(1200, 300)
    plot.show()
    app.processEvents()
    plot.update_view(series)
    assert len(plot.high_edge.xData) <= settings.HISTORY_PLOT_POINTS
    assert max(plot.high_edge.yData) == 9000.
    calls = []
    update = plot.high_edge.setData
    monkeypatch.setattr(plot.high_edge, 'setData', lambda *args: (calls.append(True), update(*args))[-1])
    plot.update_view(series, current=(20000., 250.))
    assert not calls
    assert plot.dot.getData()[1][0] == 250.
    series.add(20001., -500.)
    plot.update_view(series)
    assert len(calls) == 1
    assert min(plot.low_edge.yData) == -500.
    plot.close()
