// Эксперимент: управление газом, выбор пары молекул и сбор статистики.

#include "model/experiment.h"

#include <algorithm>
#include <chrono>
#include <cmath>

using theory::Kind;

const std::vector<Obj> OBJECTS = {Obj::Pair, Obj::Single, Obj::Second};
const std::vector<Kind> KINDS = {Kind::Modulus, Kind::Projection, Kind::Energy};

Experiment::Experiment(unsigned seed) : rng_(seed)
{
    rebuild();
}

// ----------------------------------------------------------------------
// Состав газа и выбор молекул
// ----------------------------------------------------------------------

int Experiment::n_b() const
{
    if (params.mode == GasMode::Pure)
        return 0;
    return std::clamp(params.n_b, 1, params.n_total - 1);
}

// Новые параметры газа. Если изменились только массы или включение столкновений —
// газ остаётся тем же, статистика сохраняется (см. set_masses). Если изменились число,
// состав молекул или начальные скорости — газ создаётся заново.
void Experiment::configure_gas(const GasParams& p)
{
    bool same_molecules = p.mode == params.mode && p.n_total == params.n_total && p.n_b == params.n_b
                          && p.start == params.start;
    if (same_molecules) {
        params.collisions = p.collisions;
        gas->collisions_enabled = p.collisions;
        set_masses(p.mass_a, p.mass_b);
        return;
    }
    params = p;
    rebuild();
}

// Изменить массы, не начиная опыт заново: статистика не сбрасывается,
// старые отсчёты постепенно забываются, и видно, как газ приходит к новому равновесию.
void Experiment::set_masses(double mass_a, double mass_b)
{
    params.mass_a = mass_a;
    params.mass_b = mass_b;
    gas->set_masses(mass_a, mass_b);
    rescale_stats();
}

// Создаёт газ заново с текущими параметрами.
void Experiment::rebuild()
{
    int n_total = std::clamp(params.n_total, 2, physics::MAX_PARTICLES);
    int nb = n_b();
    gas = std::make_unique<physics::Gas>(n_total - nb, nb, params.mass_a, params.mass_b, temperature,
                                         static_cast<unsigned>(rng_()), params.start);
    gas->collisions_enabled = params.collisions;
    auto types = available_pair_types();
    if (std::find(types.begin(), types.end(), pair_type) == types.end())
        pair_type = types.front();
    choose_pair(pair_type);
}

std::vector<std::string> Experiment::available_pair_types() const
{
    std::vector<std::string> types;
    if (gas->n_a >= 2)
        types.push_back("AA");
    if (gas->n_a >= 1 && gas->n_b >= 1)
        types.push_back("AB");
    if (gas->n_b >= 2)
        types.push_back("BB");
    return types;
}

// Выбирает пару молекул нужных сортов (первые по списку).
void Experiment::choose_pair(const std::string& type)
{
    std::vector<int> a = gas->indices_of(0);
    std::vector<int> b = gas->indices_of(1);
    if (type == "AB") {
        i = a[0]; j = b[0];
    } else if (type == "BB") {
        i = b[0]; j = b[1];
    } else {
        i = a[0]; j = a[1];
    }
    pair_type = type;
    reset_stats();
}

// Пользователь щёлкнул по молекуле: which = 1 или 2.
void Experiment::select(int index, int which)
{
    if (which == 1) {
        if (index == j)
            j = i;
        i = index;
    } else {
        if (index == i)
            i = j;
        j = index;
    }
    std::string names = "AB";
    std::string type = {names[gas->species[i]], names[gas->species[j]]};
    std::sort(type.begin(), type.end());
    pair_type = type;
    reset_stats();
}

// Изменить температуру, не сбрасывая статистику (как и для масс).
void Experiment::set_temperature(double t)
{
    temperature = t;
    gas->set_temperature(t);
    rescale_stats();
}

// ----------------------------------------------------------------------
// Теория для выбранных молекул
// ----------------------------------------------------------------------

// Масса, которая входит в распределение: m1, m2 или приведённая масса пары.
double Experiment::mass(Obj obj) const
{
    switch (obj) {
    case Obj::Single: return mass_1();
    case Obj::Second: return mass_2();
    case Obj::Pair: break;
    }
    return reduced_mass();
}

// sqrt(kT/m) для молекулы или sqrt(kT/mu) для пары, м/с.
double Experiment::sigma(Obj obj) const
{
    return theory::sigma_for(mass(obj), temperature);
}

// Масштаб распределения: sqrt(kT/m) для скоростей, kT для энергии (в ENERGY_UNIT).
double Experiment::scale(Obj obj, Kind kind) const
{
    if (kind == Kind::Energy)
        return physics::K_B * temperature / ENERGY_UNIT;
    return sigma(obj);
}

std::pair<double, double> Experiment::value_range(Kind kind, Obj obj) const
{
    return theory::value_range(kind, scale(obj, kind));
}

// Наибольшее из sqrt(kT/m) для векторов v1, v2 и v_отн на диаграмме.
double Experiment::max_speed_scale() const
{
    double s = 0;
    for (Obj obj : OBJECTS)
        s = std::max(s, sigma(obj));
    return s;
}

// Время (пс), за которое вес старых отсчётов уменьшается в e раз.
double Experiment::memory_time() const
{
    return memory_collisions * gas->collision_time(i);
}

// ----------------------------------------------------------------------
// Статистика
// ----------------------------------------------------------------------

void Experiment::reset_stats()
{
    hist.clear();
    series.clear();
    for (Kind kind : KINDS) {
        for (Obj obj : OBJECTS) {
            auto [low, high] = value_range(kind, obj);
            hist.emplace(Quantity{obj, kind}, Histogram(low, high, bins));
            series.emplace(Quantity{obj, kind}, TimeSeries());
        }
    }
    steps_since_reset = 0;
    memory_time_ = memory_time();
}

// История величин во времени начинается заново (с текущего момента), а гистограммы
// остаются. Нужно при смене режима: после быстрого режима время опыта уходит далеко
// вперёд, история сильно прорежена, и в медленном режиме график почти не двигался бы.
void Experiment::restart_history()
{
    for (auto& [q, s] : series)
        s.reset();
}

// Сколько столкновений помнит статистика; накопленное не сбрасывается.
void Experiment::set_memory(int collisions)
{
    memory_collisions = collisions;
    memory_time_ = memory_time();
}

// Другое число столбиков; накопленная статистика переносится в новые столбики.
void Experiment::set_bins(int n)
{
    bins = n;
    for (auto& [q, h] : hist)
        h.rebin(h.low(), h.high(), bins);
}

// После изменения T или масс: перенести гистограммы на новые диапазоны значений
// и пересчитать время памяти (оно зависит от частоты столкновений).
void Experiment::rescale_stats()
{
    for (auto& [q, h] : hist) {
        auto [low, high] = value_range(q.kind, q.obj);
        h.rebin(low, high);
    }
    memory_time_ = memory_time();
}

// Вектор скорости молекулы 1, молекулы 2 или относительной скорости v1 - v2.
Vec2 Experiment::velocity(Obj obj) const
{
    Vec2 v1 = gas->vel[i];
    Vec2 v2 = gas->vel[j];
    switch (obj) {
    case Obj::Single: return v1;
    case Obj::Second: return v2;
    case Obj::Pair: break;
    }
    return v1 - v2;
}

// Модуль, проекция и кинетическая энергия для скорости v.
// Энергия: m·|v|²/2, для пары — mu·|v_отн|²/2 (энергия относительного движения).
Experiment::Values Experiment::values(Obj obj, Vec2 v) const
{
    double speed_sq = v.length_sq();
    double energy = 0.5 * mass(obj) * physics::AMU * speed_sq / ENERGY_UNIT;
    return {std::sqrt(speed_sq), v.x, energy};
}

void Experiment::add_to_hist(Obj obj, Vec2 v)
{
    Values x = values(obj, v);
    hist.at({obj, Kind::Modulus}).add(x.modulus);
    hist.at({obj, Kind::Projection}).add(x.projection);
    hist.at({obj, Kind::Energy}).add(x.energy);
}

// Отсчёт для выбранных молекул: в гистограммы и во временные ряды.
void Experiment::sample_selected()
{
    double t = gas->time;
    for (Obj obj : OBJECTS) {
        Vec2 v = velocity(obj);
        add_to_hist(obj, v);
        Values x = values(obj, v);
        series.at({obj, Kind::Modulus}).add(t, x.modulus);
        series.at({obj, Kind::Projection}).add(t, x.projection);
        series.at({obj, Kind::Energy}).add(t, x.energy);
    }
}

// Та же статистика, но сразу по многим молекулам того же сорта, что и выбранные.
void Experiment::sample_ensemble()
{
    std::vector<int> same_1 = gas->indices_of(gas->species[i]);
    std::vector<int> same_2 = gas->indices_of(gas->species[j]);
    for (int k : same_1)
        add_to_hist(Obj::Single, gas->vel[k]);
    for (int k : same_2)
        add_to_hist(Obj::Second, gas->vel[k]);
    // Случайные пары: первая молекула из сорта молекулы 1, вторая — из сорта молекулы 2.
    std::uniform_int_distribution<size_t> pick_1(0, same_1.size() - 1);
    std::uniform_int_distribution<size_t> pick_2(0, same_2.size() - 1);
    for (size_t n = 0; n < same_1.size(); ++n) {
        int p = same_1[pick_1(rng_)];
        int q = same_2[pick_2(rng_)];
        if (p != q)
            add_to_hist(Obj::Pair, gas->vel[p] - gas->vel[q]);
    }
}

// Экспоненциальное забывание: за время dt вес старых отсчётов умножается на exp(-dt/tau).
void Experiment::forget(double dt)
{
    double factor = std::exp(-dt / memory_time_);
    for (auto& [q, h] : hist)
        h.forget(factor);
}

// ----------------------------------------------------------------------
// Ход расчёта
// ----------------------------------------------------------------------

// n_steps шагов моделирования; после каждого — отсчёт для выбранных молекул.
void Experiment::advance(int n_steps, double dt)
{
    if (dt <= 0)
        dt = gas->dt;
    for (int s = 0; s < n_steps; ++s) {
        gas->step(dt);
        forget(dt);
        sample_selected();
        ++steps_since_reset;
        if (ensemble && steps_since_reset % settings::ENSEMBLE_EVERY == 0)
            sample_ensemble();
    }
}

// Смоделировать время factor·dt (шагами не длиннее dt).
void Experiment::advance_by(double factor)
{
    int n = std::max(1, static_cast<int>(std::ceil(factor)));
    advance(n, gas->dt * factor / n);
}

// Считать шагами dt, пока не пройдёт seconds секунд реального времени.
void Experiment::advance_for_seconds(double seconds, int chunk)
{
    using clock = std::chrono::steady_clock;
    auto started = clock::now();
    while (std::chrono::duration<double>(clock::now() - started).count() < seconds)
        advance(chunk);
}
