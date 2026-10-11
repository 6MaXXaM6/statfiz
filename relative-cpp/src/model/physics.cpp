// Модель двумерного газа твёрдых дисков: начальные условия, шаг, столкновения.

#include "model/physics.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <stdexcept>

namespace physics {

double radius_for_mass(double mass_amu)
{
    double m = std::clamp(mass_amu, 1.0, M_MAX);
    return R_MAX * std::cbrt(m / M_MAX);
}

double thermal_sigma(double mass_amu, double temperature)
{
    return std::sqrt(K_B * temperature / (mass_amu * AMU));
}

Gas::Gas(int n_a_, int n_b_, double mass_a, double mass_b, double temperature_, unsigned seed, Start start)
    : n_a(n_a_), n_b(n_b_), temperature(temperature_), rng_(seed)
{
    int count = n_a + n_b;
    if (count < 1 || count > MAX_PARTICLES)
        throw std::invalid_argument("число молекул должно быть от 1 до 300");

    species.assign(count, 0);
    std::fill(species.begin() + n_a, species.end(), 1);
    for (int s : species) {
        mass.push_back(s == 0 ? mass_a : mass_b);
        radius.push_back(radius_for_mass(mass.back()));
    }
    random_positions();
    if (start == Start::Beam)
        beam_velocities();
    else
        maxwell_velocities();
    dt = recommended_dt();
}

// ----------------------------------------------------------------------
// Начальные условия
// ----------------------------------------------------------------------

// Случайные неперекрывающиеся положения: по одной молекуле в случайной клетке сетки.
void Gas::random_positions()
{
    double r_max = max_radius();
    double cell = 2.05 * r_max;
    int per_side = static_cast<int>(box / cell);

    // Перемешиваем номера клеток и берём первые n: все клетки разные.
    std::vector<int> cells(per_side * per_side);
    std::iota(cells.begin(), cells.end(), 0);
    std::shuffle(cells.begin(), cells.end(), rng_);

    // Небольшой случайный сдвиг внутри клетки, чтобы не было видно сетки.
    double margin = cell / 2 - r_max;
    std::uniform_real_distribution<double> jitter(-margin, margin);
    double offset = (box - per_side * cell) / 2;
    pos.resize(n());
    for (int k = 0; k < n(); ++k) {
        int cx = cells[k] % per_side;
        int cy = cells[k] / per_side;
        pos[k] = {offset + (cx + 0.5) * cell + jitter(rng_),
                  offset + (cy + 0.5) * cell + jitter(rng_)};
    }
}

// Скорости по распределению Максвелла (каждая проекция — Гаусс с sigma² = kT/m),
// затем точная подгонка полной энергии под T.
void Gas::maxwell_velocities()
{
    std::normal_distribution<double> normal(0.0, 1.0);
    vel.resize(n());
    for (int k = 0; k < n(); ++k) {
        double sigma = thermal_sigma(mass[k], temperature);
        vel[k] = {normal(rng_) * sigma, normal(rng_) * sigma};
    }
    set_temperature(temperature);
}

// Все молекулы летят в одну сторону (угол BEAM_ANGLE к оси x) с одинаковой энергией kT:
// m·v²/2 = kT, т.е. |v| = sqrt(2kT/m). Полная энергия сразу N·k·T, а распределение
// скоростей — "столбик", далёкий от максвелловского.
void Gas::beam_velocities()
{
    double angle = settings::BEAM_ANGLE * M_PI / 180.0;
    Vec2 direction(std::cos(angle), std::sin(angle));
    vel.resize(n());
    for (int k = 0; k < n(); ++k)
        vel[k] = direction * (std::sqrt(2.0) * thermal_sigma(mass[k], temperature));
}

// ----------------------------------------------------------------------
// Управление параметрами
// ----------------------------------------------------------------------

double Gas::kinetic_energy() const
{
    double e = 0.0;
    for (int k = 0; k < n(); ++k)
        e += 0.5 * mass[k] * AMU * vel[k].length_sq();
    return e;
}

Vec2 Gas::momentum() const
{
    Vec2 p;
    for (int k = 0; k < n(); ++k)
        p += vel[k] * (mass[k] * AMU);
    return p;
}

// Меняет температуру, умножая все скорости на один коэффициент.
// В двумерном газе на молекулу приходится энергия kT (две степени свободы),
// поэтому полная энергия должна быть равна N·k·T.
void Gas::set_temperature(double temperature_)
{
    temperature = temperature_;
    double target = n() * K_B * temperature;
    double current = kinetic_energy();
    if (current > 0) {
        double k = std::sqrt(target / current);
        for (Vec2& v : vel)
            v *= k;
    }
    dt = recommended_dt();
}

// Новые массы без пересоздания газа: молекулы остаются на местах.
// Радиусы меняются вслед за массами. Скорости умножаются на sqrt(m_старая / m_новая),
// так что энергия каждой молекулы, а значит и температура, сохраняются; меняется
// только распределение скоростей — газ сам придёт к новому равновесию.
void Gas::set_masses(double mass_a, double mass_b)
{
    for (int k = 0; k < n(); ++k) {
        double old = mass[k];
        mass[k] = species[k] == 0 ? mass_a : mass_b;
        radius[k] = radius_for_mass(mass[k]);
        vel[k] *= std::sqrt(old / mass[k]);
    }
    separate_overlaps();
    dt = recommended_dt();
}

// Раздвинуть перекрывшиеся диски (например, после того как радиусы выросли).
void Gas::separate_overlaps(int max_rounds)
{
    for (int round = 0; round < max_rounds; ++round) {
        auto pairs = find_close_pairs();
        if (pairs.empty())
            return;
        for (auto [i, j] : pairs) {
            Vec2 d = pos[j] - pos[i];
            double dist = d.length();
            if (dist > 0)
                push_apart(i, j, d * (1.0 / dist), dist);
        }
        for (int k = 0; k < n(); ++k)
            clamp_inside(k);
    }
}

// Шаг по времени (пс): быстрая молекула за шаг смещается не более чем на 1/4 радиуса.
double Gas::recommended_dt() const
{
    double m_min = *std::min_element(mass.begin(), mass.end());
    double r_min = *std::min_element(radius.begin(), radius.end());
    double v_fast = 4.0 * thermal_sigma(m_min, temperature);
    return 0.25 * r_min / (v_fast * NM_PER_MS_PS);
}

// ----------------------------------------------------------------------
// Шаг моделирования
// ----------------------------------------------------------------------

void Gas::step(double step_dt)
{
    double shift = step_dt * NM_PER_MS_PS;
    for (int k = 0; k < n(); ++k)
        pos[k] += vel[k] * shift;
    bounce_walls();
    if (collisions_enabled)
        collide();
    time += step_dt;
}

// Зеркальное отражение от стенок: меняется знак нормальной к стенке проекции скорости.
void Gas::bounce_walls()
{
    for (int k = 0; k < n(); ++k) {
        double r = radius[k];
        if ((pos[k].x < r && vel[k].x < 0) || (pos[k].x > box - r && vel[k].x > 0))
            vel[k].x = -vel[k].x;
        if ((pos[k].y < r && vel[k].y < 0) || (pos[k].y > box - r && vel[k].y > 0))
            vel[k].y = -vel[k].y;
        clamp_inside(k);  // возвращаем внутрь, если молекула успела "залезть" в стенку
    }
}

// Пары перекрывающихся дисков методом "сортировки и прохода" (sort and sweep):
// молекулы сортируются по x; каждая сравнивается только с соседями по этому списку,
// пока расстояние по x не превысит наибольшую сумму радиусов. Так не нужен перебор
// всех N² пар.
std::vector<std::pair<int, int>> Gas::find_close_pairs() const
{
    std::vector<std::pair<int, int>> found;
    std::vector<int> order(n());
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [this](int a, int b) { return pos[a].x < pos[b].x; });

    double reach = 2.0 * max_radius();
    for (int a = 0; a < n(); ++a) {
        int i = order[a];
        for (int b = a + 1; b < n(); ++b) {
            int j = order[b];
            if (pos[j].x - pos[i].x >= reach)
                break;  // дальше по списку молекулы только правее
            double touch = radius[i] + radius[j];
            if ((pos[j] - pos[i]).length_sq() < touch * touch)
                found.emplace_back(i, j);
        }
    }
    return found;
}

// Упругий удар дисков. Скорости меняются только вдоль линии центров (normal):
// так сохраняются и импульс, и энергия:
//     v_i += 2 m_j / (m_i + m_j) · (Δv·n) n,   v_j -= 2 m_i / (m_i + m_j) · (Δv·n) n.
void Gas::collide()
{
    for (auto [i, j] : find_close_pairs()) {
        Vec2 d = pos[j] - pos[i];
        double dist = d.length();
        if (dist == 0)
            continue;
        Vec2 normal = d * (1.0 / dist);
        double vn = (vel[j] - vel[i]).dot(normal);
        if (vn < 0) {  // молекулы сближаются — удар
            double mi = mass[i];
            double mj = mass[j];
            vel[i] += normal * (2.0 * mj / (mi + mj) * vn);
            vel[j] -= normal * (2.0 * mi / (mi + mj) * vn);
            ++collisions;
        }
        push_apart(i, j, normal, dist);
    }
}

// Раздвинуть перекрывшиеся диски i и j вдоль линии центров (на скорости и энергию не влияет).
void Gas::push_apart(int i, int j, Vec2 normal, double dist)
{
    double overlap = radius[i] + radius[j] - dist;
    if (overlap > 0) {
        pos[i] -= normal * (0.5 * overlap);
        pos[j] += normal * (0.5 * overlap);
    }
}

void Gas::clamp_inside(int k)
{
    double r = radius[k];
    pos[k].x = std::clamp(pos[k].x, r, box - r);
    pos[k].y = std::clamp(pos[k].y, r, box - r);
}

double Gas::max_radius() const
{
    return *std::max_element(radius.begin(), radius.end());
}

// Среднее время (пс) между столкновениями молекулы k — оценка кинетической теории (2D).
// Относительно молекулы сорта s молекула k движется со средней скоростью
// <u> = sqrt(pi/2)·sqrt(kT/mu) и "заметает" полосу шириной 2(r_k + r_s),
// поэтому частота столкновений nu = sum_s n_s · 2(r_k + r_s) · <u>.
double Gas::collision_time(int k) const
{
    double area = box * box;
    double rate = 0.0;  // 1/пс
    for (int s = 0; s < 2; ++s) {
        std::vector<int> others = indices_of(s);
        int count = static_cast<int>(others.size()) - (species[k] == s ? 1 : 0);
        if (count <= 0)
            continue;
        int o = others.front();
        double mu = mass[k] * mass[o] / (mass[k] + mass[o]);
        double mean_u = std::sqrt(M_PI / 2) * thermal_sigma(mu, temperature) * NM_PER_MS_PS;  // нм/пс
        rate += count / area * 2 * (radius[k] + radius[o]) * mean_u;
    }
    return rate > 0 ? 1.0 / rate : std::numeric_limits<double>::infinity();
}

// ----------------------------------------------------------------------
// Вспомогательное
// ----------------------------------------------------------------------

int Gas::nearest(double x, double y, double max_dist) const
{
    int best = -1;
    double best_d = max_dist;
    for (int k = 0; k < n(); ++k) {
        double d = (pos[k] - Vec2(x, y)).length();
        if (d <= best_d) {
            best = k;
            best_d = d;
        }
    }
    return best;
}

std::vector<int> Gas::indices_of(int sort) const
{
    std::vector<int> result;
    for (int k = 0; k < n(); ++k)
        if (species[k] == sort)
            result.push_back(k);
    return result;
}

}  // namespace physics
