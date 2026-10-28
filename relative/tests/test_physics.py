import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model import theory as tf  # noqa: E402
from model.physics import AMU, K_B, Gas  # noqa: E402
from model.stats import Histogram  # noqa: E402



def assert_energy_close(actual, expected, rtol=1e-12):
    """Относительный допуск: абсолютный 1e-8 Дж здесь был бы огромным."""
    assert expected > 0
    np.testing.assert_allclose(actual, expected, rtol=rtol, atol=0)


def assert_momentum_close(actual, expected, scale, rtol=1e-12):
    """Масштаб — сумма |p_i| до удара, даже если полный импульс равен нулю."""
    assert scale > 0
    error = np.linalg.norm(np.asarray(actual) - expected) / scale
    assert np.isfinite(error) and error <= rtol, f"относительная ошибка импульса {error}"


@pytest.mark.parametrize("factor", [0, 2, 1.001])
def test_energy_check_rejects_corruption(factor):
    energy = 1e-19
    with pytest.raises(AssertionError):
        assert_energy_close(factor * energy, energy)


@pytest.mark.parametrize("initial", [[0., 0.], [1e-23, -2e-23]])
def test_momentum_check_rejects_corruption(initial):
    scale = 1e-22
    with pytest.raises(AssertionError):
        assert_momentum_close(np.asarray(initial) + [scale * .01, 0], initial, scale)

def test_initial_energy_matches_temperature():
    gas = Gas(200, 50, 28, 4, 300, seed=1)
    assert_energy_close(gas.kinetic_energy(), gas.n * K_B * 300)


@pytest.mark.parametrize("zero_momentum", [False, True])
def test_collision_conserves_energy_and_momentum(zero_momentum):
    gas = Gas(2, 0, 10, 10, 300, seed=2)
    gas.mass[:] = [10.0, 40.0]
    gas.pos[:] = [[50.0, 50.0], [51.5, 50.3]]  # диски перекрываются
    gas.vel[:] = [[500.0, 100.0], [-300.0, 0.0]]
    if zero_momentum:
        gas.vel[:] = [[500., 100.], [-125., -25.]]
    scale = np.sum(gas.mass * AMU * np.linalg.norm(gas.vel, axis=1))
    e0, p0 = gas.kinetic_energy(), gas.momentum()
    gas._collide()
    assert gas.collisions == 1
    assert_energy_close(gas.kinetic_energy(), e0)
    assert_momentum_close(gas.momentum(), p0, scale)


def test_energy_conserved_over_many_steps():
    gas = Gas(150, 20, 20, 80, 400, seed=3)
    e0 = gas.kinetic_energy()
    for _ in range(2000):
        gas.step()
    assert_energy_close(gas.kinetic_energy(), e0, rtol=1e-9)
    assert np.all(gas.pos >= 0) and np.all(gas.pos <= gas.box)


def _equilibrated_samples(n_a, n_b, m_a, m_b, T, steps=3000, seed=4):
    gas = Gas(n_a, n_b, m_a, m_b, T, seed=seed)
    for _ in range(1500):  # установление равновесия
        gas.step()
    rng = np.random.default_rng(seed)
    a = gas.indices_of(0)
    b = gas.indices_of(1)
    speed_a, rel_aa, rel_ab, vx_a = [], [], [], []
    for k in range(steps):
        gas.step()
        if k % 10:
            continue
        speed_a.append(np.hypot(*gas.vel[a].T))
        vx_a.append(gas.vel[a, 0])
        i, j = rng.choice(a, size=(2, 100))
        ok = i != j
        rel_aa.append(np.hypot(*(gas.vel[i[ok]] - gas.vel[j[ok]]).T))
        if len(b):
            i = rng.choice(a, size=100)
            j = rng.choice(b, size=100)
            rel_ab.append(np.hypot(*(gas.vel[i] - gas.vel[j]).T))
    cat = lambda x: np.concatenate(x) if x else np.array([])  # noqa: E731
    return gas, cat(speed_a), cat(rel_aa), cat(rel_ab), cat(vx_a)


def test_relative_speed_is_sqrt2_larger():
    gas, speed, rel, _, vx = _equilibrated_samples(250, 0, 30, 30, 300)
    ratio = rel.mean() / speed.mean()
    assert abs(ratio - np.sqrt(2)) < 0.04 * np.sqrt(2)
    sigma = tf.sigma_for(30, 300)
    assert abs(speed.mean() - tf.mean(tf.MODULUS, sigma)) < 0.03 * speed.mean()
    assert abs(vx.var() - K_B * 300 / (30 * AMU)) < 0.05 * vx.var()


def test_mixture_uses_reduced_mass():
    _, _, _, rel_ab, _ = _equilibrated_samples(200, 60, 10, 90, 300)
    mu = tf.reduced_mass(10, 90)
    expected = tf.mean(tf.MODULUS, tf.sigma_for(mu, 300))
    assert abs(rel_ab.mean() - expected) < 0.05 * expected


def test_histogram_density_normalised():
    h = Histogram(0, 10, bins=20)
    h.add(np.random.default_rng(0).uniform(0, 10, 10000))
    assert np.isclose(np.sum(h.density()) * h.width, 1.0)
    assert h.bin_of(0.1) == 0 and h.bin_of(9.99) == 19 and h.bin_of(11) is None


def test_energy_pdf_is_normalised():
    kt = 4.14
    e = np.linspace(0, 60 * kt, 200001)
    for kind, x, s in ((tf.ENERGY, e, kt), (tf.MODULUS, np.linspace(0, 3000, 200001), 400.0)):
        assert np.isclose(np.trapz(tf.pdf(kind, x, s), x), 1.0, atol=1e-3)
    assert tf.mean(tf.ENERGY, kt) == kt and tf.variance(tf.ENERGY, kt) == kt ** 2


def test_mean_energy_is_kT_in_equilibrium():
    """В двумерном газе средняя кинетическая энергия молекулы равна kT (две степени свободы)."""
    from model.experiment import ENERGY_UNIT, SINGLE, Experiment
    exp = Experiment(seed=5)
    exp.ensemble = True
    exp.advance(3000)
    hist = exp.hist[SINGLE, tf.ENERGY]
    kt = K_B * exp.temperature / ENERGY_UNIT
    assert np.isclose(exp.scale(SINGLE, tf.ENERGY), kt)
    assert abs(hist.mean() - kt) < 0.05 * kt


def test_temperature_and_mass_change_keep_statistics():
    """Температура и массы меняются без сброса статистики; газ остаётся тем же."""
    from model.experiment import PAIR, Experiment
    exp = Experiment(seed=7)
    exp.advance(500)
    hist = exp.hist[PAIR, tf.MODULUS]
    total = hist.total
    gas = exp.gas
    exp.set_temperature(600)
    assert exp.gas is gas and np.isclose(hist.total, total)
    assert np.isclose(hist.edges[-1], exp.value_range(tf.MODULUS, PAIR)[1])
    assert_energy_close(gas.kinetic_energy(), gas.n * K_B * 600)

    energy_before = 0.5 * gas.mass * np.sum(gas.vel ** 2, axis=1)
    exp.configure_gas(exp.gas_mode, 4, exp.mass_b, exp.n_total, exp.n_b_mix)  # только масса A
    assert exp.gas is gas and exp.hist[PAIR, tf.MODULUS] is hist
    assert np.allclose(0.5 * gas.mass * np.sum(gas.vel ** 2, axis=1), energy_before)  # T сохранилась
    assert np.allclose(gas.mass, 4) and len(gas.find_close_pairs()[0]) == 0  # перекрытий нет

    exp.configure_gas(exp.gas_mode, 4, exp.mass_b, 100, exp.n_b_mix)  # другое число молекул — новый газ
    assert exp.gas is not gas and exp.hist[PAIR, tf.MODULUS].total == 0


def test_memory_setting_keeps_statistics():
    from model.experiment import PAIR, Experiment
    exp = Experiment(seed=8)
    exp.advance(300)
    hist = exp.hist[PAIR, tf.MODULUS]
    total, tau = hist.total, exp.memory_time
    exp.set_memory(30)
    assert np.isclose(hist.total, total) and np.isclose(exp.memory_time, tau / 10)


def test_beam_relaxes_only_with_collisions():
    gas = Gas(150, 0, 28, 28, 300, seed=11, start="beam")
    speed0 = np.linalg.norm(gas.vel, axis=1)
    assert np.allclose(gas.vel, gas.vel[0])
    assert_energy_close(gas.kinetic_energy(), gas.n*K_B*300)
    walls = Gas(150, 0, 28, 28, 300, seed=11, start="beam", collisions=False)
    for _ in range(3000):
        walls.step()
    assert np.allclose(np.linalg.norm(walls.vel, axis=1), speed0)
    assert walls.collisions == 0
    for _ in range(6000):
        gas.step()
    samples = []
    for step in range(3000):
        gas.step()
        if step % 50 == 0:
            samples.extend(np.linalg.norm(gas.vel, axis=1))
    sigma = tf.sigma_for(28, 300)
    assert np.isclose(np.mean(samples), tf.mean(tf.MODULUS, sigma), rtol=.05)
    assert np.isclose(np.var(samples), tf.variance(tf.MODULUS, sigma), rtol=.15)


def test_collision_toggle_and_history_restart_preserve_statistics():
    from model.experiment import Experiment, PAIR
    exp = Experiment(seed=9)
    exp.advance(100)
    hist = exp.hist[PAIR, tf.MODULUS]
    total, mean = hist.total, hist.mean()
    gas = exp.gas
    exp.configure_gas(exp.gas_mode, exp.mass_a, exp.mass_b, exp.n_total, exp.n_b_mix,
                      collisions=False)
    assert exp.gas is gas and not gas.collisions_enabled
    exp.restart_history()
    assert exp.series[PAIR, tf.MODULUS].count == 0
    assert hist.total == total and hist.mean() == mean
