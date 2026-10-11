// Гистограмма с ленивым забыванием и "схлопывающийся" временной ряд.

#include "model/stats.h"

#include <algorithm>
#include <cmath>
#include <limits>

// ----------------------------------------------------------------------
// Histogram
// ----------------------------------------------------------------------

Histogram::Histogram(double low, double high, int bins)
{
    set_edges(low, high, bins);
    reset();
}

void Histogram::set_edges(double low, double high, int bins)
{
    low_ = low;
    high_ = high;
    bins_ = bins;
    inv_width_ = bins / (high - low);
}

void Histogram::reset()
{
    counts_.assign(bins_, 0.0);
    total_ = sum_ = sum_sq_ = 0.0;
    gain_ = 1.0;
}

void Histogram::forget(double factor)
{
    gain_ /= factor;
    if (gain_ > renormalize_at)
        renormalize();
}

void Histogram::renormalize()
{
    for (double& c : counts_)
        c /= gain_;
    total_ /= gain_;
    sum_ /= gain_;
    sum_sq_ /= gain_;
    gain_ = 1.0;
}

void Histogram::add(double x, double weight)
{
    double w = weight * gain_;
    if (auto k = bin_of(x))
        counts_[*k] += w;
    total_ += w;
    sum_ += w * x;
    sum_sq_ += w * x * x;
}

void Histogram::add(const std::vector<double>& values, double weight)
{
    for (double x : values)
        add(x, weight);
}

// Новый диапазон или число столбиков без потери накопленного
// (например, после изменения температуры).
//
// Внутри старого столбика отсчёты считаются распределёнными равномерно, и его вес
// делится между новыми столбиками пропорционально перекрытию. То, что вышло за новый
// диапазон, в столбиках пропадает, но среднее и дисперсия (они считаются по самим
// значениям) остаются точными.
void Histogram::rebin(double low, double high, int bins)
{
    std::vector<double> old = counts_;
    double old_low = low_;
    double old_width = width();
    set_edges(low, high, bins > 0 ? bins : bins_);
    counts_.assign(bins_, 0.0);

    for (int k = 0; k < static_cast<int>(old.size()); ++k) {
        double a = old_low + k * old_width;   // границы старого столбика
        double b = a + old_width;
        // Новые столбики, с которыми он пересекается
        int first = std::max(0, static_cast<int>(std::floor((a - low_) * inv_width_)));
        int last = std::min(bins_ - 1, static_cast<int>(std::floor((b - low_) * inv_width_)));
        for (int j = first; j <= last; ++j) {
            double overlap = std::min(b, edge(j + 1)) - std::max(a, edge(j));
            if (overlap > 0)
                counts_[j] += old[k] * overlap / old_width;
        }
    }
}

std::vector<double> Histogram::counts() const
{
    std::vector<double> c(counts_);
    for (double& x : c)
        x /= gain_;
    return c;
}

std::optional<int> Histogram::bin_of(double x) const
{
    if (x < low_)
        return std::nullopt;
    int k = static_cast<int>((x - low_) * inv_width_);
    if (k >= bins_)
        return std::nullopt;
    return k;
}

std::vector<double> Histogram::density() const
{
    std::vector<double> d(bins_, 0.0);
    if (total_ == 0)
        return d;
    for (int k = 0; k < bins_; ++k)
        d[k] = counts_[k] / (total_ * width());
    return d;
}

double Histogram::mean() const
{
    if (total_ == 0)
        return std::numeric_limits<double>::quiet_NaN();
    return sum_ / total_;
}

double Histogram::variance() const
{
    if (total() < 1.5)
        return std::numeric_limits<double>::quiet_NaN();
    double m = sum_ / total_;
    return std::max(sum_sq_ / total_ - m * m, 0.0);
}

// ----------------------------------------------------------------------
// TimeSeries
// ----------------------------------------------------------------------

TimeSeries::TimeSeries(int capacity) : capacity_(capacity - capacity % 2)
{
    reset();
}

void TimeSeries::reset()
{
    buckets_.clear();
    buckets_.reserve(capacity_);
    span_ = 1;
    in_last_ = 0;
    count_ = 0;
    last_.reset();
}

void TimeSeries::add(double t, double v)
{
    if (buckets_.empty() || in_last_ == span_) {
        // Последняя корзина полна — начинаем новую (если места нет, сначала сливаем пары)
        if (static_cast<int>(buckets_.size()) == capacity_)
            merge_pairs();
        buckets_.push_back({t, t, v, v, v, 1, v, v * v});
        in_last_ = 1;
    } else {
        Bucket& b = buckets_.back();
        b.t1 = t;
        b.min = std::min(b.min, v);
        b.max = std::max(b.max, v);
        b.last = v;
        b.n += 1;
        b.sum += v;
        b.sum_sq += v * v;
        ++in_last_;
    }
    ++count_;
    last_ = std::make_pair(t, v);
}

// Все корзины полны: сливаем соседние пары, корзин становится вдвое меньше, а вмещают они вдвое больше.
void TimeSeries::merge_pairs()
{
    int half = capacity_ / 2;
    for (int k = 0; k < half; ++k) {
        const Bucket& a = buckets_[2 * k];
        const Bucket& b = buckets_[2 * k + 1];
        buckets_[k] = {a.t0, b.t1, std::min(a.min, b.min), std::max(a.max, b.max), b.last,
                       a.n + b.n, a.sum + b.sum, a.sum_sq + b.sum_sq};
    }
    buckets_.resize(half);
    span_ *= 2;
}
