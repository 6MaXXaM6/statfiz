"""Перевод единиц не должен менять модель или нормировку вероятности."""
import os
from pathlib import Path
import pickle
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest
from PyQt5 import QtCore, QtTest, QtWidgets

from main import MainWindow
from model import theory as tf
from model.experiment import Experiment
from model.physics import NM_PER_MS_PS
from model.stats import Histogram, TimeSeries
from ui import style, units
from ui.plots.hist_plot import HistPlot
from ui.plots.time_plot import TimePlot


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_conditional_energy_velocity_and_time_are_consistent():
    exp = Experiment(seed=312)
    v = exp.velocity('single')
    speed = np.linalg.norm(v) * units.value_factor(tf.MODULUS)
    energy = exp.current_value('single', tf.ENERGY) * units.value_factor(tf.ENERGY)
    assert energy == pytest.approx(.5 * exp.mass_1 * speed**2)
    dt = .5
    displacement = v * dt * NM_PER_MS_PS
    np.testing.assert_allclose(displacement, v / units.VELOCITY_UNIT * (dt * units.TIME_FACTOR))
    assert tf.mean(tf.ENERGY, exp.scale('single', tf.ENERGY)) * units.ENERGY_FACTOR == pytest.approx(exp.temperature)


@pytest.mark.parametrize('kind', [tf.MODULUS, tf.PROJECTION, tf.ENERGY])
@pytest.mark.parametrize('sideways', [False, True])
def test_probability_density_keeps_area_and_model_data(app, kind, sideways):
    scale = 400. if kind != tf.ENERGY else 4.
    low, high = tf.value_range(kind, scale)
    hist = Histogram(low, high, 20)
    hist.add(hist.centers)
    before = pickle.dumps(hist)
    x = np.linspace(low, high, 500)
    pdf = tf.pdf(kind, x, scale)
    factor = units.value_factor(kind)
    plot = HistPlot(sideways)
    plot.configure('X, у.е.', x, pdf, peak=max(pdf.max(), hist.density().max()),
                   density_unit='у.е.⁻¹', rescale=False, value_factor=factor)
    plot.update_view(hist, current=hist.centers[3])
    assert plot.getAxis('bottom' if sideways else 'left').labelText == ''
    assert np.sum(plot.bars.opts['width'] * plot.bars.opts['height']) == pytest.approx(1.)
    assert np.trapz(plot._curves['pdf'], plot._curves['x']) == pytest.approx(np.trapz(pdf, x))
    assert plot.current.value() == pytest.approx(hist.centers[3] * factor)
    assert pickle.dumps(hist) == before
    plot.close()


@pytest.mark.parametrize('samples', [3, 100])
def test_sparse_and_compacted_history_use_same_units(app, samples):
    series = TimeSeries(size=8)
    for k in range(samples):
        series.add(k*.2, float(k % 9))
    before = pickle.dumps(series)
    factor = units.value_factor(tf.MODULUS)
    plot = TimePlot()
    plot.configure('v, у.е.', 0, 20, factor, units.TIME_FACTOR)
    plot.update_view(series, current=(samples*.2, 12.))
    x, y = plot.dot.getData()
    np.testing.assert_allclose(x, [samples*.2*units.TIME_FACTOR])
    np.testing.assert_allclose(y, [12.*factor])
    assert plot.current.value() == pytest.approx(12.*factor)
    if samples == 3:
        t, v = series.data()
        x, y = plot.curve.getData()
        np.testing.assert_allclose(x, t*units.TIME_FACTOR)
        np.testing.assert_allclose(y, v*factor)
    else:
        summary = series.summary(256)
        _, y = plot.average.getData()
        np.testing.assert_allclose(y, summary[:, 6]/summary[:, 5]*factor)
    # summary() заполняет только кэш: исходные корзины не должны измениться.
    original = pickle.loads(before)
    assert series.buckets == original.buckets and series.count == original.count
    plot.close()


def test_compact_header_defaults_and_controls(app):
    style.init_style(app, QtCore.QSize(1093, 614))
    window = MainWindow()
    window.resize(1093, 614)
    window.show()
    window.show_demo()
    demo = window.demo
    demo.pause()
    QtTest.QTest.qWait(180)
    assert (demo.exp.n_total, demo.exp.bins, demo.exp.memory_collisions) == (15, 20, 200)
    assert demo.exp.n_b_mix == 5
    assert demo.display_button.height() == demo.link_scales.height()
    assert demo.display_button.width() < demo.link_scales.width()
    assert demo.display_button.y() == demo.link_scales.y()
    assert demo.conditions.isAncestorOf(demo.vector_toggle)
    toggles = (demo.gas.collisions, demo.run.ensemble_box, demo.vector_toggle)
    assert all(isinstance(toggle, QtWidgets.QCheckBox) for toggle in toggles)
    assert len({toggle.font().pixelSize() for toggle in toggles}) == 1
    assert demo.run_card.y() - demo.box_card.geometry().bottom() - 1 == demo.left.layout().spacing()
    assert demo.run_card.geometry().bottom() == demo.left.height() - 1
    assert all('Мгновенные' not in action.text() for action in demo.display_button.menu().actions())
    for panel in demo.panels:
        assert not hasattr(panel, 'value')
        assert '<br>' not in panel.stats.text()
        assert not any(label.text().startswith('График ') for label in panel.header.findChildren(QtWidgets.QLabel))
        assert abs(panel.selector.geometry().center().y() - panel.stats.geometry().center().y()) <= 1
    assert '√2' in demo.ratio.text()
    demo.panels[1].show_quantity('single', 'energy')
    assert demo.ratio.text() == ''
    window.close()
