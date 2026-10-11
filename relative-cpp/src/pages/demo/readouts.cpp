// Тексты легенды и строки сравнения.

#include "pages/demo/readouts.h"

#include <cmath>
#include <limits>

#include "ui/labels.h"
#include "ui/style.h"
#include "ui/widgets.h"

using theory::Kind;

QString vector_legend(std::optional<Obj> projection_of)
{
    QString text = QString::fromUtf8("%1 = %2 − %3")
                       .arg(html_color(labels::VREL, style::REL), html_color(labels::V1, style::MOL1),
                            html_color(labels::V2, style::MOL2));
    if (projection_of)
        text += "<br>" + html_color(labels::quantity(*projection_of, Kind::Projection), style::PROJ);
    return text;
}

// Для модуля сравниваются средние, для проекции — среднеквадратичные отклонения.
// Теория: отношение равно sqrt(m/mu) — для одинаковых молекул sqrt(2).
QString ratio_text(const Experiment& exp, Obj obj, Kind kind)
{
    const Histogram& single = exp.hist.at({obj, kind});
    const Histogram& pair = exp.hist.at({Obj::Pair, kind});
    QString q_pair = labels::quantity(Obj::Pair, kind), q_single = labels::quantity(obj, kind);
    QString name;
    double ratio = std::numeric_limits<double>::quiet_NaN();
    if (kind == Kind::Modulus) {
        name = QString::fromUtf8("⟨%1⟩ / ⟨%2⟩").arg(q_pair, q_single);
        if (single.total() > 0 && single.mean() > 0)
            ratio = pair.mean() / single.mean();
    } else {
        name = QString::fromUtf8("σ(%1) / σ(%2)").arg(q_pair, q_single);
        if (single.variance() > 0 && pair.variance() > 0)
            ratio = std::sqrt(pair.variance() / single.variance());
    }
    QString theory;
    if (std::fabs(exp.mass_1() - exp.mass_2()) < 1e-9)
        theory = QString::fromUtf8("√2 ≈ 1.414");
    else
        theory = QString::fromUtf8("√(m/μ) ≈ %1, μ = %2 а.е.м.")
                     .arg(std::sqrt(exp.mass(obj) / exp.reduced_mass()), 0, 'f', 3)
                     .arg(style::fmt(exp.reduced_mass(), 1));
    return QString::fromUtf8("%1 = <b>%2</b> &nbsp; <span style='color:%3'>теория: %4</span>")
        .arg(name, style::fmt(ratio, 3), style::THEORY, theory);
}
