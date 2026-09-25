"""
Эксперимент: газ + выбранные молекулы + накопленная статистика.
Здесь нет ничего про интерфейс — только логика, которую показывает страница демонстрации.
"""

import math
import time

import numpy as np

from model import theory as tf
from model.physics import MAX_PARTICLES, Gas
from model.stats import Histogram, TimeSeries

# Что наблюдаем
SINGLE = "single"  # молекула 1
SECOND = "second"  # молекула 2
PAIR = "pair"      # относительная скорость молекул 1 и 2: v_отн = v1 - v2
OBJECTS = (PAIR, SINGLE, SECOND)

# Состав газа
GAS_PURE = "pure"  # только газ A
GAS_MIX = "mix"    # смесь газов A и B (при N_B = 1 — одна "чужая" молекула в газе A)

HIST_BINS = 30
ENSEMBLE_EVERY = 10  # как часто (в шагах) добавлять статистику по всем молекулам

# Память статистики: старые отсчёты забываются экспоненциально, exp(-t/tau),
# tau = MEMORY_COLLISIONS средних времён между столкновениями молекулы 1.
# Подобрано тестом tools/forgetting_test.py: расстояние L1 между гистограммой |v_отн|
# (30 столбиков) и теорией — медиана 0.26 при K=100, 0.15 при K=300, 0.08 при K=1000.
# K=300 — шум уже мал, а память ещё короткая (~7.6 нс при 300 К: ~40 с быстрого режима).
MEMORY_COLLISIONS = 300


class Experiment:
    def __init__(self, seed=None):
        self.rng = np.random.default_rng(seed)
        # Параметры, которые меняет пользователь
        self.n_total = 150
        self.gas_mode = GAS_PURE
        self.n_b_mix = 50
        self.mass_a = 28     # а.е.м. (азот)
        self.mass_b = 4      # а.е.м. (гелий)
        self.temperature = 300
        self.pair_type = "AA"
        self.ensemble = False  # добавлять ли статистику по всем молекулам (быстрый режим)
        self.memory_collisions = MEMORY_COLLISIONS
        self.rebuild()

    # ------------------------------------------------------------------
    # Состав газа и выбор молекул
    # ------------------------------------------------------------------
    def n_b(self):
        if self.gas_mode == GAS_PURE:
            return 0
        return int(min(max(self.n_b_mix, 1), self.n_total - 1))

    def configure_gas(self, gas_mode, mass_a, mass_b, n_total, n_b):
        """Новый состав газа (газ создаётся заново)."""
        self.gas_mode = gas_mode
        self.mass_a = mass_a
        self.mass_b = mass_b
        self.n_total = n_total
        self.n_b_mix = n_b
        self.rebuild()

    def rebuild(self):
        """Создаёт газ заново с текущими параметрами."""
        n_total = int(min(max(self.n_total, 2), MAX_PARTICLES))
        n_b = self.n_b()
        self.gas = Gas(n_total - n_b, n_b, self.mass_a, self.mass_b, self.temperature,
                       seed=int(self.rng.integers(1 << 31)))
        if self.pair_type not in self.available_pair_types():
            self.pair_type = self.available_pair_types()[0]
        self.choose_pair(self.pair_type)

    def available_pair_types(self):
        n_a, n_b = self.gas.n_a, self.gas.n_b
        types = []
        if n_a >= 2:
            types.append("AA")
        if n_a >= 1 and n_b >= 1:
            types.append("AB")
        if n_b >= 2:
            types.append("BB")
        return types

    def choose_pair(self, pair_type):
        """Выбирает пару молекул нужных сортов (первые по списку)."""
        a = self.gas.indices_of(0)
        b = self.gas.indices_of(1)
        if pair_type == "AB":
            self.i, self.j = int(a[0]), int(b[0])
        elif pair_type == "BB":
            self.i, self.j = int(b[0]), int(b[1])
        else:
            self.i, self.j = int(a[0]), int(a[1])
        self.pair_type = pair_type
        self.reset_stats()

    def select(self, index, which):
        """Пользователь щёлкнул по молекуле: which = 1 или 2."""
        if which == 1:
            if index == self.j:
                self.j = self.i
            self.i = index
        else:
            if index == self.i:
                self.i = self.j
            self.j = index
        names = "AB"
        self.pair_type = "".join(sorted(names[self.gas.species[self.i]] + names[self.gas.species[self.j]]))
        self.reset_stats()

    def set_temperature(self, temperature):
        self.temperature = temperature
        self.gas.set_temperature(temperature)
        self.reset_stats()

    # ------------------------------------------------------------------
    # Теория для выбранных молекул
    # ------------------------------------------------------------------
    @property
    def mass_1(self):
        return float(self.gas.mass[self.i])

    @property
    def mass_2(self):
        return float(self.gas.mass[self.j])

    @property
    def reduced_mass(self):
        return tf.reduced_mass(self.mass_1, self.mass_2)

    def mass(self, obj):
        """Масса, которая входит в распределение: m1, m2 или приведённая масса пары."""
        return {SINGLE: self.mass_1, SECOND: self.mass_2, PAIR: self.reduced_mass}[obj]

    def sigma(self, obj):
        """sqrt(kT/m) для молекулы или sqrt(kT/mu) для пары, м/с."""
        return tf.sigma_for(self.mass(obj), self.temperature)

    def value_range(self, kind, obj):
        return tf.value_range(kind, self.sigma(obj))

    def max_speed_scale(self):
        """Наибольшее из sqrt(kT/m) для векторов v1, v2 и v_отн на диаграмме."""
        return max(self.sigma(obj) for obj in OBJECTS)

    @property
    def memory_time(self):
        """Время (пс), за которое вес старых отсчётов уменьшается в e раз."""
        return self.memory_collisions * self.gas.collision_time(self.i)

    # ------------------------------------------------------------------
    # Статистика
    # ------------------------------------------------------------------
    def reset_stats(self):
        self.hist = {}
        self.series = {}
        for kind in (tf.MODULUS, tf.PROJECTION):
            for obj in OBJECTS:
                low, high = self.value_range(kind, obj)
                self.hist[obj, kind] = Histogram(low, high, HIST_BINS)
                self.series[obj, kind] = TimeSeries()
        self.steps_since_reset = 0
        self._memory_time = self.memory_time

    def velocity(self, obj):
        """Вектор скорости молекулы 1, молекулы 2 или относительной скорости v1 - v2."""
        v1 = self.gas.vel[self.i]
        v2 = self.gas.vel[self.j]
        return {SINGLE: v1, SECOND: v2, PAIR: v1 - v2}[obj]

    def _sample_selected(self):
        t = self.gas.time
        for obj in OBJECTS:
            v = self.velocity(obj)
            for kind, x in ((tf.MODULUS, np.hypot(v[0], v[1])), (tf.PROJECTION, v[0])):
                self.hist[obj, kind].add(x)
                self.series[obj, kind].add(t, x)

    def _add_ensemble(self, obj, velocities):
        self.hist[obj, tf.MODULUS].add(np.hypot(velocities[:, 0], velocities[:, 1]))
        self.hist[obj, tf.PROJECTION].add(velocities[:, 0])

    def _sample_ensemble(self):
        """Та же статистика, но сразу по многим молекулам того же сорта, что и выбранные."""
        vel = self.gas.vel
        same_1 = self.gas.indices_of(self.gas.species[self.i])
        same_2 = self.gas.indices_of(self.gas.species[self.j])
        self._add_ensemble(SINGLE, vel[same_1])
        self._add_ensemble(SECOND, vel[same_2])
        # Случайные пары: первая молекула из сорта молекулы 1, вторая — из сорта молекулы 2.
        k = len(same_1)
        p = self.rng.choice(same_1, size=k)
        q = self.rng.choice(same_2, size=k)
        ok = p != q
        self._add_ensemble(PAIR, vel[p[ok]] - vel[q[ok]])

    def _forget(self, dt):
        factor = math.exp(-dt / self._memory_time)
        for hist in self.hist.values():
            hist.forget(factor)

    def advance(self, n_steps, dt=None):
        """n_steps шагов моделирования; после каждого — отсчёт для выбранных молекул."""
        dt = self.gas.dt if dt is None else dt
        for _ in range(n_steps):
            self.gas.step(dt)
            self._forget(dt)
            self._sample_selected()
            self.steps_since_reset += 1
            if self.ensemble and self.steps_since_reset % ENSEMBLE_EVERY == 0:
                self._sample_ensemble()

    def advance_by(self, factor):
        """Смоделировать время factor·dt (шагами не длиннее dt)."""
        n = max(1, int(math.ceil(factor)))
        self.advance(n, self.gas.dt * factor / n)

    def advance_for_seconds(self, seconds, chunk=5):
        """Считать шагами dt, пока не пройдёт seconds секунд реального времени."""
        started = time.perf_counter()
        while time.perf_counter() - started < seconds:
            self.advance(chunk)
