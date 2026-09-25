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
