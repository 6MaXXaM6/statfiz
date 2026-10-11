// Рисунок упругого удара (см. collision_sketch.h).

#include "pages/theory/collision_sketch.h"

#include <QPainter>
#include <QTextDocument>

#include "model/vec2.h"
#include "ui/plots/plot_base.h"
#include "ui/style.h"

CollisionSketch::CollisionSketch()
{
    setMinimumSize(style::px(14), style::px(12));
}

static void caption(QPainter& p, const QString& html, QPointF at, const char* color)
{
    QTextDocument doc;
    doc.setDefaultFont(style::font(0.95, true));
    doc.setDocumentMargin(0);
    doc.setDefaultStyleSheet(QString("body { color: %1; }").arg(color));
    doc.setHtml("<body>" + html + "</body>");
    p.save();
    p.translate(at);
    doc.drawContents(&p);
    p.restore();
}

void CollisionSketch::paintEvent(QPaintEvent*)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);
    p.fillRect(rect(), Qt::white);

    // Диски в момент касания (единицы — доли меньшей стороны виджета), массы m₁ = 1, m₂ = 2
    double u = std::min(width(), height()) / 11.0;
    QPointF c(width() / 2.0, height() / 2.0);
    Vec2 p1(-1.1, 0.35), p2(1.3, -0.45);
    double r1 = 1.1, r2 = 1.4, m1 = 1, m2 = 2;
    Vec2 v1(2.2, -0.6), v2(-1.4, 0.9);  // скорости до удара (сближаются)
    auto at = [&](Vec2 w) { return c + QPointF(w.x * u, -w.y * u); };

    // Удар меняет скорости только вдоль линии центров n (как в Gas::collide)
    Vec2 d = p2 - p1;
    Vec2 n = d * (1.0 / d.length());
    double vn = (v2 - v1).dot(n);
    Vec2 v1_after = v1 + n * (2 * m2 / (m1 + m2) * vn);
    Vec2 v2_after = v2 - n * (2 * m1 / (m1 + m2) * vn);

    p.setPen(QPen(QColor("#888888"), 1, Qt::DashLine));  // линия центров
    p.drawLine(at(p1 - n * 2.5), at(p2 + n * 2.5));
    // Диски полупрозрачные, чтобы стрелки скоростей были видны и поверх них
    QColor c1(style::MOL1), c2(style::MOL2);
    c1.setAlphaF(0.35);
    c2.setAlphaF(0.35);
    p.setPen(QPen(QColor(style::MOL1), 2));
    p.setBrush(c1);
    p.drawEllipse(at(p1), r1 * u, r1 * u);
    p.setPen(QPen(QColor(style::MOL2), 2));
    p.setBrush(c2);
    p.drawEllipse(at(p2), r2 * u, r2 * u);

    // Скорость до удара "приходит" в центр диска, скорость после удара из него "уходит"
    double head = u * 0.45;
    draw_arrow(p, at(p1 - v1), at(p1), head, Qt::black);
    draw_arrow(p, at(p2 - v2), at(p2), head, Qt::black);
    draw_arrow(p, at(p1), at(p1 + v1_after), head, QColor(style::HILITE));
    draw_arrow(p, at(p2), at(p2 + v2_after), head, QColor(style::HILITE));
    draw_arrow(p, at(p1 + d * (r1 / d.length())), at(p1 + d * (r1 / d.length()) + n * 1.2), head * 0.8, QColor(style::PROJ), 0.15);

    caption(p, QString::fromUtf8("n"), at(p1 + n * (r1 + 1.2)) + QPointF(0, -u * 0.8), style::PROJ);
    caption(p, QString::fromUtf8("v<sub>1</sub>"), at(p1 - v1) + QPointF(-u * 0.9, -u * 0.3), "#000000");
    caption(p, QString::fromUtf8("v<sub>2</sub>"), at(p2 - v2) + QPointF(4, -u * 0.2), "#000000");
    caption(p, QString::fromUtf8("v′<sub>1</sub>"), at(p1 + v1_after) + QPointF(-u * 0.9, -u * 0.6), style::HILITE);
    caption(p, QString::fromUtf8("v′<sub>2</sub>"), at(p2 + v2_after) + QPointF(4, -u * 0.2), style::HILITE);
    caption(p, QString::fromUtf8("чёрные — до удара, оранжевые — после"), QPointF(u * 0.3, height() - u * 0.8), "#555555");
}
