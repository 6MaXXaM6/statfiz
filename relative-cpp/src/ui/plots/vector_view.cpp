// Рисование векторов скоростей v1, v2, v_отн и проекции.

#include "ui/plots/vector_view.h"

#include "settings.h"
#include "ui/style.h"

constexpr double HEAD = 0.12;  // наконечник стрелки в долях радиуса диаграммы

VectorView::VectorView(QWidget* parent) : CanvasBase(parent)
{
    set_sizes(settings::VECTOR_SIZE, settings::VECTOR_MIN_SIZE);
}

void VectorView::set_sizes(double preferred, double minimum)
{
    preferred_ = QSize(style::px(preferred), style::px(preferred));
    minimum_ = QSize(style::px(minimum), style::px(minimum));
    setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Maximum);
    setMinimumSize(minimum_);
    setMaximumSize(preferred_);
    updateGeometry();
}

void VectorView::set_radius(double r)
{
    radius_ = r;
    set_world(-r, r, -r, r, 0.02);
}

void VectorView::update_view(const Experiment& exp, std::optional<Obj> projection_of)
{
    v1_ = exp.gas->vel[exp.i];
    v2_ = exp.gas->vel[exp.j];
    projection_.reset();
    if (projection_of)
        projection_ = exp.velocity(*projection_of).x;
    update();
}

void VectorView::draw_world(QPainter& p)
{
    double r = radius_ * 1.02;
    // Рамка и оси координат
    p.setPen(QPen(QColor("#999999"), 1));
    p.setBrush(Qt::NoBrush);
    p.drawRect(QRectF(map(-r, r), map(r, -r)));
    p.setPen(make_pen("#bbbbbb", 0.05));
    p.drawLine(map(-r, 0), map(r, 0));
    p.drawLine(map(0, -r), map(0, r));
    p.setPen(QColor("#888888"));
    p.setFont(style::font(0.8));
    QPointF x_end = map(radius_, 0);
    p.drawText(QRectF(x_end.x() - style::px(1), x_end.y(), style::px(1), style::px(1.2)), Qt::AlignRight, "x");

    double head = HEAD * radius_ * scale();
    auto to_screen = [this](Vec2 v) { return map(v.x, v.y); };
    QPointF origin = map(0, 0);
    draw_arrow(p, origin, to_screen(v1_), head, QColor(style::MOL1));
    draw_arrow(p, origin, to_screen(v2_), head, QColor(style::MOL2));
    draw_arrow(p, to_screen(v2_), to_screen(v1_), head, QColor(style::REL), 0.28);
    if (projection_)
        draw_arrow(p, origin, map(*projection_, 0), head, QColor(style::PROJ), 0.35);
}
