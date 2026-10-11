// Векторная диаграмма скоростей.

#pragma once

#include <optional>

#include "model/experiment.h"
#include "ui/plots/plot_base.h"

// v1, v2 из общего начала и v_отн = v1 − v2 (из конца v2 в конец v1); проекция — вектор на оси x.
class VectorView : public CanvasBase {
public:
    explicit VectorView(QWidget* parent = nullptr);

    // Желаемая и наименьшая сторона (в базовых шрифтах). Если места мало, компоновка
    // сама уменьшит диаграмму до minimum; рисунок остаётся квадратным.
    void set_sizes(double preferred, double minimum);
    void set_radius(double r);
    // projection_of — чью проекцию на ось x показать (пары или молекулы 1) или пусто.
    void update_view(const Experiment& exp, std::optional<Obj> projection_of);

    QSize sizeHint() const override { return preferred_; }
    QSize minimumSizeHint() const override { return minimum_; }

protected:
    void draw_world(QPainter& p) override;

private:
    QSize preferred_, minimum_;
    double radius_ = 1;
    Vec2 v1_, v2_;
    std::optional<double> projection_;
};
