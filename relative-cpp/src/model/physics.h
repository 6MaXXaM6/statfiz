// Модель двумерного идеального газа из твёрдых дисков.
//
// Единицы измерения внутри модели:
//     координаты  — нм (нанометры),
//     скорости    — м/с,
//     время       — пс (пикосекунды),
//     массы       — а.е.м.,
//     температура — К.
// За время dt [пс] частица со скоростью v [м/с] проходит v * dt * 1e-3 нм.
//
// Газ может состоять из двух сортов молекул: A (основной) и B (второй газ
// или одна "чужая" частица). Столкновения — абсолютно упругие удары дисков,
// со стенками — зеркальное отражение.
//
// Этот файл ничего не знает об интерфейсе: только физика.

#pragma once

#include <random>
#include <utility>
#include <vector>

#include "model/vec2.h"
#include "settings.h"

namespace physics {

constexpr double K_B = 1.380649e-23;    // постоянная Больцмана, Дж/К
constexpr double AMU = 1.66053907e-27;  // атомная единица массы, кг

constexpr double BOX_SIZE = settings::BOX_SIZE;  // сторона квадратного сосуда, нм
constexpr int MAX_PARTICLES = settings::MAX_PARTICLES;

// Радиус молекулы пропорционален m^(1/3) (объём пропорционален массе), поэтому
// отношение размеров на экране честно показывает отношение масс.
// Самая тяжёлая молекула (M_MAX) имеет радиус R_MAX.
constexpr double M_MAX = settings::M_MAX;  // а.е.м.
constexpr double R_MAX = settings::R_MAX;  // нм

// Перевод: скорость [м/с] * время [пс] * NM_PER_MS_PS = путь [нм]
constexpr double NM_PER_MS_PS = 1e-3;

// Радиус молекулы (нм) по её массе (а.е.м.): r ∝ m^(1/3).
double radius_for_mass(double mass_amu);

// Среднеквадратичное значение одной проекции скорости sqrt(kT/m), м/с.
double thermal_sigma(double mass_amu, double temperature);

// Начальные скорости
enum class Start {
    Maxwell,  // по распределению Максвелла (газ сразу в равновесии)
    Beam,     // все с одной скоростью sqrt(2kT/m) в одну сторону (опыт из лекции 8:
              // равновесие устанавливается только благодаря столкновениям)
};

// Состояние газа и шаг моделирования.
class Gas {
public:
    Gas(int n_a, int n_b, double mass_a, double mass_b, double temperature, unsigned seed,
        Start start = Start::Maxwell);

    int n() const { return static_cast<int>(mass.size()); }

    // --- управление параметрами ---
    double kinetic_energy() const;  // полная кинетическая энергия, Дж
    Vec2 momentum() const;          // полный импульс, кг·м/с
    void set_temperature(double temperature);
    void set_masses(double mass_a, double mass_b);
    void separate_overlaps(int max_rounds = 200);
    double recommended_dt() const;

    // --- шаг моделирования ---
    void step(double dt);
    void step() { step(dt); }

    // Пары молекул (i, j), диски которых перекрываются.
    std::vector<std::pair<int, int>> find_close_pairs() const;

    // Среднее время (пс) между столкновениями молекулы k (оценка кинетической теории).
    double collision_time(int k) const;

    // --- вспомогательное ---
    int nearest(double x, double y, double max_dist) const;  // -1, если дальше max_dist
    std::vector<int> indices_of(int sort) const;

    // Состояние (открыто для чтения: его рисуют и по нему считают статистику).
    double box = BOX_SIZE;
    int n_a = 0;
    int n_b = 0;
    std::vector<int> species;     // 0 — сорт A, 1 — сорт B (молекулы B в конце)
    std::vector<double> mass;     // а.е.м.
    std::vector<double> radius;   // нм
    std::vector<Vec2> pos;        // нм
    std::vector<Vec2> vel;        // м/с
    double temperature = 300.0;   // К
    double time = 0.0;            // пс
    long long collisions = 0;
    double dt = 0.0;              // рекомендуемый шаг, пс
    bool collisions_enabled = true;  // false — молекулы пролетают друг сквозь друга (остаются только стенки)

private:
    void random_positions();
    void maxwell_velocities();
    void beam_velocities();
    void bounce_walls();
    void collide();
    void push_apart(int i, int j, Vec2 normal, double dist);
    void clamp_inside(int k);
    double max_radius() const;

    std::mt19937_64 rng_;
};

}  // namespace physics
