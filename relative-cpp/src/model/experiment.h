// Эксперимент: газ + выбранные молекулы + накопленная статистика.
// Здесь нет ничего про интерфейс — только логика, которую показывает страница демонстрации.

#pragma once

#include <map>
#include <memory>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include "model/physics.h"
#include "model/stats.h"
#include "model/theory.h"
#include "settings.h"

// Что наблюдаем
enum class Obj {
    Pair,    // относительная скорость молекул 1 и 2: v_отн = v1 - v2
    Single,  // молекула 1
    Second,  // молекула 2
};

// Наблюдаемая величина: (что наблюдаем, какая величина), например (Pair, Modulus) = |v_отн|.
struct Quantity {
    Obj obj;
    theory::Kind kind;
    bool operator<(const Quantity& o) const { return std::make_pair(obj, kind) < std::make_pair(o.obj, o.kind); }
    bool operator==(const Quantity& o) const { return obj == o.obj && kind == o.kind; }
};

extern const std::vector<Obj> OBJECTS;
extern const std::vector<theory::Kind> KINDS;

constexpr double ENERGY_UNIT = 1e-21;  // энергия показывается в единицах 10⁻²¹ Дж (kT при 300 К ≈ 4.1)

// Состав газа
enum class GasMode {
    Pure,  // только газ A
    Mix,   // смесь газов A и B (при N_B = 1 — одна "чужая" молекула в газе A)
};

// Память статистики: старые отсчёты забываются экспоненциально, exp(-t/tau),
// tau = memory_collisions средних времён между столкновениями молекулы 1.
// По умолчанию settings::START_MEMORY = 300 — подобрано тестом (tools/forgetting_test.py
// в Python-версии): расстояние L1 между гистограммой |v_отн| (30 столбиков) и теорией —
// медиана 0.26 при K=100, 0.15 при K=300, 0.08 при K=1000. K=300 — шум уже мал, а память ещё короткая.

// Параметры газа, которые задаёт пользователь (панель "Газ").
struct GasParams {
    GasMode mode = GasMode::Pure;
    double mass_a = settings::START_MASS_A;  // а.е.м.
    double mass_b = settings::START_MASS_B;
    int n_total = settings::START_N;
    int n_b = settings::START_N_B;           // сколько молекул B в смеси
    physics::Start start = physics::Start::Maxwell;  // начальные скорости
    bool collisions = true;                  // сталкиваются ли молекулы друг с другом
};

class Experiment {
public:
    explicit Experiment(unsigned seed = std::random_device{}());

    // --- состав газа и выбор молекул ---
    int n_b() const;
    void configure_gas(const GasParams& params);
    void set_masses(double mass_a, double mass_b);
    void rebuild();
    std::vector<std::string> available_pair_types() const;
    void choose_pair(const std::string& pair_type);
    void select(int index, int which);
    void set_temperature(double temperature);

    // --- теория для выбранных молекул ---
    double mass_1() const { return gas->mass[i]; }
    double mass_2() const { return gas->mass[j]; }
    double reduced_mass() const { return theory::reduced_mass(mass_1(), mass_2()); }
    double mass(Obj obj) const;
    double sigma(Obj obj) const;
    double scale(Obj obj, theory::Kind kind) const;
    std::pair<double, double> value_range(theory::Kind kind, Obj obj) const;
    double max_speed_scale() const;
    double memory_time() const;

    // --- статистика ---
    void reset_stats();
    void restart_history();  // графики во времени — заново, гистограммы остаются
    void set_memory(int collisions);
    void set_bins(int bins);
    Vec2 velocity(Obj obj) const;

    // --- ход расчёта ---
    void advance(int n_steps, double dt = 0);
    void advance_by(double factor);
    void advance_for_seconds(double seconds, int chunk = 5);

    // Состояние
    GasParams params;
    double temperature = settings::START_TEMPERATURE;
    std::string pair_type = "AA";
    bool ensemble = false;  // добавлять ли статистику по всем молекулам (быстрый режим)
    int memory_collisions = settings::START_MEMORY;
    int bins = settings::START_BINS;

    std::unique_ptr<physics::Gas> gas;
    int i = 0, j = 1;  // номера выбранных молекул 1 и 2
    std::map<Quantity, Histogram> hist;
    std::map<Quantity, TimeSeries> series;
    long long steps_since_reset = 0;

private:
    struct Values { double modulus, projection, energy; };
    Values values(Obj obj, Vec2 v) const;
    void add_to_hist(Obj obj, Vec2 v);
    void rescale_stats();
    void sample_selected();
    void sample_ensemble();
    void forget(double dt);

    std::mt19937_64 rng_;
    double memory_time_ = 1.0;  // запомненное memory_time(): пересчитывается при изменении параметров
};
