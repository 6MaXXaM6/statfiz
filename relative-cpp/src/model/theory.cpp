// Формулы теоретических распределений (см. описание в theory.h).

#include "model/theory.h"

#include <cmath>

#include "model/physics.h"

namespace theory {

double reduced_mass(double m1, double m2)
{
    return m1 * m2 / (m1 + m2);
}

double sigma_for(double mass_amu, double temperature)
{
    return physics::thermal_sigma(mass_amu, temperature);
}

double pdf(Kind kind, double x, double s)
{
    switch (kind) {
    case Kind::Modulus:     // Рэлей: x/s² · exp(-x²/2s²)
        return x >= 0 ? x / (s * s) * std::exp(-x * x / (2 * s * s)) : 0.0;
    case Kind::Energy:      // экспонента: exp(-x/s) / s
        return x >= 0 ? std::exp(-x / s) / s : 0.0;
    case Kind::Projection:  // Гаусс: exp(-x²/2s²) / (sqrt(2pi)·s)
        break;
    }
    return std::exp(-x * x / (2 * s * s)) / (std::sqrt(2 * M_PI) * s);
}

double mean(Kind kind, double s)
{
    switch (kind) {
    case Kind::Modulus: return s * std::sqrt(M_PI / 2);
    case Kind::Energy: return s;  // <E> = kT
    case Kind::Projection: break;
    }
    return 0.0;
}

double variance(Kind kind, double s)
{
    if (kind == Kind::Modulus)
        return (2 - M_PI / 2) * s * s;
    return s * s;  // проекция: sigma²; энергия: (kT)²
}

std::pair<double, double> value_range(Kind kind, double s)
{
    switch (kind) {
    case Kind::Modulus: return {0.0, 4.0 * s};
    case Kind::Energy: return {0.0, 6.0 * s};  // exp(-6) ≈ 0.25%
    case Kind::Projection: break;
    }
    return {-4.0 * s, 4.0 * s};
}

// Максимум плотности: у модуля — при v = s, у энергии и проекции — в нуле.
double peak(Kind kind, double s)
{
    return pdf(kind, kind == Kind::Modulus ? s : 0.0, s);
}

}  // namespace theory
