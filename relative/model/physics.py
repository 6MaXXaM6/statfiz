"""
Модель двумерного идеального газа из твёрдых дисков.

Единицы измерения внутри модели:
    координаты  — нм (нанометры),
    скорости    — м/с,
    время       — пс (пикосекунды),
    массы       — а.е.м.,
    температура — К.
За время dt [пс] частица со скоростью v [м/с] проходит v * dt * 1e-3 нм.

Газ может состоять из двух сортов молекул: A (основной) и B (второй газ
или одна "чужая" частица). Столкновения — абсолютно упругие удары дисков,
со стенками — зеркальное отражение.
"""

import numpy as np

K_B = 1.380649e-23      # постоянная Больцмана, Дж/К
AMU = 1.66053907e-27    # атомная единица массы, кг

BOX_SIZE = 100.0        # сторона квадратного сосуда, нм
MAX_PARTICLES = 300

# Радиус молекулы пропорционален m^(1/3) (объём пропорционален массе), поэтому
# отношение размеров на экране честно показывает отношение масс.
# Самая тяжёлая молекула (M_MAX) имеет радиус R_MAX, самая лёгкая (1 а.е.м.) — R_MIN.
M_MAX = 200.0                        # а.е.м.
R_MAX = 2.4                          # нм
R_MIN = R_MAX / M_MAX ** (1.0 / 3)   # ≈ 0.41 нм

# Перевод: скорость [м/с] * время [пс] * NM_PER_MS_PS = путь [нм]
NM_PER_MS_PS = 1e-3


def radius_for_mass(mass_amu):
    """Радиус молекулы (нм) по её массе (а.е.м.): r ∝ m^(1/3)."""
    return R_MAX * np.cbrt(np.clip(mass_amu, 1.0, M_MAX) / M_MAX)


def thermal_sigma(mass_amu, temperature):
    """Среднеквадратичное значение одной проекции скорости sqrt(kT/m), м/с."""
    return np.sqrt(K_B * temperature / (mass_amu * AMU))


class Gas:
    """Состояние газа и шаг моделирования."""

    def __init__(self, n_a, n_b, mass_a, mass_b, temperature, seed=None):
        self.rng = np.random.default_rng(seed)
        self.box = BOX_SIZE
        self.n_a = int(n_a)
        self.n_b = int(n_b)
        n = self.n_a + self.n_b
        if n < 1 or n > MAX_PARTICLES:
            raise ValueError("число молекул должно быть от 1 до %d" % MAX_PARTICLES)

        # species[k] = 0 для сорта A, 1 для сорта B. Молекулы B идут в конце массива.
        self.species = np.zeros(n, dtype=int)
        self.species[self.n_a:] = 1
        self.mass = np.where(self.species == 0, float(mass_a), float(mass_b))
        self.radius = radius_for_mass(self.mass)
        self.temperature = float(temperature)
        self.time = 0.0  # пс
        self.collisions = 0

        self.pos = self._random_positions(n)
        self.vel = self._maxwell_velocities()
        self.dt = self.recommended_dt()

    @property
    def n(self):
        return len(self.mass)

    # ------------------------------------------------------------------
    # Начальные условия
    # ------------------------------------------------------------------
    def _random_positions(self, n):
        """Случайные неперекрывающиеся положения: по одной молекуле в случайной клетке сетки."""
        r_max = self.radius.max()
        cell = 2.05 * r_max
        cells_per_side = int(self.box // cell)
        chosen = self.rng.choice(cells_per_side ** 2, size=n, replace=False)
        cx = chosen % cells_per_side
        cy = chosen // cells_per_side
        # Небольшой случайный сдвиг внутри клетки, чтобы не было видно сетки.
        margin = cell / 2 - r_max
        jitter = self.rng.uniform(-margin, margin, size=(n, 2))
        offset = (self.box - cells_per_side * cell) / 2
        pos = np.empty((n, 2))
        pos[:, 0] = offset + (cx + 0.5) * cell + jitter[:, 0]
        pos[:, 1] = offset + (cy + 0.5) * cell + jitter[:, 1]
        return pos

    def _maxwell_velocities(self):
        """Скорости по распределению Максвелла, затем точная подгонка энергии под T."""
        sigma = thermal_sigma(self.mass, self.temperature)
        vel = self.rng.normal(size=(self.n, 2)) * sigma[:, None]
        self.vel = vel
        self.set_temperature(self.temperature)
        return self.vel

    # ------------------------------------------------------------------
    # Управление параметрами
    # ------------------------------------------------------------------
    def kinetic_energy(self):
        """Полная кинетическая энергия, Дж."""
        return 0.5 * np.sum(self.mass * AMU * np.sum(self.vel ** 2, axis=1))

    def momentum(self):
        """Полный импульс, кг·м/с (вектор)."""
        return np.sum((self.mass * AMU)[:, None] * self.vel, axis=0)

    def set_temperature(self, temperature):
        """Меняет температуру, умножая все скорости на один коэффициент.

        В двумерном газе на молекулу приходится энергия kT (две степени свободы),
        поэтому полная энергия должна быть равна N·k·T.
        """
        self.temperature = float(temperature)
        target = self.n * K_B * self.temperature
        current = self.kinetic_energy()
        if current > 0:
            self.vel *= np.sqrt(target / current)
        self.dt = self.recommended_dt()

    def set_masses(self, mass_a, mass_b):
        """Новые массы без пересоздания газа: молекулы остаются на местах.

        Радиусы меняются вслед за массами. Скорости умножаются на sqrt(m_старая / m_новая),
        так что энергия каждой молекулы, а значит и температура, сохраняются; меняется
        только распределение скоростей — газ сам придёт к новому равновесию.
        """
        old = self.mass
        self.mass = np.where(self.species == 0, float(mass_a), float(mass_b))
        self.radius = radius_for_mass(self.mass)
        self.vel *= np.sqrt(old / self.mass)[:, None]
        self.separate_overlaps()
        self.dt = self.recommended_dt()

    def separate_overlaps(self, max_rounds=200):
        """Раздвинуть перекрывшиеся диски (например, после того как радиусы выросли)."""
        for _ in range(max_rounds):
            ii, jj = self.find_close_pairs()
            if len(ii) == 0:
                return
            for i, j in zip(ii, jj):
                d = self.pos[j] - self.pos[i]
                dist = np.hypot(d[0], d[1])
                if dist > 0:
                    self._push_apart(i, j, d / dist, dist)
            for axis in (0, 1):
                np.clip(self.pos[:, axis], self.radius, self.box - self.radius, out=self.pos[:, axis])

    def recommended_dt(self):
        """Шаг по времени (пс): быстрая молекула за шаг смещается не более чем на 1/4 радиуса."""
        v_fast = 4.0 * thermal_sigma(self.mass.min(), self.temperature)
        return 0.25 * self.radius.min() / (v_fast * NM_PER_MS_PS)

    # ------------------------------------------------------------------
    # Шаг моделирования
    # ------------------------------------------------------------------
    def step(self, dt=None):
        """Сдвигает систему на время dt (пс)."""
        if dt is None:
            dt = self.dt
        self.pos += self.vel * (dt * NM_PER_MS_PS)
        self._bounce_walls()
        self._collide()
        self.time += dt

    def _bounce_walls(self):
        r = self.radius
        for axis in (0, 1):
            low = (self.pos[:, axis] < r) & (self.vel[:, axis] < 0)
            high = (self.pos[:, axis] > self.box - r) & (self.vel[:, axis] > 0)
            hit = low | high
            self.vel[hit, axis] *= -1.0
            # Возвращаем внутрь, если молекула успела "залезть" в стенку.
            np.clip(self.pos[:, axis], r, self.box - r, out=self.pos[:, axis])

    def find_close_pairs(self):
        """Пары молекул (i, j), диски которых перекрываются.

        Молекулы сортируются по x; сравниваются только соседи по этому списку,
        пока расстояние по x не превысит сумму радиусов. Так не нужна полная
        матрица расстояний N×N.
        """
        n = self.n
        if n < 2:
            return np.empty(0, dtype=int), np.empty(0, dtype=int)
        order = np.argsort(self.pos[:, 0])
        xs = self.pos[order]
        rs = self.radius[order]
        reach = 2.0 * self.radius.max()
        found_i = []
        found_j = []
        for shift in range(1, n):
            dx = xs[shift:, 0] - xs[:-shift, 0]
            near = dx < reach
            if not near.any():
                break  # при большем сдвиге по отсортированному списку ближе уже не будет
            a = np.nonzero(near)[0]
            b = a + shift
            d = xs[b] - xs[a]
            touch = np.sum(d * d, axis=1) < (rs[a] + rs[b]) ** 2
            found_i.append(order[a[touch]])
            found_j.append(order[b[touch]])
        if not found_i:
            return np.empty(0, dtype=int), np.empty(0, dtype=int)
        return np.concatenate(found_i), np.concatenate(found_j)

    def _collide(self):
        ii, jj = self.find_close_pairs()
        for i, j in zip(ii, jj):
            d = self.pos[j] - self.pos[i]
            dist = np.hypot(d[0], d[1])
            if dist == 0:
                continue
            normal = d / dist
            dv = self.vel[j] - self.vel[i]
            vn = dv[0] * normal[0] + dv[1] * normal[1]
            if vn < 0:  # молекулы сближаются — упругий удар
                mi = self.mass[i]
                mj = self.mass[j]
                self.vel[i] += (2.0 * mj / (mi + mj)) * vn * normal
                self.vel[j] -= (2.0 * mi / (mi + mj)) * vn * normal
                self.collisions += 1
            self._push_apart(i, j, normal, dist)

    def _push_apart(self, i, j, normal, dist):
        """Раздвинуть перекрывшиеся диски i и j вдоль линии центров (на скорости и энергию не влияет)."""
        overlap = self.radius[i] + self.radius[j] - dist
        if overlap > 0:
            self.pos[i] -= 0.5 * overlap * normal
            self.pos[j] += 0.5 * overlap * normal

    def collision_time(self, k):
        """Среднее время (пс) между столкновениями молекулы k — оценка кинетической теории (2D).

        Относительно молекулы сорта s молекула k движется со средней скоростью
        <u> = sqrt(pi/2)·sqrt(kT/mu) и "заметает" полосу шириной 2(r_k + r_s),
        поэтому частота столкновений nu = sum_s n_s · 2(r_k + r_s) · <u>.
        """
        area = self.box ** 2
        rate = 0.0  # 1/пс
        for s in (0, 1):
            others = self.species == s
            count = others.sum() - (1 if self.species[k] == s else 0)
            if count <= 0:
                continue
            r_s = self.radius[others][0]
            mu = self.mass[k] * self.mass[others][0] / (self.mass[k] + self.mass[others][0])
            mean_u = np.sqrt(np.pi / 2) * thermal_sigma(mu, self.temperature) * NM_PER_MS_PS  # нм/пс
            rate += count / area * 2 * (self.radius[k] + r_s) * mean_u
        return 1.0 / rate if rate > 0 else float("inf")

    # ------------------------------------------------------------------
    # Вспомогательное
    # ------------------------------------------------------------------
    def nearest(self, x, y, max_dist=None):
        """Индекс молекулы, ближайшей к точке (x, y), или None."""
        d = np.hypot(self.pos[:, 0] - x, self.pos[:, 1] - y)
        k = int(np.argmin(d))
        if max_dist is not None and d[k] > max_dist:
            return None
        return k

    def indices_of(self, species):
        return np.nonzero(self.species == species)[0]
