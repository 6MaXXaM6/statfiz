// Гистограмма: столбики, теоретическая кривая, подсветка нового отсчёта, поворот.

#include "ui/plots/hist_plot.h"

#include <algorithm>
#include <cmath>

#include "settings.h"
#include "ui/style.h"
#include "ui/widgets.h"

constexpr double FLASH_MIN = 0.03;    // более слабая подсветка не рисуется

// Показатель степени для оси плотности: 0.0012 с/м -> -3 (ось в единицах 10⁻³ с/м).
static int density_exponent(double peak)
{
    if (!(peak > 0) || !std::isfinite(peak))
        return 0;
    return static_cast<int>(std::floor(std::log10(peak)));
}

HistPlot::HistPlot(bool sideways, QWidget* parent) : PlotBase(parent)
{
    rotate_button = overlay_button(this, QString::fromUtf8("↻"), QString::fromUtf8("Повернуть распределение"),
                                   [this] { emit rotate_clicked(); });
    sideways_ = !sideways;  // чтобы set_orientation точно всё настроил
    set_orientation(sideways);
}

void HistPlot::resizeEvent(QResizeEvent* event)
{
    PlotBase::resizeEvent(event);
    place_overlay(rotate_button, this);
}

void HistPlot::set_orientation(bool sideways)
{
    if (sideways == sideways_)
        return;
    sideways_ = sideways;
    show_left_axis(!sideways);  // боком: ось значений — общая с соседним графиком
    apply_axes();
}

void HistPlot::configure(const QString& value_label, const std::vector<double>& xs, const std::vector<double>& pdf,
                         double peak, const QString& density_unit, bool rescale)
{
    value_label_ = value_label;
    density_unit_ = density_unit;
    low_ = xs.front();
    high_ = xs.back();
    exponent_ = rescale ? density_exponent(peak) : 0;
    double factor = std::pow(10.0, -exponent_);
    top_ = settings::HIST_HEADROOM * peak * factor;
    xs_ = xs;
    pdf_ = pdf;
    for (double& f : pdf_)
        f *= factor;
    flash_.clear();
    apply_axes();
}

void HistPlot::apply_axes()
{
    QString power = exponent_ ? "10" + style::sup(exponent_) + " " : "";
    QString density = "f, " + power + density_unit_;  // f — плотность вероятности
    set_axis_label(Axis::Bottom, sideways_ ? density : value_label_);
    set_axis_label(Axis::Left, sideways_ ? "" : density);
    if (sideways_) {
        set_x_range(0, top_);
        set_y_range(low_, high_);
    } else {
        set_x_range(low_, high_);
        set_y_range(0, top_);
    }
}

// Точка графика по (значение величины, плотность) с учётом ориентации.
QPointF HistPlot::point(double value, double density) const
{
    return sideways_ ? map(density, value) : map(value, density);
}

// Столбик от значения from до to высотой height.
QRectF HistPlot::bar(double from, double to, double height) const
{
    return QRectF(point(from, 0), point(to, height)).normalized();
}

void HistPlot::update_view(const Histogram& hist, std::optional<double> current, bool highlight)
{
    double factor = std::pow(10.0, -exponent_);
    std::vector<double> dens = hist.density();
    shown_.resize(dens.size());
    for (size_t k = 0; k < dens.size(); ++k)
        shown_[k] = dens[k] * factor;
    hist_low_ = hist.low();
    hist_width_ = hist.width();
    current_ = current;

    // Столбик, который только что подрос, вспыхивает оранжевым и плавно гаснет.
    if (flash_.size() != shown_.size())
        flash_.assign(shown_.size(), 0.0);
    for (double& f : flash_)
        f *= settings::FLASH_DECAY;
    if (highlight && current)
        if (auto k = hist.bin_of(*current))
            flash_[*k] = 1.0;
    update();
}

void HistPlot::draw_data(QPainter& p)
{
    // Столбики (выше края — обрезаются, на краю — треугольник)
    for (size_t k = 0; k < shown_.size(); ++k) {
        double from = hist_low_ + k * hist_width_, to = from + hist_width_;
        QRectF r = bar(from, to, std::min(shown_[k], top_));
        p.setPen(QPen(QColor(style::BAR_EDGE), 1));
        p.setBrush(QColor(style::BAR));
        p.drawRect(r);
        if (flash_[k] > FLASH_MIN) {
            QColor c(style::HILITE);
            c.setAlphaF(flash_[k]);
            p.setPen(Qt::NoPen);
            p.setBrush(c);
            p.drawRect(r);
        }
        if (shown_[k] > top_) {
            double mid = (from + to) / 2, s = style::px(0.4);
            QPointF tip = point(mid, top_);
            QPointF dir = sideways_ ? QPointF(1, 0) : QPointF(0, -1);  // куда растёт столбик
            QPointF side(-dir.y(), dir.x());
            p.setPen(Qt::NoPen);
            p.setBrush(QColor("#1a2a4a"));
            p.drawPolygon(QPolygonF({tip, tip - dir * 1.6 * s + side * s, tip - dir * 1.6 * s - side * s}));
        }
    }

    // Теоретическая кривая
    QPolygonF curve;
    for (size_t k = 0; k < xs_.size(); ++k)
        curve << point(xs_[k], pdf_[k]);
    p.setPen(make_pen(style::THEORY, settings::THEORY_LINE));
    p.setBrush(Qt::NoBrush);
    p.drawPolyline(curve);

    // Текущее значение — пунктир поперёк оси значений
    if (current_) {
        p.setPen(make_pen(style::HILITE, settings::CURRENT_LINE, Qt::DashLine));
        p.drawLine(point(*current_, 0), point(*current_, top_));
    }
}
