"""
Теоретические распределения для двумерного идеального газа.

Одна проекция скорости распределена нормально с дисперсией sigma^2 = kT/m.
Модуль скорости на плоскости — распределение Рэлея (двумерный Максвелл):
    f(v) = v / sigma^2 * exp(-v^2 / (2 sigma^2)).

Относительная скорость двух молекул u = v1 - v2 имеет те же законы
распределения, но с приведённой массой mu = m1*m2 / (m1 + m2) вместо m.
Для одинаковых молекул mu = m/2, поэтому все характерные значения
относительной скорости больше в sqrt(2) раз.
"""

import numpy as np

from model.physics import thermal_sigma

# Какую величину рассматриваем
MODULUS = "modulus"        # модуль скорости |v|
PROJECTION = "projection"  # проекция скорости v_x


def reduced_mass(m1, m2):
    return m1 * m2 / (m1 + m2)


def sigma_for(mass_amu, temperature):
    return float(thermal_sigma(mass_amu, temperature))


def pdf(kind, v, sigma):
    """Плотность вероятности (с/м) для модуля или проекции скорости."""
    v = np.asarray(v, dtype=float)
    if kind == MODULUS:
        return np.where(v >= 0, v / sigma ** 2 * np.exp(-v ** 2 / (2 * sigma ** 2)), 0.0)
    return np.exp(-v ** 2 / (2 * sigma ** 2)) / (np.sqrt(2 * np.pi) * sigma)


def mean(kind, sigma):
    """Теоретическое среднее значение, м/с."""
    if kind == MODULUS:
        return sigma * np.sqrt(np.pi / 2)
    return 0.0


def variance(kind, sigma):
    """Теоретическая дисперсия, (м/с)^2."""
    if kind == MODULUS:
        return (2 - np.pi / 2) * sigma ** 2
    return sigma ** 2


def value_range(kind, sigma):
    """Диапазон значений, в который попадает практически всё распределение."""
    if kind == MODULUS:
        return 0.0, 4.0 * sigma
    return -4.0 * sigma, 4.0 * sigma
