// Сосуд с молекулами.

#pragma once

#include "model/experiment.h"
#include "ui/plots/plot_base.h"

// Молекулы газов A и B; выбранные молекулы выделены цветом и стрелками скоростей.
// Щелчок левой кнопкой мыши — сигнал clicked(x, y, 1), правой — clicked(x, y, 2).
class BoxView : public CanvasBase {
    Q_OBJECT
public:
    explicit BoxView(QWidget* parent = nullptr);

    // speed_scale — характерная скорость (м/с), которой соответствует стрелка settings::ARROW_LENGTH нм.
    void configure(double box_size, double speed_scale);
    // show_second — выделять ли и молекулу 2 (для относительной скорости)
    void update_view(const Experiment& exp, bool show_second);

signals:
    void clicked(double x, double y, int which);

protected:
    void draw_world(QPainter& p) override;
    void mousePressEvent(QMouseEvent* event) override;

private:
    const Experiment* exp_ = nullptr;
    bool show_second_ = true;
    double box_ = 100;
    double speed_scale_ = 1;
};
