// Накопление статистики: гистограммы и временные ряды.

#pragma once

#include <optional>
#include <utility>
#include <vector>

// Гистограмма с фиксированными границами + точные среднее и дисперсия.
//
// Отсчёты могут "забываться" (forget): тогда total — не число отсчётов, а их суммарный вес.
//
// Забывание "ленивое": вместо того чтобы на каждом шаге умножать все столбики на
// factor < 1, новые отсчёты добавляются с растущим весом gain (gain делится на factor).
// Отношения весов те же, а работы на шаг — одно деление. Наружу (counts, total)
// всё отдаётся уже поделённым на gain; изредка gain сбрасывается в 1, чтобы не было
// переполнения.
class Histogram {
public:
    Histogram(double low, double high, int bins = 30);

    void reset();
    void forget(double factor);  // вес всех прежних отсчётов умножается на factor < 1
    void add(double x, double weight = 1.0);
    void add(const std::vector<double>& values, double weight = 1.0);
    void rebin(double low, double high, int bins = 0);  // bins = 0 — прежнее число столбиков

    int bins() const { return bins_; }
    double low() const { return low_; }
    double high() const { return high_; }
    double width() const { return (high_ - low_) / bins_; }
    double edge(int k) const { return low_ + k * width(); }
    double center(int k) const { return low_ + (k + 0.5) * width(); }

    std::vector<double> counts() const;
    double total() const { return total_ / gain_; }
    std::optional<int> bin_of(double x) const;  // номер столбика или пусто, если за пределами
    std::vector<double> density() const;        // плотность вероятности (нормирована на 1)
    double mean() const;                        // NaN, если отсчётов нет
    double variance() const;

    double renormalize_at = 1e100;  // когда сбрасывать gain (в тестах — меньше)

private:
    void set_edges(double low, double high, int bins);
    void renormalize();

    double low_ = 0.0;
    double high_ = 1.0;
    int bins_ = 1;
    double inv_width_ = 1.0;
    std::vector<double> counts_;
    double total_ = 0.0;
    double sum_ = 0.0;
    double sum_sq_ = 0.0;
    double gain_ = 1.0;
};

// Вся история величины во времени в ограниченной памяти — "корзины min/max".
//
// История делится на корзины (Bucket): в каждой — промежуток времени, минимум,
// максимум, последнее значение, а также число, сумма и сумма квадратов попавших в неё
// отсчётов (из них — среднее и разброс за этот промежуток). Пока корзин мало, в каждой
// по одному отсчёту. Когда корзин становится capacity, соседние сливаются попарно
// (минимум из минимумов, максимум из максимумов), и дальше в корзину попадает вдвое
// больше отсчётов. Так:
//   * памяти — не больше capacity корзин, добавление отсчёта — O(1);
//   * ось времени всегда от начала до текущего момента ("схлопывающийся" график);
//   * ничего не теряется: min, max, среднее и дисперсия за любой промежуток точные
//     (при простом прореживании "каждая вторая точка" пики пропадали бы).
class TimeSeries {
public:
    struct Bucket {
        double t0, t1;      // время первого и последнего отсчёта в корзине
        double min, max;    // наименьшее и наибольшее значение
        double last;        // последнее значение (чтобы соединять корзины линией)
        double n, sum, sum_sq;  // число отсчётов, их сумма и сумма квадратов
    };

    // 4096 корзин — больше ширины графика в пикселях даже на весь экран 1920 px
    explicit TimeSeries(int capacity = 4096);

    void reset();
    void add(double t, double v);

    const std::vector<Bucket>& buckets() const { return buckets_; }
    long long span() const { return span_; }  // сколько отсчётов в одной полной корзине
    std::optional<std::pair<double, double>> last() const { return last_; }
    long long count() const { return count_; }

private:
    void merge_pairs();

    int capacity_;
    std::vector<Bucket> buckets_;
    long long span_ = 1;      // отсчётов в полной корзине
    long long in_last_ = 0;   // отсчётов в последней (незаполненной) корзине
    long long count_ = 0;     // сколько всего было отсчётов
    std::optional<std::pair<double, double>> last_;
};
