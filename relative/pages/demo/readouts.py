"""Подписи: легенда к векторной диаграмме и сравнение двух величин (√2)."""

import math

import settings

from model import theory as tf
from model.experiment import PAIR
from ui import labels, style
from ui.widgets import html_color


def stats_ready(exp):
    """Задержка первых чисел, а не оценка независимости/точности измерений.

    Счётчик шагов не сбрасывается при повороте или переключении темпа и
    не зависит от флажков отображения. Новый опыт/выбор частиц сбрасывает его.
    """
    return exp.steps_since_reset >= settings.STATS_MIN_STEPS


def significant(value):
    """Две значащие цифры только в тексте; сами данные не округляются."""
    if not math.isfinite(value):
        return "—"
    if value == 0:
        return "0"
    rounded = float(format(value, ".2g"))
    exponent = math.floor(math.log10(abs(rounded)))
    if exponent >= 4 or exponent <= -3:
        return ("%.1f·10%s" % (rounded / 10**exponent, style.sup(exponent))).replace("-", "−")
    return style.fmt(rounded, max(0, 1 - exponent))


# Правка цветной формулы под построением; сами обозначения задаются в ui/labels.py.
def vector_legend(projection_of=None):
    """Цветная подпись к векторной диаграмме; projection_of — чья проекция показана (или None)."""
    # Менять знаки/HTML этой строки для оформления легенды; цвета берутся из style, обозначения — из labels.
    text = "%s = %s − %s" % (html_color(labels.VREL, style.REL), html_color(labels.V1, style.MOL1),
                             html_color(labels.V2, style.MOL2))
    if projection_of is not None:
        text += "<br>" + html_color(labels.projection(projection_of), style.PROJ)
    return text


# Правка нижнего сравнения опыта с теорией; это другая подпись, чем «теор.» под каждой панелью.
def ratio_text(exp, obj, kind):
    """Во сколько раз относительная скорость больше скорости молекулы obj (1 или 2) — опыт и теория.

    Для модуля сравниваются средние, для проекции — среднеквадратичные отклонения.
    Теория: отношение равно sqrt(m/mu) — для одинаковых молекул sqrt(2).
    """
    single, pair = exp.hist[obj, kind], exp.hist[PAIR, kind]
    q_pair, q_single = labels.quantity(PAIR, kind), labels.quantity(obj, kind)
    if kind == tf.MODULUS:
        name = "⟨%s⟩ / ⟨%s⟩" % (q_pair, q_single)
        ok = single.total > 0 and single.mean() > 0
        ratio = pair.mean() / single.mean() if ok else float("nan")
    else:
        name = "σ(%s) / σ(%s)" % (q_pair, q_single)
        ok = single.variance() > 0 and pair.variance() > 0
        ratio = math.sqrt(pair.variance() / single.variance()) if ok else float("nan")
    mass = exp.mass(obj)
    if abs(exp.mass_1 - exp.mass_2) < 1e-9:
        theory = "√2 ≈ 1.41"
    else:
        theory = "√(m/μ) ≈ %s" % style.fmt(math.sqrt(mass / exp.reduced_mass), 2)
    # Здесь находится слово «теория:» в нижней строке опыта; текущие значения подставляются автоматически.
    return "%s = <b>%s</b> &nbsp; <span style='color:%s'>теория: %s</span>" % (
        name, style.fmt(ratio, 2) if stats_ready(exp) else "—", style.THEORY, theory)
