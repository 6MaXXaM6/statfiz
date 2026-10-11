// Обозначения физических величин (HTML) — одни и те же во всех подписях.

#pragma once

#include <QString>

#include "model/experiment.h"

namespace labels {

inline const char* V1 = "v<sub>1</sub>";
inline const char* V2 = "v<sub>2</sub>";
inline const char* VREL = "v<sub>отн</sub>";

QString quantity(Obj obj, theory::Kind kind);        // |v_отн|, v₁,x, E₂ ... (HTML)
QString quantity_plain(Obj obj, theory::Kind kind);  // то же простым текстом (для списков)
QString unit(theory::Kind kind);                     // м/с или 10⁻²¹ Дж
double variance_divisor(theory::Kind kind);          // дисперсия скоростей показывается в 10³ (м/с)²
QString variance_unit(theory::Kind kind);
QString density_unit(theory::Kind kind);             // единица плотности вероятности
QString axis_label(Obj obj, theory::Kind kind);      // "|v<sub>1</sub>|, м/с"

}  // namespace labels
