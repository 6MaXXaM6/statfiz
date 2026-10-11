// Рисование кривых, меток и легенды (см. curve_plot.h).

#include "ui/plots/curve_plot.h"

#include <QTextDocument>

#include "ui/style.h"

CurvePlot::CurvePlot(QWidget* parent) : PlotBase(parent) {}

void CurvePlot::set_curves(std::vector<Curve> curves)
{
    curves_ = std::move(curves);
    update();
}

void CurvePlot::set_markers(std::vector<Marker> markers)
{
    markers_ = std::move(markers);
    update();
}

// Небольшой кусок HTML (обозначения с индексами) в точке top_left.
void CurvePlot::draw_html(QPainter& p, const QString& html, QPointF top_left, const QColor& color)
{
    QTextDocument doc;
    doc.setDefaultFont(style::font(0.8));
    doc.setDocumentMargin(0);
    doc.setDefaultStyleSheet(QString("body { color: %1; }").arg(color.name()));
    doc.setHtml("<body>" + html + "</body>");
    p.save();
    p.translate(top_left);
    doc.drawContents(&p);
    p.restore();
}

void CurvePlot::draw_data(QPainter& p)
{
    QRectF r = data_rect();

    // Метки: вертикальный пунктир и подпись наверху (подписи разносятся по высоте, чтобы не налезали)
    int row = 0;
    for (const Marker& m : markers_) {
        double x = map_x(m.x);
        p.setPen(make_pen(m.color, 0.08, Qt::DashLine));
        p.drawLine(QPointF(x, r.top()), QPointF(x, r.bottom()));
        draw_html(p, m.label, QPointF(x + style::px(0.2), r.top() + style::px(0.2) + row * style::px(1.1)), m.color);
        row = (row + 1) % 3;
    }

    // Кривые
    for (const Curve& c : curves_) {
        QPolygonF line;
        for (size_t k = 0; k < c.xs.size(); ++k)
            line << map(c.xs[k], c.ys[k]);
        p.setPen(make_pen(c.color, c.dashed ? 0.1 : 0.16, c.dashed ? Qt::DashLine : Qt::SolidLine));
        p.setBrush(Qt::NoBrush);
        p.drawPolyline(line);
    }

    // Легенда в правом верхнем углу: отрезок линии и подпись
    double y = r.top() + style::px(0.3);
    for (const Curve& c : curves_) {
        if (c.label.isEmpty())
            continue;
        double x = r.right() - style::px(7.5);
        p.setPen(make_pen(c.color, c.dashed ? 0.1 : 0.16, c.dashed ? Qt::DashLine : Qt::SolidLine));
        p.drawLine(QPointF(x, y + style::px(0.5)), QPointF(x + style::px(1.5), y + style::px(0.5)));
        draw_html(p, c.label, QPointF(x + style::px(1.9), y), Qt::black);
        y += style::px(1.2);
    }
}
