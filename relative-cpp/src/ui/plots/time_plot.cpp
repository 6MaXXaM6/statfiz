// Рисование истории величины: ломаная или столбцы пикселей min…max (как в осциллографе).

#include "ui/plots/time_plot.h"

#include <algorithm>
#include <cmath>

#include "settings.h"
#include "ui/style.h"

static const char* RANGE = settings::COLOR_RANGE;    // полоса min…max — светлая
static const char* SPREAD = settings::COLOR_SPREAD;  // полоса среднее ± σ — потемнее

TimePlot::TimePlot(QWidget* parent) : PlotBase(parent)
{
    set_axis_label(Axis::Bottom, QString::fromUtf8("время t, пс"));
}

void TimePlot::configure(const QString& axis_label, double low, double high)
{
    set_axis_label(Axis::Left, axis_label);
    set_y_range(low, high);
}

void TimePlot::update_view(const TimeSeries& series, std::optional<double> theory_mean)
{
    series_ = &series;
    theory_mean_ = theory_mean;
    // Ось времени от начала набора статистики: график не бежит, а "схлопывается".
    const auto& b = series.buckets();
    if (!b.empty())
        set_x_range(b.front().t0, std::max(b.back().t1, b.front().t0 + 1e-3));
    update();
}

void TimePlot::draw_data(QPainter& p)
{
    if (!series_ || series_->buckets().empty())
        return;
    QRectF r = data_rect();
    // Отсчётов меньше, чем пикселей по ширине, — ломаная; иначе — столбцы min…max.
    bool sparse = series_->span() == 1 && static_cast<double>(series_->buckets().size()) < r.width();
    if (sparse)
        draw_line(p);
    else
        draw_columns(p);

    // Теоретическое среднее — поверх кривой
    if (theory_mean_) {
        p.setPen(make_pen(style::THEORY, 0.1, Qt::DotLine));
        p.drawLine(QPointF(r.left(), map_y(*theory_mean_)), QPointF(r.right(), map_y(*theory_mean_)));
    }

    // Текущее значение: пунктир через весь график и точка на конце кривой
    auto [t, v] = *series_->last();
    p.setPen(make_pen(style::HILITE, settings::CURRENT_LINE, Qt::DashLine));
    p.drawLine(QPointF(r.left(), map_y(v)), QPointF(r.right(), map_y(v)));
    p.setPen(QPen(Qt::black, 1.5));
    p.setBrush(QColor(style::HILITE));
    double d = style::px(0.35);
    p.drawEllipse(map(t, v), d, d);
}

// В каждой корзине по одному отсчёту — просто соединяем их.
void TimePlot::draw_line(QPainter& p)
{
    QPolygonF line;
    for (const TimeSeries::Bucket& b : series_->buckets())
        line << map(b.t0, b.last);
    p.setPen(make_pen(style::REL, settings::CURVE_LINE));
    p.drawPolyline(line);
}

// Корзины раскладываются по столбцам (по пикселю). В каждом столбце три слоя:
//   светлая полоса — от минимума до максимума (весь размах значений),
//   полоса потемнее — среднее ± σ (типичный разброс),
//   тёмная линия — среднее за столбец (видно, как оно колеблется около теории).
// Размах захватывает и последнее значение предыдущего столбца, чтобы соседние
// столбцы соединялись, как у настоящей ломаной.
void TimePlot::draw_columns(QPainter& p)
{
    struct Column {
        double lo = INFINITY, hi = -INFINITY, last = NAN;
        double n = 0, sum = 0, sum_sq = 0;
    };
    QRectF r = data_rect();
    // Столбцов — по пикселю, но не больше, чем корзин (иначе между столбцами были бы дырки)
    int count = std::clamp(static_cast<int>(series_->buckets().size()), 1, std::max(1, static_cast<int>(r.width())));
    double width = r.width() / count;
    std::vector<Column> columns(count);
    for (const TimeSeries::Bucket& b : series_->buckets()) {
        double x = (map_x(0.5 * (b.t0 + b.t1)) - r.left()) / width;
        Column& c = columns[std::clamp(static_cast<int>(x), 0, count - 1)];
        c.lo = std::min(c.lo, b.min);
        c.hi = std::max(c.hi, b.max);
        c.last = b.last;
        c.n += b.n;
        c.sum += b.sum;
        c.sum_sq += b.sum_sq;
    }

    QVector<QRectF> range, spread, mean;  // полосы min…max, среднее ± σ и линия среднего
    double thick = std::max(2, style::px(0.08));  // толщина линии среднего, пикселей
    double prev = NAN, prev_mean = NAN;
    for (int k = 0; k < count; ++k) {
        const Column& c = columns[k];
        if (c.n == 0)
            continue;  // в этот столбец ничего не попало
        double lo = std::isnan(prev) ? c.lo : std::min(c.lo, prev);
        double hi = std::isnan(prev) ? c.hi : std::max(c.hi, prev);
        double m = c.sum / c.n;
        double sigma = std::sqrt(std::max(c.sum_sq / c.n - m * m, 0.0));
        double x = r.left() + k * width, w = std::max(width, 1.0);
        range << QRectF(x, map_y(hi), w, std::max(map_y(lo) - map_y(hi), 1.0));
        spread << QRectF(x, map_y(m + sigma), w, map_y(m - sigma) - map_y(m + sigma));
        // Линия среднего — ступенькой: отрезок по столбцу и вертикальная связка с предыдущим
        double y = map_y(m);
        mean << QRectF(x, y - thick / 2, w, thick);
        if (!std::isnan(prev_mean))
            mean << QRectF(x, std::min(y, prev_mean) - thick / 2, thick, std::fabs(y - prev_mean) + thick);
        prev_mean = y;
        prev = c.last;
    }
    p.save();
    // Всё — прямоугольники по пикселям: сглаживание не нужно, а без него рисуется в разы быстрее
    p.setRenderHint(QPainter::Antialiasing, false);
    p.setPen(Qt::NoPen);
    p.setBrush(QColor(RANGE));
    p.drawRects(range);
    p.setBrush(QColor(SPREAD));
    p.drawRects(spread);
    p.setBrush(QColor(style::REL));
    p.drawRects(mean);
    p.restore();
}
