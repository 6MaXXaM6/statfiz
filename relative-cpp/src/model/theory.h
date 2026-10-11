// Теоретические распределения для двумерного идеального газа.
//
// Одна проекция скорости распределена нормально с дисперсией sigma² = kT/m.
// Модуль скорости на плоскости — распределение Рэлея (двумерный Максвелл):
//     f(v) = v / sigma² · exp(-v² / (2 sigma²)).
// Кинетическая энергия (две степени свободы) — экспоненциальное распределение:
//     f(E) = exp(-E / kT) / kT,  <E> = kT.
//
// Относительная скорость двух молекул u = v1 - v2 имеет те же законы
// распределения, но с приведённой массой mu = m1·m2 / (m1 + m2) вместо m.
// Для одинаковых молекул mu = m/2, поэтому все характерные значения
// относительной скорости больше в sqrt(2) раз.
//
// Все функции принимают "масштаб" распределения s:
//     для скоростей s = sigma = sqrt(kT/m), м/с;
//     для энергии   s = kT (в тех же единицах, что и энергия).

#pragma once

#include <utility>

namespace theory {

// Какую величину рассматриваем
enum class Kind {
    Modulus,     // модуль скорости |v|
    Projection,  // проекция скорости v_x
    Energy,      // кинетическая энергия m·v²/2
};

double reduced_mass(double m1, double m2);
double sigma_for(double mass_amu, double temperature);

double pdf(Kind kind, double x, double s);      // плотность вероятности
double mean(Kind kind, double s);               // теоретическое среднее
double variance(Kind kind, double s);           // теоретическая дисперсия
std::pair<double, double> value_range(Kind kind, double s);  // где лежит практически всё распределение
double peak(Kind kind, double s);               // максимум плотности

}  // namespace theory
