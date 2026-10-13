// Оси, деления и подписи графиков; холст с одинаковым масштабом по осям.

#include "ui/plots/plot_base.h"

#include <QAbstractTextDocumentLayout>
#include <QTextDocument>
#include <algorithm>
#include <cmath>

#include "settings.h"
#include "ui/style.h"

QPen make_pen(const QColor& color, double width, Qt::PenStyle line)
{
    QPen pen(color, style::px(width), line, Qt::FlatCap, Qt::RoundJoin);
    return pen;
}

void draw_arrow(QPainter& p, QPointF from, QPointF to, double head, const QColor& color, double width)
{
    QPointF d = to - from;
    double length = std::hypot(d.x(), d.y());
    if (length < 1e-9)
        return;
    QPointF u = d / length;              // направление стрелки
    QPointF n(-u.y(), u.x());            // перпендикуляр к ней
    head = std::min(head, 0.6 * length);
    QPointF base = to - u * head;        // основание наконечника
    double half = 0.45 * head;
    p.setPen(QPen(color, style::px(width), Qt::SolidLine, Qt::RoundCap, Qt::MiterJoin));
    p.drawLine(from, base);
    p.setPen(Qt::NoPen);
    p.setBrush(color);
    p.drawPolygon(QPolygonF({to, base + n * half, base - n * half}));
}

// ----------------------------------------------------------------------
// Деления на оси
// ----------------------------------------------------------------------

// "Круглый" шаг делений (1, 2 или 5 · 10ⁿ), чтобы на оси было не больше max_count делений.
static double nice_step(double span, int max_count)
{
    double raw = span / std::max(1, max_count);
    double power = std::pow(10.0, std::floor(std::log10(raw)));
    for (double k : {1.0, 2.0, 5.0, 10.0})
        if (k * power >= raw)
            return k * power;
    return 10 * power;
}

static std::vector<double> ticks(double low, double high, int max_count, double& step)
{
    std::vector<double> result;
    if (!(high > low))
        return result;
    step = nice_step(high - low, max_count);
    for (double t = std::ceil(low / step) * step; t <= high + step * 1e-9; t += step)
        result.push_back(std::fabs(t) < step * 1e-9 ? 0.0 : t);
    return result;
}

// Сколько знаков после запятой нужно, чтобы различать деления с шагом step.
static int digits_for(double step)
{
    return std::max(0, static_cast<int>(std::ceil(-std::log10(step) - 1e-9)));
}

// ----------------------------------------------------------------------
// PlotBase
// ----------------------------------------------------------------------

PlotBase::PlotBase(QWidget* parent) : QWidget(parent)
{
    setMinimumSize(style::px(6), style::px(5));
}

void PlotBase::set_x_range(double low, double high)
{
    x_low_ = low;
    x_high_ = high > low ? high : low + 1e-9;
    update();
}

void PlotBase::set_y_range(double low, double high)
{
    y_low_ = low;
    y_high_ = high > low ? high : low + 1e-9;
    update();
}

void PlotBase::set_axis_label(Axis axis, const QString& html)
{
    (axis == Axis::Left ? left_label_ : bottom_label_) = html;
    update();
}

void PlotBase::show_left_axis(bool show)
{
    left_axis_ = show;
    update();
}

// Размеры осей постоянные: иначе область графика "ездила" бы, когда меняются числа на осях.
QRectF PlotBase::data_rect() const
{
    double left = left_axis_ ? style::px(AXIS_WIDTH) : style::px(0.9);  // без оси — место для числа "0" под ней
    double bottom = style::px(AXIS_HEIGHT);
    double top = style::px(0.6), right = style::px(0.6);
    return QRectF(left, top, width() - left - right, height() - top - bottom);
}

double PlotBase::map_x(double x) const
{
    QRectF r = data_rect();
    return r.left() + (x - x_low_) / (x_high_ - x_low_) * r.width();
}

double PlotBase::map_y(double y) const
{
    QRectF r = data_rect();
    return r.bottom() - (y - y_low_) / (y_high_ - y_low_) * r.height();
}

void PlotBase::paintEvent(QPaintEvent*)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);
    p.fillRect(rect(), Qt::white);
    p.save();
    p.setClipRect(data_rect());
    draw_data(p);
    p.restore();
    draw_axes(p);
}

void PlotBase::draw_axes(QPainter& p)
{
    QRectF r = data_rect();
    int tick = style::px(0.4);
    p.setPen(QPen(Qt::black, 2));
    p.setFont(style::font(settings::AXIS_NUMBERS_FONT));
    QFontMetrics fm(p.font());

    // Нижняя ось: деления и числа под ними
    p.drawLine(r.bottomLeft(), r.bottomRight());
    double step = 1;
    int max_x = std::max(2, static_cast<int>(r.width() / style::px(4.5)));
    for (double t : ticks(x_low_, x_high_, max_x, step)) {
        double x = map_x(t);
        p.drawLine(QPointF(x, r.bottom()), QPointF(x, r.bottom() + tick));
        QString text = style::fmt(t, digits_for(step));
        p.drawText(QRectF(x - 100, r.bottom() + tick, 200, fm.height()), Qt::AlignHCenter | Qt::AlignTop, text);
    }
    draw_label(p, bottom_label_, QPointF(r.center().x(), r.bottom() + tick + fm.height() * 1.6), false);

    // Левая ось: деления и числа слева от них
    if (!left_axis_)
        return;
    p.setPen(QPen(Qt::black, 2));
    p.setFont(style::font(settings::AXIS_NUMBERS_FONT));
    p.drawLine(r.topLeft(), r.bottomLeft());
    int max_y = std::max(2, static_cast<int>(r.height() / style::px(2.2)));
    for (double t : ticks(y_low_, y_high_, max_y, step)) {
        double y = map_y(t);
        p.drawLine(QPointF(r.left() - tick, y), QPointF(r.left(), y));
        QString text = style::fmt(t, digits_for(step));
        p.drawText(QRectF(0, y - fm.height() / 2.0, r.left() - tick - 2, fm.height()),
                   Qt::AlignRight | Qt::AlignVCenter, text);
    }
    draw_label(p, left_label_, QPointF(style::px(0.7), r.center().y()), true);
}

// Подпись оси (HTML) с центром в точке center; vertical — повернуть на 90° (для левой оси).
void PlotBase::draw_label(QPainter& p, const QString& html, QPointF center, bool vertical)
{
    if (html.isEmpty())
        return;
    QTextDocument doc;
    doc.setDefaultFont(style::font(settings::AXIS_LABEL_FONT));
    doc.setDocumentMargin(0);
    doc.setHtml(html);
    QSizeF size = doc.size();
    p.save();
    p.translate(center);
    if (vertical)
        p.rotate(-90);
    p.translate(-size.width() / 2, -size.height() / 2);
    doc.drawContents(&p);
    p.restore();
}

// ----------------------------------------------------------------------
// CanvasBase
// ----------------------------------------------------------------------

CanvasBase::CanvasBase(QWidget* parent) : QWidget(parent) {}

void CanvasBase::set_world(double low_x, double high_x, double low_y, double high_y, double margin)
{
    double mx = (high_x - low_x) * margin, my = (high_y - low_y) * margin;
    low_x_ = low_x - mx;
    high_x_ = high_x + mx;
    low_y_ = low_y - my;
    high_y_ = high_y + my;
    update();
}

double CanvasBase::scale() const
{
    return std::min(width() / (high_x_ - low_x_), height() / (high_y_ - low_y_));
}

// Мир вписан в виджет с сохранением пропорций и стоит по центру.
QPointF CanvasBase::map(double x, double y) const
{
    double k = scale();
    double ox = (width() - k * (high_x_ - low_x_)) / 2;
    double oy = (height() - k * (high_y_ - low_y_)) / 2;
    return {ox + (x - low_x_) * k, height() - oy - (y - low_y_) * k};
}

QPointF CanvasBase::unmap(QPointF s) const
{
    double k = scale();
    double ox = (width() - k * (high_x_ - low_x_)) / 2;
    double oy = (height() - k * (high_y_ - low_y_)) / 2;
    return {low_x_ + (s.x() - ox) / k, low_y_ + (height() - oy - s.y()) / k};
}

void CanvasBase::paintEvent(QPaintEvent*)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);
    p.fillRect(rect(), Qt::white);
    draw_world(p);
}
