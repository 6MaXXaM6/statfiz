// Панель графика: выбор величины, график во времени и распределение рядом с ним.

#pragma once

#include <QBoxLayout>
#include <QComboBox>
#include <QLabel>
#include <QWidget>
#include <vector>

#include "model/experiment.h"
#include "ui/plots/hist_plot.h"
#include "ui/plots/time_plot.h"

// Что можно выбрать в панели: |v_отн|, v_отн,x, |v₁|, v₁,x, |v₂|, v₂,x, E₁, E₂
extern const std::vector<Quantity> QUANTITIES;

// Одна величина: заголовок с выбором и текущим значением, x(t) + распределение, среднее и дисперсия.
//
// Распределение стоит боком рядом с графиком во времени (общая ось значений).
// Кнопка ↻ поворачивает его в обычный вид — тогда график во времени временно
// скрывается и распределение занимает всю панель.
//
// quantity_changed — выбрали другую величину; close_clicked — нажали ✕ (если панель можно закрыть).
class GraphPanel : public QWidget {
    Q_OBJECT
public:
    GraphPanel(Quantity quantity, bool closable);

    Quantity quantity() const;
    void show_quantity(Quantity q);   // выбрать величину программно (как будто её выбрали в списке)
    void set_side_stats(bool side);   // подписи справа от графиков (true) или под ними
    void rotate();
    // Диапазон значений и масштаб плотности задаёт страница (у двух панелей они могут быть общими).
    void configure(const Experiment& exp, double low, double high, double peak);
    void refresh(const Experiment& exp, bool fast);

    TimePlot* time_plot;
    HistPlot* hist_plot;

signals:
    void quantity_changed();
    void close_clicked();

private:
    void configure_hist();

    QComboBox* selector_;
    QLabel* value_;
    QLabel* stats_;
    QBoxLayout* body_;
    long long last_count_ = 0;

    // Последние параметры распределения: нужны, чтобы перенастроить его после поворота
    QString axis_;
    std::vector<double> xs_, pdf_;
    double peak_ = 1;
    theory::Kind kind_ = theory::Kind::Modulus;
};

// Среднее и дисперсия: опыт и теория (HTML, две строки).
QString stats_text(const Experiment& exp, Quantity q);
