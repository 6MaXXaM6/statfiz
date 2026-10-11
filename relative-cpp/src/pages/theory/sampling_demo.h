// Живой пример к разделу "Как устроен опыт": случайные значения |v| (распределение Рэлея)
// складываются в гистограмму, и видно, как она приближается к теоретической кривой
// по мере роста числа отсчётов N (ошибка уменьшается примерно как 1/√N).

#pragma once

#include <QLabel>
#include <QPushButton>
#include <QTimer>
#include <QWidget>
#include <random>

#include "model/stats.h"
#include "ui/plots/hist_plot.h"

class SamplingDemo : public QWidget {
public:
    SamplingDemo();

    void add_samples(int n);
    void reset();

private:
    void update_view();

    double sigma_;           // sqrt(kT/m) для m = 28 а.е.м., T = 300 К
    Histogram hist_;
    HistPlot* plot_;
    QLabel* readout_;
    QPushButton* auto_button_;
    QTimer timer_;           // "Набирать": добавляет отсчёты сам, понемногу
    std::mt19937_64 rng_{1};
};
