import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.physics import R_MAX, R_MIN, radius_for_mass  # noqa: E402
from model.stats import TimeSeries  # noqa: E402


def test_time_series_keeps_whole_history():
    ts = TimeSeries(size=100)
    for k in range(1000):
        ts.add(float(k), float(k) * 2)
    t, v = ts.data()
    assert t[0] == 0.0 and t[-1] == 999.0
    assert len(t) <= 101
    assert np.all(np.diff(t) > 0)
    assert np.allclose(v, 2 * t)
    assert ts.last() == (999.0, 1998.0) and ts.count == 1000


def test_radius_grows_with_mass_within_bounds():
    masses = np.array([1, 4, 28, 100, 200, 500])
    r = radius_for_mass(masses)
    assert np.isclose(r[0], R_MIN) and np.isclose(r[4], R_MAX) and np.isclose(r[5], R_MAX)
    assert np.all(np.diff(r[:5]) > 0)
    # отношение радиусов = корень кубический из отношения масс
    assert np.isclose(r[2] / r[1], (28 / 4) ** (1 / 3))


def test_lazy_forgetting_matches_explicit():
    """Ленивое забывание (растущий вес новых отсчётов) даёт то же, что умножение старых на factor."""
    from model.stats import Histogram
    rng = np.random.default_rng(1)
    h = Histogram(0, 10, bins=20)
    h.RENORMALIZE_AT = 1e6  # чтобы в тесте сработала и перенормировка
    counts, total, s = np.zeros(20), 0.0, 0.0
    for _ in range(3000):
        x = rng.uniform(0, 10)
        h.forget(0.99)
        counts *= 0.99
        total *= 0.99
        s *= 0.99
        h.add(x)
        counts[int(x / 0.5)] += 1
        total += 1
        s += x
    assert np.allclose(h.counts, counts) and np.isclose(h.total, total) and np.isclose(h.mean(), s / total)
    h.add(rng.uniform(0, 10, 500))  # массив значений
    assert np.isclose(np.sum(h.density()) * h.width, 1.0)


def test_rebin_keeps_samples():
    from model.stats import Histogram
    h = Histogram(0, 10, bins=20)
    h.add(np.random.default_rng(2).uniform(2, 8, 1000))
    mean, total = h.mean(), h.total
    h.rebin(0, 20)
    assert np.isclose(h.total, total) and np.isclose(h.mean(), mean)
    assert np.isclose(h.counts.sum(), total)  # всё попало в новый диапазон
    assert np.isclose(h.edges[-1], 20)


def test_rebin_to_other_bin_count():
    from model.stats import Histogram
    h = Histogram(0, 10, bins=30)
    h.add(np.random.default_rng(3).uniform(0, 10, 3000))
    total = h.total
    h.rebin(0, 10, bins=10)
    assert len(h.counts) == 10 and np.isclose(h.counts.sum(), total)
    assert np.isclose(np.sum(h.density()) * h.width, 1.0)
    # Мельче: веса делятся пропорционально перекрытию — без пустых "через один" столбиков
    h.rebin(0, 10, bins=40)
    assert np.isclose(h.counts.sum(), total) and np.all(h.counts > 0)


def test_history_compaction_preserves_peaks_and_moments():
    ts = TimeSeries(size=16)
    values = np.zeros(1003)
    values[11], values[97], values[998] = 10000, -3000, 75
    for t, v in enumerate(values):
        ts.add(t, v)
    b = np.array(ts.buckets)
    assert len(b) <= 16
    assert b[:, 2].min() == values.min()
    assert b[:, 3].max() == values.max()
    assert b[:, 5].sum() == len(values)
    assert np.isclose(b[:, 6].sum(), values.sum())
    assert np.isclose(b[:, 7].sum(), np.square(values).sum())
    assert b[0, 0] == 0 and b[-1, 1] == len(values)-1


def test_budgeted_steps_do_not_skip_physics_or_samples(monkeypatch):
    from types import SimpleNamespace
    from model import experiment
    exp = experiment.Experiment(seed=73)
    exp.configure_gas('pure', 28, 28, 2, 1, collisions=False)
    clock = [0.]
    step = exp.gas.step

    def slow_step(dt=None):
        step(dt)
        clock[0] += .004

    monkeypatch.setattr(exp.gas, 'step', slow_step)
    monkeypatch.setattr(experiment, 'time', SimpleNamespace(perf_counter=lambda: clock[0]))
    dt = exp.gas.dt
    exp.advance_by(25., seconds=.008)
    assert exp.steps_since_reset == 2
    assert np.isclose(exp.gas.time, 2 * dt)
    assert all(series.count == 2 for series in exp.series.values())
    assert all(np.isclose(hist.total, exp.hist['pair', 'modulus'].total)
               for hist in exp.hist.values())
    exp.advance_for_seconds(.008)
    assert exp.steps_since_reset == 4
    assert np.isclose(exp.gas.time, 4 * dt)


def test_history_summary_preserves_weights_peaks_and_partial_tail():
    ts = TimeSeries(size=32)
    values = np.linspace(-20, 80, 1003)
    values[17], values[998] = 9000., -6000.
    times = np.cumsum(np.linspace(.01, .1, len(values)))
    for t, v in zip(times, values):
        ts.add(float(t), float(v))
    for limit in (1, 3, 16, 100):
        b = ts.summary(limit)
        assert len(b) <= limit
        assert b[0, 0] == times[0] and b[-1, 1] == times[-1]
        assert b[:, 2].min() == values.min() and b[:, 3].max() == values.max()
        assert b[-1, 4] == values[-1]
        assert b[:, 5].sum() == len(values)
        assert np.isclose(b[:, 6].sum(), values.sum())
        assert np.isclose(b[:, 7].sum(), np.square(values).sum())
        mean = b[:, 6].sum() / b[:, 5].sum()
        variance = b[:, 7].sum() / b[:, 5].sum() - mean**2
        assert np.isclose(mean, values.mean())
        assert np.isclose(variance, values.var())


def test_history_stays_bounded_after_a_million_measurements():
    import settings
    ts = TimeSeries()
    values = np.arange(1000003, dtype=float) % 101 - 50
    values[999991] = 12345.
    for t, v in enumerate(values):
        ts.add(t, float(v))
    assert len(ts.buckets) <= settings.HISTORY_BUCKETS
    b = ts.summary(settings.HISTORY_PLOT_POINTS)
    assert len(b) <= settings.HISTORY_PLOT_POINTS
    assert ts.count == len(values) and b[:, 5].sum() == len(values)
    assert b[:, 2].min() == values.min() and b[:, 3].max() == values.max()
    assert b[:, 6].sum() == values.sum()
    assert b[:, 7].sum() == np.square(values).sum()
    assert ts.first() == (0, values[0]) and ts.last() == (len(values)-1, values[-1])
    ts.reset()
    assert ts.summary(10).shape == (0, 8)
