"""Согласованные условные единицы отображения, без изменения физической модели.

Выбираем единицы массы и температуры так, чтобы их числовые значения в полях
оставались прежними. В условных единицах k=1 и E=m*v²/2.
Скорость измеряем в sqrt(k_B/AMU), энергию — в k_B, длину — в единице
координат сосуда. Единица времени следует из длины/скорости.
Внутри Gas по-прежнему используются исходные единицы; перевод — только в UI.
"""
import math

from model import theory as tf
from model.experiment import ENERGY_UNIT
from model.physics import AMU, K_B, NM_PER_MS_PS

VELOCITY_UNIT = math.sqrt(K_B / AMU)
TIME_FACTOR = NM_PER_MS_PS * VELOCITY_UNIT
ENERGY_FACTOR = ENERGY_UNIT / K_B


def value_factor(kind):
    """Множитель исходного значения для показа в условных единицах."""
    return ENERGY_FACTOR if kind == tf.ENERGY else 1.0 / VELOCITY_UNIT
