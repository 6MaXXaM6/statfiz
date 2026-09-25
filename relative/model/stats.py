"""Накопление статистики: гистограммы и временные ряды."""

import numpy as np


class Histogram:
    """Гистограмма с фиксированными границами + точные среднее и дисперсия.

    Отсчёты могут "забываться" (forget): тогда total — не число отсчётов, а их суммарный вес.
    """

    def __init__(self, low, high, bins=30):
        self.edges = np.linspace(low, high, bins + 1)
        self.reset()

    def reset(self):
        self.counts = np.zeros(len(self.edges) - 1)
        self.total = 0.0
        self._sum = 0.0
        self._sum_sq = 0.0

    @property
    def width(self):
        return self.edges[1] - self.edges[0]

    @property
    def centers(self):
        return 0.5 * (self.edges[:-1] + self.edges[1:])

    def forget(self, factor):
        """Экспоненциальное забывание: вес всех прежних отсчётов умножается на factor < 1."""
        self.counts *= factor
        self.total *= factor
        self._sum *= factor
        self._sum_sq *= factor

    def add(self, values):
        values = np.atleast_1d(np.asarray(values, dtype=float))
        if values.size == 0:
            return
        counts, _ = np.histogram(values, bins=self.edges)
        self.counts += counts
        self.total += values.size
        self._sum += values.sum()
        self._sum_sq += np.sum(values ** 2)

    def bin_of(self, value):
        """Номер столбика, в который попадает значение (или None, если за пределами)."""
        k = int(np.floor((value - self.edges[0]) / self.width))
        if 0 <= k < len(self.counts):
            return k
        return None

    def density(self):
        """Экспериментальная плотность вероятности (нормирована на 1)."""
        if self.total == 0:
            return np.zeros_like(self.counts)
        return self.counts / (self.total * self.width)

    def mean(self):
        if self.total == 0:
            return float("nan")
        return self._sum / self.total

    def variance(self):
        if self.total < 1.5:
            return float("nan")
        m = self._sum / self.total
        return max(self._sum_sq / self.total - m * m, 0.0)


class TimeSeries:
    """Вся история величины во времени в ограниченном числе точек.

    Пока место есть, запоминается каждый отсчёт. Когда буфер заполнен, каждая
    вторая точка выбрасывается, а новые отсчёты записываются через один (потом
    через три и т.д.). Так график "схлопывается": ось времени всегда от 0 до
    текущего момента, а памяти нужно не больше `size` точек.
    """

    def __init__(self, size=1000):
        self.size = size - size % 2
        self.t = np.zeros(self.size)
        self.v = np.zeros(self.size)
        self.reset()

    def reset(self):
        self.n = 0          # сколько точек в буфере
        self.stride = 1     # в буфер попадает каждый stride-й отсчёт
        self.count = 0      # сколько всего было отсчётов
        self._last = None

    def add(self, t, v):
        if self.count % self.stride == 0:
            if self.n == self.size:
                self._thin_out()
            self.t[self.n] = t
            self.v[self.n] = v
            self.n += 1
        self.count += 1
        self._last = (t, v)

    def _thin_out(self):
        half = self.size // 2
        self.t[:half] = self.t[0:self.size:2]
        self.v[:half] = self.v[0:self.size:2]
        self.n = half
        self.stride *= 2

    def data(self):
        """Массивы (t, v) в хронологическом порядке, последний отсчёт — всегда в конце."""
        t, v = self.t[:self.n], self.v[:self.n]
        if self._last is not None and (self.n == 0 or t[-1] != self._last[0]):
            t = np.append(t, self._last[0])
            v = np.append(v, self._last[1])
        return t, v

    def last(self):
        return self._last
