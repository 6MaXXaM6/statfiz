// Тесты модели (физика, теория, статистика, эксперимент) — перенос тестов Python-версии.
// Модель не зависит от Qt, поэтому и тесты — обычная программа без библиотек:
// каждая проверка печатает, что не так, а программа возвращает число провалов.

#include <cmath>
#include <cstdio>
#include <functional>
#include <random>
#include <string>
#include <vector>

#include "model/experiment.h"
#include "model/physics.h"
#include "model/stats.h"
#include "model/theory.h"

using namespace physics;
using theory::Kind;

namespace {

int failures = 0;
std::string current_test;

void check(bool ok, const char* what)
{
    if (!ok) {
        std::printf("  FAIL [%s]: %s\n", current_test.c_str(), what);
        ++failures;
    }
}

bool close(double a, double b, double rtol = 1e-9, double atol = 1e-12)
{
    return std::fabs(a - b) <= atol + rtol * std::fabs(b);
}

double mean_of(const std::vector<double>& x)
{
    double s = 0;
    for (double v : x)
        s += v;
    return s / x.size();
}

double variance_of(const std::vector<double>& x)
{
    double m = mean_of(x), s = 0;
    for (double v : x)
        s += (v - m) * (v - m);
    return s / x.size();
}

double sum_of(const std::vector<double>& x)
{
    double s = 0;
    for (double v : x)
        s += v;
    return s;
}

// ----------------------------------------------------------------------
// Физика газа
// ----------------------------------------------------------------------

void test_initial_energy_matches_temperature()
{
    Gas gas(200, 50, 28, 4, 300, 1);
    check(close(gas.kinetic_energy(), gas.n() * K_B * 300), "полная энергия = N·k·T");
}

void test_collision_conserves_energy_and_momentum()
{
    Gas gas(2, 0, 10, 10, 300, 2);
    gas.mass = {10.0, 40.0};
    gas.pos = {{50.0, 50.0}, {51.5, 50.3}};  // диски перекрываются
    gas.vel = {{500.0, 100.0}, {-300.0, 0.0}};
    double e0 = gas.kinetic_energy();
    Vec2 p0 = gas.momentum();
    gas.step(0.0);  // шаг нулевой длины: только обработка столкновений
    Vec2 p1 = gas.momentum();
    check(gas.collisions == 1, "ровно одно столкновение");
    check(close(gas.kinetic_energy(), e0), "энергия сохраняется");
    check(close(p1.x, p0.x, 1e-9, 1e-30) && close(p1.y, p0.y, 1e-9, 1e-30), "импульс сохраняется");
}

void test_energy_conserved_over_many_steps()
{
    Gas gas(150, 20, 20, 80, 400, 3);
    double e0 = gas.kinetic_energy();
    for (int s = 0; s < 2000; ++s)
        gas.step();
    check(close(gas.kinetic_energy(), e0, 1e-9), "энергия сохраняется за 2000 шагов");
    bool inside = true;
    for (Vec2 p : gas.pos)
        inside = inside && p.x >= 0 && p.x <= gas.box && p.y >= 0 && p.y <= gas.box;
    check(inside, "все молекулы внутри сосуда");
}

struct Samples {
    std::vector<double> speed_a, rel_aa, rel_ab, vx_a;
};

// Выборки в равновесии: скорости молекул A, относительные скорости пар AA и AB.
Samples equilibrated_samples(int n_a, int n_b, double m_a, double m_b, double T)
{
    Gas gas(n_a, n_b, m_a, m_b, T, 4);
    for (int s = 0; s < 1500; ++s)  // установление равновесия
        gas.step();
    std::mt19937_64 rng(4);
    std::vector<int> a = gas.indices_of(0), b = gas.indices_of(1);
    std::uniform_int_distribution<size_t> pick_a(0, a.size() - 1);
    std::uniform_int_distribution<size_t> pick_b(0, b.empty() ? 0 : b.size() - 1);
    Samples out;
    for (int step = 0; step < 3000; ++step) {
        gas.step();
        if (step % 10)
            continue;
        for (int k : a) {
            out.speed_a.push_back(gas.vel[k].length());
            out.vx_a.push_back(gas.vel[k].x);
        }
        for (int n = 0; n < 100; ++n) {
            int i = a[pick_a(rng)], j = a[pick_a(rng)];
            if (i != j)
                out.rel_aa.push_back((gas.vel[i] - gas.vel[j]).length());
            if (!b.empty())
                out.rel_ab.push_back((gas.vel[a[pick_a(rng)]] - gas.vel[b[pick_b(rng)]]).length());
        }
    }
    return out;
}

void test_relative_speed_is_sqrt2_larger()
{
    Samples s = equilibrated_samples(250, 0, 30, 30, 300);
    double ratio = mean_of(s.rel_aa) / mean_of(s.speed_a);
    check(std::fabs(ratio - std::sqrt(2.0)) < 0.04 * std::sqrt(2.0), "<|v_отн|> / <|v|> ≈ √2");
    double sigma = theory::sigma_for(30, 300);
    check(std::fabs(mean_of(s.speed_a) - theory::mean(Kind::Modulus, sigma)) < 0.03 * mean_of(s.speed_a),
          "<|v|> совпадает с теорией");
    double var = variance_of(s.vx_a);
    check(std::fabs(var - K_B * 300 / (30 * AMU)) < 0.05 * var, "D(v_x) = kT/m");
}

void test_mixture_uses_reduced_mass()
{
    Samples s = equilibrated_samples(200, 60, 10, 90, 300);
    double mu = theory::reduced_mass(10, 90);
    double expected = theory::mean(Kind::Modulus, theory::sigma_for(mu, 300));
    check(std::fabs(mean_of(s.rel_ab) - expected) < 0.05 * expected, "<|v_отн|> для смеси — с приведённой массой");
}

void test_radius_grows_with_mass_within_bounds()
{
    std::vector<double> masses = {1, 4, 28, 100, 200, 500};
    std::vector<double> r;
    for (double m : masses)
        r.push_back(radius_for_mass(m));
    check(close(r[0], R_MAX / std::cbrt(M_MAX)) && close(r[4], R_MAX) && close(r[5], R_MAX), "границы радиусов");
    bool growing = true;
    for (int k = 1; k < 5; ++k)
        growing = growing && r[k] > r[k - 1];
    check(growing, "радиус растёт с массой");
    check(close(r[2] / r[1], std::cbrt(28.0 / 4.0)), "r2/r1 = (m2/m1)^(1/3)");
}

// ----------------------------------------------------------------------
// Теория
// ----------------------------------------------------------------------

// Интеграл плотности методом трапеций.
double integrate_pdf(Kind kind, double s, double high, int n = 200000)
{
    double h = high / n, sum = 0;
    for (int k = 0; k <= n; ++k)
        sum += theory::pdf(kind, k * h, s) * ((k == 0 || k == n) ? 0.5 : 1.0);
    return sum * h;
}

void test_energy_pdf_is_normalised()
{
    double kt = 4.14;
    check(std::fabs(integrate_pdf(Kind::Energy, kt, 60 * kt) - 1.0) < 1e-3, "∫f(E)dE = 1");
    check(std::fabs(integrate_pdf(Kind::Modulus, 400.0, 3000) - 1.0) < 1e-3, "∫f(v)dv = 1");
    check(theory::mean(Kind::Energy, kt) == kt && theory::variance(Kind::Energy, kt) == kt * kt, "<E> = kT, D = (kT)²");
}

// ----------------------------------------------------------------------
// Статистика
// ----------------------------------------------------------------------

void test_histogram_density_normalised()
{
    Histogram h(0, 10, 20);
    std::mt19937_64 rng(0);
    std::uniform_real_distribution<double> u(0, 10);
    for (int k = 0; k < 10000; ++k)
        h.add(u(rng));
    check(close(sum_of(h.density()) * h.width(), 1.0), "плотность нормирована");
    check(h.bin_of(0.1) == 0 && h.bin_of(9.99) == 19 && !h.bin_of(11), "номера столбиков");
}

void test_time_series_keeps_whole_history()
{
    TimeSeries ts(100);
    for (int k = 0; k < 1000; ++k)
        ts.add(k, 2.0 * k * (k % 2 ? 1 : -1));  // пила: 0, 2, -4, 6, -8, ...
    const auto& b = ts.buckets();
    check(b.size() <= 100 && b.size() >= 50, "корзин не больше capacity");
    check(b.front().t0 == 0.0 && b.back().t1 == 999.0, "история от 0 до последнего отсчёта");
    bool ordered = true;
    double lo = INFINITY, hi = -INFINITY;
    for (size_t k = 0; k < b.size(); ++k) {
        ordered = ordered && b[k].t0 <= b[k].t1 && (k == 0 || b[k].t0 > b[k - 1].t1);
        lo = std::min(lo, b[k].min);
        hi = std::max(hi, b[k].max);
    }
    check(ordered, "корзины по порядку и не перекрываются");
    check(lo == -2.0 * 998 && hi == 2.0 * 999, "пики не потерялись при слиянии");
    check(ts.last()->first == 999.0 && ts.count() == 1000, "последний отсчёт");
}

void test_lazy_forgetting_matches_explicit()
{
    std::mt19937_64 rng(1);
    std::uniform_real_distribution<double> u(0, 10);
    Histogram h(0, 10, 20);
    h.renormalize_at = 1e6;  // чтобы в тесте сработала и перенормировка
    std::vector<double> counts(20, 0.0);
    double total = 0, s = 0;
    for (int n = 0; n < 3000; ++n) {
        double x = u(rng);
        h.forget(0.99);
        for (double& c : counts)
            c *= 0.99;
        total *= 0.99;
        s *= 0.99;
        h.add(x);
        counts[static_cast<int>(x / 0.5)] += 1;
        total += 1;
        s += x;
    }
    bool same = true;
    std::vector<double> hc = h.counts();
    for (int k = 0; k < 20; ++k)
        same = same && close(hc[k], counts[k], 1e-7);
    check(same && close(h.total(), total, 1e-7) && close(h.mean(), s / total, 1e-7),
          "ленивое забывание = явное умножение на factor");
}

void test_rebin_keeps_samples()
{
    Histogram h(0, 10, 20);
    std::mt19937_64 rng(2);
    std::uniform_real_distribution<double> u(2, 8);
    for (int k = 0; k < 1000; ++k)
        h.add(u(rng));
    double mean = h.mean(), total = h.total();
    h.rebin(0, 20);
    check(close(h.total(), total) && close(h.mean(), mean), "сумма и среднее не меняются");
    check(close(sum_of(h.counts()), total), "всё попало в новый диапазон");
    check(close(h.high(), 20), "новая граница");
}

void test_rebin_to_other_bin_count()
{
    Histogram h(0, 10, 30);
    std::mt19937_64 rng(3);
    std::uniform_real_distribution<double> u(0, 10);
    for (int k = 0; k < 3000; ++k)
        h.add(u(rng));
    double total = h.total();
    h.rebin(0, 10, 10);
    check(h.bins() == 10 && close(sum_of(h.counts()), total), "30 → 10 столбиков без потерь");
    check(close(sum_of(h.density()) * h.width(), 1.0), "плотность нормирована");
    // Мельче: веса делятся пропорционально перекрытию — без пустых "через один" столбиков
    h.rebin(0, 10, 40);
    bool positive = true;
    for (double c : h.counts())
        positive = positive && c > 0;
    check(close(sum_of(h.counts()), total) && positive, "10 → 40 столбиков без пустых");
}

// ----------------------------------------------------------------------
// Эксперимент
// ----------------------------------------------------------------------

// В двумерном газе средняя кинетическая энергия молекулы равна kT (две степени свободы).
void test_mean_energy_is_kT_in_equilibrium()
{
    Experiment exp(5);
    exp.ensemble = true;
    exp.advance(3000);
    const Histogram& h = exp.hist.at({Obj::Single, Kind::Energy});
    double kt = K_B * exp.temperature / ENERGY_UNIT;
    check(close(exp.scale(Obj::Single, Kind::Energy), kt), "масштаб энергии = kT");
    check(std::fabs(h.mean() - kt) < 0.05 * kt, "<E> ≈ kT");
}

// Температура и массы меняются без сброса статистики; газ остаётся тем же.
void test_temperature_and_mass_change_keep_statistics()
{
    Experiment exp(7);
    exp.advance(500);
    Quantity q{Obj::Pair, Kind::Modulus};
    double total = exp.hist.at(q).total();
    const Gas* gas = exp.gas.get();
    exp.set_temperature(600);
    check(exp.gas.get() == gas && close(exp.hist.at(q).total(), total), "смена T не сбрасывает статистику");
    check(close(exp.hist.at(q).high(), exp.value_range(Kind::Modulus, Obj::Pair).second), "диапазон под новую T");
    check(close(gas->kinetic_energy(), gas->n() * K_B * 600), "энергия соответствует новой T");

    std::vector<double> energy_before;
    for (int k = 0; k < gas->n(); ++k)
        energy_before.push_back(0.5 * gas->mass[k] * gas->vel[k].length_sq());
    GasParams p = exp.params;
    p.mass_a = 4;  // только масса A
    exp.configure_gas(p);
    check(exp.gas.get() == gas && close(exp.hist.at(q).total(), total * 1.0, 1e-9), "смена массы не сбрасывает статистику");
    bool same_energy = true, mass_ok = true;
    for (int k = 0; k < gas->n(); ++k) {
        same_energy = same_energy && close(0.5 * gas->mass[k] * gas->vel[k].length_sq(), energy_before[k]);
        mass_ok = mass_ok && gas->mass[k] == 4;
    }
    check(same_energy, "энергия каждой молекулы (а значит T) сохранилась");
    check(mass_ok && gas->find_close_pairs().empty(), "новые массы, перекрытий нет");

    p.n_total = 100;  // другое число молекул — новый газ
    exp.configure_gas(p);
    check(exp.hist.at(q).total() == 0, "новое число молекул — статистика с нуля");
}

void test_memory_setting_keeps_statistics()
{
    Experiment exp(8);
    exp.advance(300);
    Quantity q{Obj::Pair, Kind::Modulus};
    double total = exp.hist.at(q).total(), tau = exp.memory_time();
    exp.set_memory(30);
    check(close(exp.hist.at(q).total(), total) && close(exp.memory_time(), tau / 10), "память меняется без сброса");
}

void test_restart_history_keeps_histograms()
{
    Experiment exp(9);
    exp.advance(500);
    Quantity q{Obj::Pair, Kind::Modulus};
    double total = exp.hist.at(q).total();
    exp.restart_history();
    check(exp.series.at(q).count() == 0 && !exp.series.at(q).last(), "история во времени начата заново");
    check(close(exp.hist.at(q).total(), total), "гистограмма не тронута");
}

// Опыт из лекции 8: все молекулы стартуют с одной скоростью в одну сторону.
void test_beam_start_relaxes_only_with_collisions()
{
    double T = 300, m = 28;
    Gas beam(150, 0, m, m, T, 11, Start::Beam);
    double v0 = beam.vel[0].length();
    bool same = true;
    for (Vec2 v : beam.vel)
        same = same && close(v.length(), v0) && close(v.x, beam.vel[0].x);
    check(same, "в начале у всех одна и та же скорость");
    check(close(beam.kinetic_energy(), beam.n() * K_B * T), "энергия всё равно N·k·T");

    // Без столкновений (только стенки) модули скоростей не меняются никогда
    Gas walls(150, 0, m, m, T, 11, Start::Beam);
    walls.collisions_enabled = false;
    for (int s = 0; s < 3000; ++s)
        walls.step();
    bool kept = true;
    for (Vec2 v : walls.vel)
        kept = kept && close(v.length(), v0, 1e-9);
    check(kept && walls.collisions == 0, "без столкновений |v| не меняются");

    // Со столкновениями устанавливается распределение Максвелла (Рэлей по модулю)
    for (int s = 0; s < 6000; ++s)
        beam.step();
    std::vector<double> speed;
    for (int s = 0; s < 3000; ++s) {
        beam.step();
        if (s % 50 == 0)
            for (Vec2 v : beam.vel)
                speed.push_back(v.length());
    }
    double sigma = theory::sigma_for(m, T);
    double d_theory = theory::variance(Kind::Modulus, sigma);
    check(std::fabs(variance_of(speed) - d_theory) < 0.15 * d_theory, "со столкновениями D(|v|) → (2 − π/2)·kT/m");
    check(std::fabs(mean_of(speed) - theory::mean(Kind::Modulus, sigma)) < 0.05 * mean_of(speed), "⟨|v|⟩ → √(πkT/2m)");
}

}  // namespace

int main()
{
    const std::vector<std::pair<const char*, std::function<void()>>> tests = {
        {"initial_energy_matches_temperature", test_initial_energy_matches_temperature},
        {"collision_conserves_energy_and_momentum", test_collision_conserves_energy_and_momentum},
        {"energy_conserved_over_many_steps", test_energy_conserved_over_many_steps},
        {"relative_speed_is_sqrt2_larger", test_relative_speed_is_sqrt2_larger},
        {"mixture_uses_reduced_mass", test_mixture_uses_reduced_mass},
        {"radius_grows_with_mass_within_bounds", test_radius_grows_with_mass_within_bounds},
        {"energy_pdf_is_normalised", test_energy_pdf_is_normalised},
        {"histogram_density_normalised", test_histogram_density_normalised},
        {"time_series_keeps_whole_history", test_time_series_keeps_whole_history},
        {"lazy_forgetting_matches_explicit", test_lazy_forgetting_matches_explicit},
        {"rebin_keeps_samples", test_rebin_keeps_samples},
        {"rebin_to_other_bin_count", test_rebin_to_other_bin_count},
        {"mean_energy_is_kT_in_equilibrium", test_mean_energy_is_kT_in_equilibrium},
        {"temperature_and_mass_change_keep_statistics", test_temperature_and_mass_change_keep_statistics},
        {"memory_setting_keeps_statistics", test_memory_setting_keeps_statistics},
        {"restart_history_keeps_histograms", test_restart_history_keeps_histograms},
        {"beam_start_relaxes_only_with_collisions", test_beam_start_relaxes_only_with_collisions},
    };
    for (const auto& [name, run] : tests) {
        current_test = name;
        int before = failures;
        run();
        std::printf("%s %s\n", failures == before ? "ok  " : "FAIL", name);
    }
    std::printf("%s: %d проверок не прошло\n", failures ? "ОШИБКИ" : "ВСЁ ХОРОШО", failures);
    return failures;
}
