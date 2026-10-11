// Рисование сосуда: молекулы кружками (радиус — из массы), выбранные — цветом и стрелками.

#include "ui/plots/box_view.h"

#include <QMouseEvent>

#include "settings.h"
#include "ui/style.h"

constexpr double ARROW_HEAD = 3.0;     // наконечник стрелки, нм

BoxView::BoxView(QWidget* parent) : CanvasBase(parent)
{
    setToolTip(QString::fromUtf8("Щелчок по молекуле: левая кнопка — молекула 1, правая — молекула 2"));
}

void BoxView::configure(double box_size, double speed_scale)
{
    box_ = box_size;
    speed_scale_ = speed_scale;
    set_world(0, box_size, 0, box_size);
}

void BoxView::update_view(const Experiment& exp, bool show_second)
{
    exp_ = &exp;
    show_second_ = show_second;
    update();
}

void BoxView::draw_world(QPainter& p)
{
    // Стенки сосуда
    p.setPen(QPen(Qt::black, 3));
    p.setBrush(Qt::NoBrush);
    p.drawRect(QRectF(map(0, box_), map(box_, 0)));
    if (!exp_)
        return;

    const physics::Gas& gas = *exp_->gas;
    double k = scale();  // пикселей на нм

    // Все молекулы: сорт A — серо-синие, сорт B — зелёные
    p.setPen(Qt::NoPen);
    for (int n = 0; n < gas.n(); ++n) {
        p.setBrush(QColor(gas.species[n] == 0 ? style::GAS_A : style::GAS_B));
        double r = gas.radius[n] * k;
        p.drawEllipse(map(gas.pos[n].x, gas.pos[n].y), r, r);
    }

    // Выбранные молекулы: чуть крупнее, с белой каймой, и стрелки их скоростей
    std::vector<std::pair<int, const char*>> chosen = {{exp_->i, style::MOL1}};
    if (show_second_)
        chosen.push_back({exp_->j, style::MOL2});
    double arrow_scale = settings::ARROW_LENGTH / speed_scale_;  // нм на (м/с)
    for (auto [n, color] : chosen) {
        Vec2 pos = gas.pos[n];
        double r = (gas.radius[n] + 0.3) * k;
        p.setPen(QPen(Qt::white, 2));
        p.setBrush(QColor(color));
        p.drawEllipse(map(pos.x, pos.y), r, r);
        Vec2 tip = pos + gas.vel[n] * arrow_scale;
        draw_arrow(p, map(pos.x, pos.y), map(tip.x, tip.y), ARROW_HEAD * k, QColor(color));
    }
}

void BoxView::mousePressEvent(QMouseEvent* event)
{
    QPointF w = unmap(event->pos());
    emit clicked(w.x(), w.y(), event->button() == Qt::RightButton ? 2 : 1);
}
