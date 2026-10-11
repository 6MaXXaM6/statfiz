// Таблицы обозначений и единиц.

#include "ui/labels.h"

using theory::Kind;

namespace labels {

static int index(Kind kind)
{
    return kind == Kind::Modulus ? 0 : kind == Kind::Projection ? 1 : 2;
}

// Для каждого объекта — (модуль, проекция, энергия)
QString quantity(Obj obj, Kind kind)
{
    static const char* pair[] = {"|v<sub>отн</sub>|", "v<sub>отн,x</sub>", "E<sub>отн</sub>"};
    static const char* single[] = {"|v<sub>1</sub>|", "v<sub>1,x</sub>", "E<sub>1</sub>"};
    static const char* second[] = {"|v<sub>2</sub>|", "v<sub>2,x</sub>", "E<sub>2</sub>"};
    const char** table = obj == Obj::Pair ? pair : obj == Obj::Single ? single : second;
    return QString::fromUtf8(table[index(kind)]);
}

QString quantity_plain(Obj obj, Kind kind)
{
    static const char* pair[] = {"|vотн|", "vотн,x", "Eотн"};
    static const char* single[] = {"|v₁|", "v₁,x", "E₁"};
    static const char* second[] = {"|v₂|", "v₂,x", "E₂"};
    const char** table = obj == Obj::Pair ? pair : obj == Obj::Single ? single : second;
    return QString::fromUtf8(table[index(kind)]);
}

QString unit(Kind kind)
{
    return QString::fromUtf8(kind == Kind::Energy ? "10⁻²¹ Дж" : "м/с");
}

double variance_divisor(Kind kind)
{
    return kind == Kind::Energy ? 1.0 : 1e3;
}

QString variance_unit(Kind kind)
{
    return QString::fromUtf8(kind == Kind::Energy ? " (10⁻²¹ Дж)²" : " ·10³ (м/с)²");
}

QString density_unit(Kind kind)
{
    return QString::fromUtf8(kind == Kind::Energy ? "1/(10⁻²¹ Дж)" : "с/м");
}

QString axis_label(Obj obj, Kind kind)
{
    return quantity(obj, kind) + ", " + unit(kind);
}

}  // namespace labels
