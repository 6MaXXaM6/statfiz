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
    assert "3kT/2" in sources and "374" in sources
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
