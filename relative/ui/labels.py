"""Обозначения физических величин (HTML) — одни и те же во всех подписях."""

from model import theory as tf
from model.experiment import PAIR, SECOND, SINGLE

V1 = "v<sub>1</sub>"
V2 = "v<sub>2</sub>"
VREL = "v<sub>отн</sub>"
V1X = "v<sub>1,x</sub>"
V2X = "v<sub>2,x</sub>"
VRELX = "v<sub>отн,x</sub>"


# Обозначения: для каждого объекта — (модуль, проекция, энергия),
# в HTML и простым текстом (для кнопок и списков, где HTML не работает)
_HTML = {
    PAIR: ("|%s|" % VREL, VRELX, "E<sub>отн</sub>"),
    SINGLE: ("|%s|" % V1, V1X, "E<sub>1</sub>"),
    SECOND: ("|%s|" % V2, V2X, "E<sub>2</sub>"),
}
_PLAIN = {
    PAIR: ("|vотн|", "vотн,x", "Eотн"),
    SINGLE: ("|v₁|", "v₁,x", "E₁"),
    SECOND: ("|v₂|", "v₂,x", "E₂"),
}
_INDEX = {tf.MODULUS: 0, tf.PROJECTION: 1, tf.ENERGY: 2}

# Единицы: (величины, делитель дисперсии для показа, единица дисперсии, единица плотности вероятности)
_UNITS = {
    tf.MODULUS: ("м/с", 1e3, " ·10³ (м/с)²", "с/м"),
    tf.PROJECTION: ("м/с", 1e3, " ·10³ (м/с)²", "с/м"),
    tf.ENERGY: ("10⁻²¹ Дж", 1.0, " (10⁻²¹ Дж)²", "1/(10⁻²¹ Дж)"),
}


def quantity(obj, kind):
    """|v_отн|, v_отн,x, |v₁|, v₁,x, E₁ и т.д. (HTML)."""
    return _HTML[obj][_INDEX[kind]]


def quantity_plain(obj, kind):
    """То же обозначение простым текстом."""
    return _PLAIN[obj][_INDEX[kind]]


def unit(kind):
    """Единица величины: м/с или 10⁻²¹ Дж."""
    return _UNITS[kind][0]


def variance_unit(kind):
    """(делитель, подпись) для показа дисперсии: скорости — в 10³ (м/с)², энергия — в (10⁻²¹ Дж)²."""
    return _UNITS[kind][1], _UNITS[kind][2]


def density_unit(kind):
    return _UNITS[kind][3]


def axis_label(obj, kind):
    """Подпись оси: обозначение и единицы, например "|v<sub>1</sub>|, м/с"."""
    return "%s, %s" % (quantity(obj, kind), unit(kind))


def projection(obj):
    return quantity(obj, tf.PROJECTION)
