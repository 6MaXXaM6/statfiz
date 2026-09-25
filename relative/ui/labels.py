"""Обозначения физических величин (HTML) — одни и те же во всех подписях."""

from model import theory as tf
from model.experiment import PAIR, SECOND, SINGLE

V1 = "v<sub>1</sub>"
V2 = "v<sub>2</sub>"
VREL = "v<sub>отн</sub>"
V1X = "v<sub>1,x</sub>"
V2X = "v<sub>2,x</sub>"
VRELX = "v<sub>отн,x</sub>"


# Обозначения для каждого объекта: (модуль, проекция) в HTML и простым текстом (для кнопок и списков)
_HTML = {PAIR: ("|%s|" % VREL, VRELX), SINGLE: ("|%s|" % V1, V1X), SECOND: ("|%s|" % V2, V2X)}
_PLAIN = {PAIR: ("|vотн|", "vотн,x"), SINGLE: ("|v₁|", "v₁,x"), SECOND: ("|v₂|", "v₂,x")}


def quantity(obj, kind):
    """|v_отн|, v_отн,x, |v₁|, v₁,x, |v₂| или v₂,x."""
    modulus, proj = _HTML[obj]
    return modulus if kind == tf.MODULUS else proj


def quantity_plain(obj, kind):
    """То же обозначение простым текстом (для кнопок и списков, где HTML не работает)."""
    modulus, proj = _PLAIN[obj]
    return modulus if kind == tf.MODULUS else proj


def projection(obj):
    return quantity(obj, tf.PROJECTION)
