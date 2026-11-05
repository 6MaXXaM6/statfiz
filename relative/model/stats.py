"""Накопление статистики: гистограммы и временные ряды."""

import numpy as np

import settings


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
    """История в ограниченной памяти без потери пиков и статистики.

    Корзина хранит t0, t1, min, max, last, n, sum, sum_sq. При заполнении
    соседние корзины сливаются попарно. Каждый новый отсчёт учитывается.
    При заданном window остаются только недавние корзины и одна граничная.
    count — все отсчёты с момента сброса; summary описывает сохранённое окно.
    """

    def __init__(self, size=None, window=None):
        size = settings.HISTORY_BUCKETS if size is None else size
        if size < 2:
            raise ValueError("нужно хотя бы две корзины")
        if window is not None and window <= 0:
            raise ValueError("окно истории должно быть положительным")
        self.size = size - size % 2
        self.window = window
        self.revision = 0
        self.reset()

    def reset(self):
        self.revision += 1
        self.buckets = []
        self.span = 1
        self.count = 0
        self._first = self._last = None
        self._summary_key = None
        self._summary = None

    def add(self, t, v):
        if self.window is not None:
            self.discard_before(t - self.window)
        if not self.buckets or self.buckets[-1][5] >= self.span:
            if len(self.buckets) == self.size:
                self._merge_pairs()
            self.buckets.append([t, t, v, v, v, 1, v, v*v])
        else:
            b = self.buckets[-1]
            b[1], b[2], b[3], b[4] = t, min(b[2], v), max(b[3], v), v
            b[5] += 1
            b[6] += v
            b[7] += v*v
        if self._first is None:
            self._first = (t, v)
        self.count += 1
        self.revision += 1
        self._last = (t, v)

    def set_window(self, duration):
        """Изменить окно истории; ранее удалённые точки не восстанавливаются."""
        if duration is not None and duration <= 0:
            raise ValueError("окно истории должно быть положительным")
        previous = self.window
        self.window = duration
        if duration is not None and (previous is None or duration < previous):
            # Не дописываем новые точки в старую крупную граничную корзину.
            self.span = 1
        if duration is not None and self._last is not None:
            self.discard_before(self._last[0] - duration)

    def discard_before(self, cutoff):
        """Удалить завершившиеся старые корзины, оставляя граничную целиком."""
        removed = 0
        for bucket in self.buckets:
            if bucket[1] >= cutoff:
                break
            removed += 1
        if not removed:
            return
        del self.buckets[:removed]
        self.revision += 1
        if self.buckets:
            first = self.buckets[0]
            self._first = (first[1], first[4])
            # После уменьшения памяти новые точки снова пишутся подробнее.
            if len(self.buckets) < self.size // 4:
                self.span = max(1, self.span // 2)
        else:
            self._first = None
            self.span = 1

    def start_time(self):
        return self.buckets[0][0] if self.buckets else None

    def _merge_pairs(self):
        self.buckets = [[a[0], b[1], min(a[2],b[2]), max(a[3],b[3]), b[4],
                         a[5]+b[5], a[6]+b[6], a[7]+b[7]]
                        for a,b in zip(self.buckets[::2], self.buckets[1::2])]
        self.span *= 2

    def summary(self, max_points):
        """Не более max_points интервалов: крайние значения и взвешенные моменты.

        Соседние корзины объединяются, а не выбрасываются. Поэтому единичный
        пик и измерения в неполной последней корзине учитываются полностью.
        """
        if max_points < 1:
            raise ValueError("нужен хотя бы один интервал")
        key = self.revision, max_points
        if key == self._summary_key:
            return self._summary
        raw = np.asarray(self.buckets, dtype=float).reshape(-1, 8)
        if len(raw) <= max_points:
            result = raw
        else:
            group = (len(raw) + max_points - 1) // max_points
            starts = np.arange(0, len(raw), group)
            ends = np.r_[starts[1:] - 1, len(raw) - 1]
            result = np.empty((len(starts), 8))
            result[:, 0] = raw[starts, 0]
            result[:, 1] = raw[ends, 1]
            result[:, 2] = np.minimum.reduceat(raw[:, 2], starts)
            result[:, 3] = np.maximum.reduceat(raw[:, 3], starts)
            result[:, 4] = raw[ends, 4]
            result[:, 5:] = np.add.reduceat(raw[:, 5:], starts, axis=0)
        self._summary_key, self._summary = key, result
        return result

    def data(self):
        """Представительные точки для совместимости; полная статистика — buckets."""
        if not self.buckets:
            return np.array([]), np.array([])
        points = [(b[1], b[4]) for b in self.buckets]
        if points[0][0] != self._first[0]:
            points.insert(0, self._first)
        return tuple(np.asarray(points).T)

    def first(self):
        return self._first

    def last(self):
        return self._last
