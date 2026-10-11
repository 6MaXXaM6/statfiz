// График величины во времени — "схлопывающийся": ось времени от начала опыта до сейчас.

#pragma once

#include <optional>
#include <vector>

#include "model/stats.h"
#include "ui/plots/plot_base.h"

// Кривая v(t), текущая точка, линия текущего значения и теоретическое среднее.
//
// Пока отсчётов меньше, чем столбцов пикселей, это обычная ломаная. Дальше в каждом
// столбце пикселей рисуются размах (min…max), разброс (среднее ± σ) и среднее значение
// попавших в него отсчётов — столбцов не больше ширины графика, сколько бы ни шёл опыт.
class TimePlot : public PlotBase {
public:
    explicit TimePlot(QWidget* parent = nullptr);

    // axis_label — подпись оси значений с единицами, например "|v₁|, м/с".
    void configure(const QString& axis_label, double low, double high);
    void update_view(const TimeSeries& series, std::optional<double> theory_mean);

protected:
    void draw_data(QPainter& p) override;

private:
    void draw_line(QPainter& p);
    void draw_columns(QPainter& p);

    const TimeSeries* series_ = nullptr;  // данные не копируются: график читает их при рисовании
    std::optional<double> theory_mean_;
};
