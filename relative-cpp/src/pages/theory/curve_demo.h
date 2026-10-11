// Живой график к разделу теории: движки T и масс, теоретические кривые,
// характерные значения. Серым пунктиром — кривая при начальных параметрах,
// чтобы изменение было видно на глаз.

#pragma once

#include <QLabel>
#include <QWidget>

#include "ui/plots/curve_plot.h"
#include "ui/widgets.h"

class CurveDemo : public QWidget {
public:
    enum class Variant {
        Projection,  // f(vₓ) — Гаусс
        Modulus,     // f(|v|) — Рэлей
        Relative,    // |v₁|, |v₂| и |v_отн| (одинаковые молекулы)
        Mixture,     // то же для смеси: сначала m₂ ≠ m₁
        Energy,      // f(E) — экспонента, от массы не зависит
    };

    explicit CurveDemo(Variant variant);

    ParamControl* temperature;
    ParamControl* mass_1;
    ParamControl* mass_2;   // только для Relative и Mixture

private:
    void reset();
    void fit_axis();          // ось x — под текущие кривые
    void update_view();
    double scale_range() const;  // правый край оси для текущих параметров

    Variant variant_;
    CurvePlot* plot_;
    QLabel* readout_;
    double x_high_ = 1;
    int start_m2_ = 28;
};
