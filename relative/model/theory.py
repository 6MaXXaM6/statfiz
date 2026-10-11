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
ENERGY = "energy"          # кинетическая энергия m·v²/2

# Все функции ниже принимают "масштаб" распределения s:
#   для скоростей s = sigma = sqrt(kT/m), м/с;
#   для энергии   s = kT (в тех же единицах, что и энергия).


def reduced_mass(m1, m2):
    return m1 * m2 / (m1 + m2)


def sigma_for(mass_amu, temperature):
    return float(thermal_sigma(mass_amu, temperature))


def pdf(kind, x, s):
    """Плотность вероятности.

    Модуль скорости (2D, Рэлей): x/s² · exp(-x²/2s²).
    Проекция (Гаусс):            exp(-x²/2s²) / (sqrt(2pi)·s).
    Энергия (2D, экспонента):    exp(-x/s) / s — в двумерном газе у энергии две
                                 степени свободы, и её распределение экспоненциальное.
    """
    x = np.asarray(x, dtype=float)
    if kind == MODULUS:
        return np.where(x >= 0, x / s ** 2 * np.exp(-x ** 2 / (2 * s ** 2)), 0.0)
    if kind == ENERGY:
        return np.where(x >= 0, np.exp(-np.maximum(x, 0) / s) / s, 0.0)
    return np.exp(-x ** 2 / (2 * s ** 2)) / (np.sqrt(2 * np.pi) * s)


def mean(kind, s):
    """Теоретическое среднее значение."""
    if kind == MODULUS:
        return s * np.sqrt(np.pi / 2)
    if kind == ENERGY:
        return s  # <E> = kT
    return 0.0


def variance(kind, s):
    """Теоретическая дисперсия."""
    if kind == MODULUS:
        return (2 - np.pi / 2) * s ** 2
    return s ** 2  # проекция: sigma²; энергия: (kT)²


def value_range(kind, s):
    """Диапазон значений, в который попадает практически всё распределение."""
    if kind == MODULUS:
        return 0.0, 4.0 * s
    if kind == ENERGY:
        return 0.0, 6.0 * s  # exp(-6) ≈ 0.25%
    return -4.0 * s, 4.0 * s


def peak(kind, s):
    """Максимум плотности: у модуля — при v = s, у энергии и проекции — в нуле."""
    return float(pdf(kind, s if kind == MODULUS else 0.0, s))
