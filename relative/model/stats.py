"""Накопление статистики: гистограммы и временные ряды."""

import numpy as np


class Histogram:
    """Гистограмма с фиксированными границами + точные среднее и дисперсия.

    Отсчёты могут "забываться" (forget): тогда total — не число отсчётов, а их суммарный вес.

    Забывание "ленивое": вместо того чтобы на каждом шаге умножать все столбики на
    factor < 1, новые отсчёты добавляются с растущим весом gain (gain делится на factor).
    Отношения весов те же, а работы на шаг — одно деление. Наружу (counts, total)
    всё отдаётся уже поделённым на gain; изредка gain сбрасывается в 1, чтобы не было
    переполнения.
    """

    RENORMALIZE_AT = 1e100

    def __init__(self, low, high, bins=30):
        self._set_edges(low, high, bins)
        self.reset()

    def _set_edges(self, low, high, bins):
        self.edges = np.linspace(low, high, bins + 1)
        self.low = float(low)
        self.bins = bins
        self._inv_width = bins / (high - low)

    def reset(self):
        self._counts = np.zeros(self.bins)
        self._total = 0.0
        self._sum = 0.0
        self._sum_sq = 0.0
        self._gain = 1.0

    @property
    def counts(self):
        return self._counts / self._gain

    @property
    def total(self):
        return self._total / self._gain

    @property
    def width(self):
        return self.edges[1] - self.edges[0]

    @property
    def centers(self):
        return 0.5 * (self.edges[:-1] + self.edges[1:])

    def forget(self, factor):
        """Экспоненциальное забывание: вес всех прежних отсчётов умножается на factor < 1."""
        self._gain /= factor
        if self._gain > self.RENORMALIZE_AT:
            self._renormalize()

    def _renormalize(self):
        g = self._gain
        self._counts /= g
        self._total /= g
        self._sum /= g
        self._sum_sq /= g
        self._gain = 1.0

    def add(self, values, weight=1.0):
        """Добавить одно значение или массив значений (каждое с весом weight)."""
        w = weight * self._gain
        if np.ndim(values) == 0:
            # Одно число — самый частый случай (каждый шаг): без numpy, сразу в нужный столбик.
            x = float(values)
            k = int((x - self.low) * self._inv_width)
            if 0 <= k < self.bins and x >= self.low:
                self._counts[k] += w
            self._total += w
            self._sum += w * x
            self._sum_sq += w * x * x
            return
        x = np.asarray(values, dtype=float).ravel()
        if x.size == 0:
            return
        k = np.floor((x - self.low) * self._inv_width).astype(int)
        inside = (k >= 0) & (k < self.bins)
        self._counts += np.bincount(k[inside], minlength=self.bins) * w
        self._total += w * x.size
        self._sum += w * x.sum()
        self._sum_sq += w * np.dot(x, x)

    def rebin(self, low, high, bins=None):
        """Новый диапазон или число столбиков без потери накопленного
        (например, после изменения температуры).

        Внутри старого столбика отсчёты считаются распределёнными равномерно, и его вес
        делится между новыми столбиками пропорционально перекрытию (через накопленную
        сумму, интерполированную на новые границы). То, что вышло за новый диапазон,
        в столбиках пропадает, но среднее и дисперсия (они считаются по самим значениям)
        остаются точными.
        """
        old_edges = self.edges
        cumulative = np.concatenate(([0.0], np.cumsum(self._counts)))
        self._set_edges(low, high, bins or self.bins)
        self._counts = np.diff(np.interp(self.edges, old_edges, cumulative))

    def bin_of(self, value):
        """Номер столбика, в который попадает значение (или None, если за пределами)."""
        k = int(np.floor((value - self.low) * self._inv_width))
        if 0 <= k < self.bins:
            return k
        return None

    def density(self):
        """Экспериментальная плотность вероятности (нормирована на 1)."""
        if self._total == 0:
            return np.zeros(self.bins)
        return self._counts / (self._total * self.width)

    def mean(self):
        if self._total == 0:
            return float("nan")
        return self._sum / self._total

    def variance(self):
        if self.total < 1.5:
            return float("nan")
        m = self._sum / self._total
        return max(self._sum_sq / self._total - m * m, 0.0)


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
