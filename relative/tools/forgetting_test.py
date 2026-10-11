"""
Статистический тест для выбора коэффициента забывания гистограмм.

Статистика забывается экспоненциально: вес отсчёта, сделанного время t назад,
равен exp(-t/tau), tau = K · tau_coll (tau_coll — среднее время между столкновениями).
Маленькое K — гистограмма шумит; большое K — долго "помнит" старое.

Мера качества — расстояние L1 между гистограммой и теорией:
    L1 = sum |p_опыт - p_теор| по столбикам (0 — совпадение, 2 — ничего общего).

1. Проверяем формулу tau_coll (Gas.collision_time) по реальной модели.
2. Для многих K считаем L1 на "суррогатной" модели: скорости двух молекул
   обновляются в случайные моменты столкновений (поток Пуассона с частотой 1/tau_coll)
   и берутся из распределения Максвелла. Это быстро и позволяет усреднить по многим проверкам.
3. Для малых K сверяем суррогат с настоящей моделью газа.

Запуск: python tools/forgetting_test.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from model import theory as tf  # noqa: E402
from model.experiment import HIST_BINS, PAIR, Experiment  # noqa: E402
from model.stats import Histogram  # noqa: E402

K_GRID = [30, 50, 100, 200, 300, 500, 1000, 2000]


def theory_probabilities(hist, sigma):
    """Теоретическая вероятность попасть в каждый столбик (модуль скорости, 2D)."""
    cdf = 1 - np.exp(-hist.edges ** 2 / (2 * sigma ** 2))
    return np.diff(cdf)


def l1(hist, p_theory):
    if hist.total <= 0:
        return 2.0
    return float(np.abs(hist.counts / hist.total - p_theory).sum())


def check_collision_time():
    exp = Experiment(seed=1)
    gas = exp.gas
    for _ in range(3000):
        gas.step()
    c0, t0 = gas.collisions, gas.time
    for _ in range(20000):
        gas.step()
    measured = gas.n * (gas.time - t0) / (2 * (gas.collisions - c0))  # каждое столкновение — у двух молекул
    predicted = gas.collision_time(0)
    print("1. Время между столкновениями: модель %.1f пс, формула %.1f пс (расхождение %+.0f%%)"
          % (measured, predicted, 100 * (predicted / measured - 1)))


def surrogate_l1(k, checks=300, seed=0):
    """L1 для |v_отн| на суррогатной модели; время — в единицах tau_coll."""
    rng = np.random.default_rng(seed)
    sigma_rel = np.sqrt(2.0)  # sigma = 1 для одной молекулы, sqrt(2) для относительной скорости
    hist = Histogram(*tf.value_range(tf.MODULUS, sigma_rel), bins=HIST_BINS)
    p_theory = theory_probabilities(hist, sigma_rel)
    v = rng.normal(size=(2, 2))
    t, tau = 0.0, float(k)
    next_check, results = 5 * tau, []
    while len(results) < checks:
        dt = rng.exponential(0.5)  # столкновение одной из двух молекул: частота 2/tau_coll
        # Значение было постоянным всё время dt: его вес — интеграл exp(-s/tau) по отрезку.
        hist.forget(np.exp(-dt / tau))
        value = np.hypot(*(v[0] - v[1]))
        weight = tau * (1 - np.exp(-dt / tau))
        hist.add(value, weight=weight)
        t += dt
        v[rng.integers(2)] = rng.normal(size=2)
        if t >= next_check:
            results.append(l1(hist, p_theory))
            next_check += tau / 2
    return np.array(results)


def real_l1(k, checks=40):
    """L1 для |v_отн| на настоящей модели газа (медленно — только для малых K)."""
    exp = Experiment(seed=2)
    exp.memory_collisions = k
    exp.reset_stats()
    hist = exp.hist[PAIR, tf.MODULUS]
    p_theory = theory_probabilities(hist, exp.sigma(PAIR))
    steps_per_tau = int(exp.memory_time / exp.gas.dt)
    exp.advance(5 * steps_per_tau)
    results = []
    for _ in range(checks):
        exp.advance(steps_per_tau // 2)
        results.append(l1(hist, p_theory))
    return np.array(results)


def main():
    check_collision_time()
    print("\n2. Суррогатная модель, |v_отн|, %d столбиков:" % HIST_BINS)
    print("     K   медиана L1   90%% L1   память tau (при 300 К, N2, N=150)")
    tau_coll = Experiment(seed=1).gas.collision_time(0)
    table = {}
    for k in K_GRID:
        r = surrogate_l1(k)
        table[k] = r
        print("  %5d     %.3f      %.3f     %.0f пс" % (k, np.median(r), np.percentile(r, 90), k * tau_coll))
    print("\n3. Проверка суррогата на настоящем газе:")
    for k in (30, 100):
        r = real_l1(k)
        print("  K=%d: газ медиана %.3f, суррогат %.3f" % (k, np.median(r), np.median(table[k])))


if __name__ == "__main__":
    main()
