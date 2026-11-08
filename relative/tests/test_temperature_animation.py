"""Температура меняет движение и стрелки; кадр не теряет время при дроблении."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest
from PyQt5 import QtCore, QtGui, QtTest, QtWidgets
import settings
from model import experiment
from model.experiment import Experiment
from model.physics import K_B
from pages.demo.page import DemoPage
from ui import style


@pytest.fixture(scope='module')
def app():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    style.init_style(app)
    return app


@pytest.fixture
def demo(app):
    page = DemoPage(lambda: None, lambda: None)
    page.run.start()
    page.run.timer.stop()
    yield page
    page.run.pause()
    page.close()


def prepare(page, temperature, mixture=False, start='maxwell'):
    exp = Experiment(seed=81)
    exp.configure_gas('mix' if mixture else 'pure', 200 if mixture else 28,
                      1 if mixture else 4, 4 if mixture else 2, 2 if mixture else 1,
                      start=start, collisions=False)
    if mixture:
        exp.choose_pair('AB')
    exp.set_temperature(temperature)
    exp.gas.pos[:] = np.array([[25.,25.],[75.,25.],[25.,75.],[75.,75.]])[:exp.gas.n]
    page.exp = exp
    page.on_experiment_changed()
    return exp


@pytest.mark.parametrize('fast', [False, True])
@pytest.mark.parametrize('mixture', [False, True])
@pytest.mark.parametrize('start', ['maxwell', 'beam'])
def test_whole_frames_keep_physical_time_and_temperature_even_across_cpu_batches(demo, monkeypatch, fast, mixture, start):
    shifts, lengths, times = [], [], []
    for temperature in (50, 300, 1200, 1500):
        exp = prepare(demo, temperature, mixture, start)
        exp.ensemble = fast
        initial = exp.gas.pos.copy()
        scale = demo.box.speed_scale
        lengths.append(np.linalg.norm(exp.gas.vel[exp.i]) / scale)
        expected = exp.frame_duration(settings.FAST_FRAME_FACTOR if fast else 5.)
        clock, steps = [0.], []
        step = exp.gas.step

        def costly_step(dt=None):
            steps.append(dt)
            step(dt)
            clock[0] += .004

        with monkeypatch.context() as patch:
            patch.setattr(exp.gas, 'step', costly_step)
            patch.setattr(experiment, 'time', SimpleNamespace(perf_counter=lambda: clock[0]))
            demo.on_tick(fast, 5.)
            batches = 1
            while demo._frame_remaining is not None:
                assert not demo.run.timer.isActive()
                before = len(steps)
                demo._continue_frame()
                assert len(steps) - before <= 2
                batches += 1
                assert batches < 500
        assert not demo._frame_timer.isActive()
        assert demo.run.timer.isActive()
        demo.run.timer.stop()
        assert exp.gas.time == pytest.approx(expected, rel=1e-12)
        assert sum(steps) == pytest.approx(expected, rel=1e-12)
        assert max(steps) <= exp.gas.dt * (1 + 1e-12)
        assert all(s.count == len(steps) for s in exp.series.values())
        shifts.append(exp.gas.pos - initial)
        times.append(exp.gas.time)
    np.testing.assert_allclose(times, times[0], rtol=1e-12)
    for index, temperature in enumerate((50, 300, 1200, 1500)):
        ratio = (temperature / 50.)**.5
        np.testing.assert_allclose(shifts[index], shifts[0] * ratio, rtol=1e-10, atol=1e-11)
        assert lengths[index] == pytest.approx(lengths[0] * ratio)


@pytest.mark.parametrize('action', ['pause', 'stop', 'temperature', 'mass', 'mode', 'restart', 'tempo', 'hide'])
def test_pending_frame_is_cancelled_without_late_motion(demo, monkeypatch, action):
    exp = prepare(demo, 1500)
    clock = [0.]
    step = exp.gas.step

    def costly_step(dt=None):
        step(dt)
        clock[0] += .009

    monkeypatch.setattr(exp.gas, 'step', costly_step)
    monkeypatch.setattr(experiment, 'time', SimpleNamespace(perf_counter=lambda: clock[0]))
    demo.on_tick(True, 1.)
    assert demo._frame_remaining > 0
    assert demo._frame_timer.isActive()
    if action == 'pause':
        demo.run.pause()
    elif action == 'stop':
        demo.run.stop()
    elif action == 'temperature':
        demo._changed(exp.set_temperature, 50)
    elif action == 'mass':
        demo._changed(exp.set_masses, 56, 4)
    elif action == 'mode':
        demo.run.mode.buttons['fast'].click()
    elif action == 'restart':
        demo.on_start()
    elif action == 'tempo':
        demo.run.speed.changed.emit(3)
    else:
        demo.hideEvent(QtGui.QHideEvent())
    assert demo._frame_remaining is None
    assert not demo._frame_timer.isActive()
    demo.run.timer.stop()
    position = demo.exp.gas.pos.copy()
    time = demo.exp.gas.time
    count = demo.exp.steps_since_reset
    demo._continue_frame()  # даже запоздалый callback ничего не меняет
    if action in ('pause', 'stop', 'hide'):
        demo.run._on_timer()
    QtTest.QTest.qWait(10)
    np.testing.assert_array_equal(demo.exp.gas.pos, position)
    assert demo.exp.gas.time == time and demo.exp.steps_since_reset == count


def test_real_event_loop_remains_responsive_during_hot_fast_frame(demo, app, monkeypatch):
    exp = Experiment(seed=17)
    exp.configure_gas('mix', 200, 1, 300, 150)
    exp.set_temperature(1500)
    exp.ensemble = True
    demo.exp = exp
    demo.on_experiment_changed()
    done, events = [], []
    original = demo.run.finish_frame

    def finish():
        original()
        demo.run.timer.stop()
        done.append(True)

    monkeypatch.setattr(demo.run, 'finish_frame', finish)
    monkeypatch.setattr(settings, "FAST_FRAME_FACTOR", 5.)
    monkeypatch.setattr(sys.modules[DemoPage.__module__], "FAST_BUDGET", 0.)
    expected = exp.frame_duration(settings.FAST_FRAME_FACTOR)
    demo.on_tick(True, 1.)
    QtCore.QTimer.singleShot(0, lambda: events.append(not done))
    elapsed = QtCore.QElapsedTimer()
    elapsed.start()
    while not done and elapsed.elapsed() < 3000:
        QtTest.QTest.qWait(5)
    assert done and events == [True]
    assert exp.gas.time == pytest.approx(expected, rel=1e-12)
    assert exp.gas.kinetic_energy() == pytest.approx(exp.gas.n * K_B * 1500, rel=1e-9, abs=0)


@pytest.mark.parametrize('temperature', [50, 300, 1500])
@pytest.mark.parametrize('mixture', [False, True])
def test_frame_energy_and_steps_at_extremes(temperature, mixture):
    exp = Experiment(seed=33)
    exp.configure_gas('mix' if mixture else 'pure', 200 if mixture else 1, 1, 300, 150)
    exp.set_temperature(temperature)
    start_dt = exp.gas.dt
    duration = exp.frame_duration(25.)
    for _ in range(10):
        assert exp.advance_duration(duration) == 0
    assert exp.gas.dt == start_dt
    assert exp.gas.time == pytest.approx(10*duration, rel=1e-11)
    assert exp.gas.kinetic_energy() == pytest.approx(exp.gas.n*K_B*temperature, rel=1e-9, abs=0)
    assert np.isfinite(exp.gas.pos).all() and np.isfinite(exp.gas.vel).all()


def test_heating_and_cooling_on_pause_preserve_positions_and_statistics(demo):
    exp = prepare(demo, 300)
    demo.run.pause()
    exp.advance(12)
    position, velocity = exp.gas.pos.copy(), exp.gas.vel.copy()
    counts = {k: s.count for k,s in exp.series.items()}
    totals = {k: h.total for k,h in exp.hist.items()}
    for temperature in (1500, 50, 300):
        demo._changed(exp.set_temperature, temperature)
        np.testing.assert_array_equal(exp.gas.pos, position)
        np.testing.assert_allclose(exp.gas.vel, velocity * (temperature/300.)**.5, rtol=1e-12)
        assert {k:s.count for k,s in exp.series.items()} == counts
        assert {k:h.total for k,h in exp.hist.items()} == totals
        assert not demo.run.timer.isActive() and not demo._frame_timer.isActive()
