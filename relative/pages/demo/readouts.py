"""Подписи: легенда к векторной диаграмме и сравнение двух величин (√2)."""

import math

from model import theory as tf
from model.experiment import PAIR
from ui import labels, style
from ui.widgets import html_color


def vector_legend(projection_of=None):
    """Цветная подпись к векторной диаграмме; projection_of — чья проекция показана (или None)."""
    text = "%s = %s − %s" % (html_color(labels.VREL, style.REL), html_color(labels.V1, style.MOL1),
                             html_color(labels.V2, style.MOL2))
    if projection_of is not None:
        text += "<br>" + html_color(labels.projection(projection_of), style.PROJ)
    return text


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
        theory = "√2 ≈ 1.414"
    else:
        theory = "√(m/μ) ≈ %.3f, μ = %s а.е.м." % (math.sqrt(mass / exp.reduced_mass), style.fmt(exp.reduced_mass, 1))
    return "%s = <b>%s</b> &nbsp; <span style='color:%s'>теория: %s</span>" % (
        name, style.fmt(ratio, 3), style.THEORY, theory)
