// Панель графика (см. graph_panel.h).

#include "pages/demo/graph_panel.h"

#include <algorithm>

#include "ui/labels.h"
#include "settings.h"
#include "ui/style.h"
#include "ui/widgets.h"

using theory::Kind;

constexpr int CURVE_POINTS = 300;        // точек на теоретической кривой

const std::vector<Quantity> QUANTITIES = {
    {Obj::Pair, Kind::Modulus},   {Obj::Pair, Kind::Projection},
    {Obj::Single, Kind::Modulus}, {Obj::Single, Kind::Projection},
    {Obj::Second, Kind::Modulus}, {Obj::Second, Kind::Projection},
    {Obj::Single, Kind::Energy},  {Obj::Second, Kind::Energy},
};

static int index_of(Quantity q)
{
    return static_cast<int>(std::find(QUANTITIES.begin(), QUANTITIES.end(), q) - QUANTITIES.begin());
}

GraphPanel::GraphPanel(Quantity quantity, bool closable)
{
    selector_ = new QComboBox;
    selector_->setFont(style::font(1.1, true));
    for (Quantity q : QUANTITIES)
        selector_->addItem(labels::quantity_plain(q.obj, q.kind));
    selector_->setCurrentIndex(index_of(quantity));
    connect(selector_, QOverload<int>::of(&QComboBox::currentIndexChanged), this, &GraphPanel::quantity_changed);
    value_ = label("", 1.2);
    value_->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Fixed);
    auto* header = hbox({selector_, {value_, 1}}, style::px(0.4));
    if (closable)
        header->addWidget(button(QString::fromUtf8("✕"), [this] { emit close_clicked(); }));

    time_plot = new TimePlot;
    hist_plot = new HistPlot(true);
    connect(hist_plot, &HistPlot::rotate_clicked, this, &GraphPanel::rotate);
    stats_ = label("", 0.85);
    stats_->setWordWrap(true);

    // Графики и подписи (среднее, дисперсия): подписи под графиками или, когда графики
    // на весь экран, справа от них — чтобы графики не становились слишком длинными.
    body_ = new QBoxLayout(QBoxLayout::TopToBottom);
    body_->setSpacing(style::px(0.15));
    body_->addLayout(hbox({{time_plot, 3}, {hist_plot, 2}}, 0), 1);
    body_->addWidget(stats_);
    set_side_stats(false);
    setLayout(vbox({header, {body_, 1}}, style::px(0.15)));
}

Quantity GraphPanel::quantity() const
{
    return QUANTITIES[selector_->currentIndex()];
}

void GraphPanel::show_quantity(Quantity q)
{
    selector_->setCurrentIndex(index_of(q));
}

void GraphPanel::set_side_stats(bool side)
{
    if (side) {
        body_->setDirection(QBoxLayout::LeftToRight);
        // Сбоку ширина постоянная, и компоновка обязана её выделить.
        stats_->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Preferred);
        stats_->setFixedWidth(style::px(settings::SIDE_STATS_WIDTH));
        stats_->setMinimumHeight(0);
        stats_->setMaximumHeight(QWIDGETSIZE_MAX);
        stats_->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
        stats_->setFont(style::font(1.0));
    } else {
        body_->setDirection(QBoxLayout::TopToBottom);
        // Под графиками подпись может сжиматься (Ignored) — окно не станет шире экрана.
        stats_->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Preferred);
        stats_->setMinimumWidth(0);
        stats_->setMaximumWidth(QWIDGETSIZE_MAX);
        stats_->setFont(style::font(0.85));
        // Высота постоянная: иначе от цифр (минус, степени) она меняется на пиксель,
        // и графики над ними дрожат.
        stats_->setFixedHeight(2 * stats_->fontMetrics().lineSpacing() + style::px(0.4));
        stats_->setAlignment(Qt::AlignLeft | Qt::AlignTop);
    }
}

// Распределение боком (рядом с графиком во времени) ↔ обычный вид (только распределение).
// История никуда не девается — она копится и дальше и снова видна после поворота обратно.
void GraphPanel::rotate()
{
    bool sideways = !hist_plot->sideways();
    hist_plot->set_orientation(sideways);
    time_plot->setVisible(sideways);
}

void GraphPanel::configure(const Experiment& exp, double low, double high, double peak)
{
    Quantity q = quantity();
    kind_ = q.kind;
    axis_ = labels::axis_label(q.obj, q.kind);
    peak_ = peak;
    double s = exp.scale(q.obj, q.kind);
    xs_.resize(CURVE_POINTS);
    pdf_.resize(CURVE_POINTS);
    for (int k = 0; k < CURVE_POINTS; ++k) {
        xs_[k] = low + (high - low) * k / (CURVE_POINTS - 1);
        pdf_[k] = theory::pdf(q.kind, xs_[k], s);
    }
    time_plot->configure(axis_, low, high);
    configure_hist();
    last_count_ = exp.series.at(q).count();
}

void GraphPanel::configure_hist()
{
    hist_plot->configure(axis_, xs_, pdf_, peak_, labels::density_unit(kind_), kind_ != Kind::Energy);
}

void GraphPanel::refresh(const Experiment& exp, bool fast)
{
    Quantity q = quantity();
    const TimeSeries& series = exp.series.at(q);
    auto last = series.last();
    std::optional<double> current;
    if (last)
        current = last->second;
    // Новое значение "подращивает" свой столбик — в медленном режиме он подсвечивается.
    bool new_sample = series.count() > last_count_;
    last_count_ = series.count();

    int digits = q.kind == Kind::Energy ? 1 : 0;
    value_->setText(QString("= <b>%1</b> %2")
                        .arg(current ? style::fmt(*current, digits) : QString::fromUtf8("—"), labels::unit(q.kind)));
    if (time_plot->isVisible()) {
        std::optional<double> theory_mean;
        if (q.kind != Kind::Projection)
            theory_mean = theory::mean(q.kind, exp.scale(q.obj, q.kind));
        time_plot->update_view(series, theory_mean);
    }
    hist_plot->update_view(exp.hist.at(q), current, new_sample && !fast);
    stats_->setText(stats_text(exp, q));
}

// Кусок текста, который нельзя переносить посередине (число с единицами и т.п.).
static QString nowrap(const QString& html)
{
    return "<span style='white-space:nowrap'>" + html + "</span>";
}

// Переносы строк — только между частями, а не внутри числа или единиц
// (важно, когда подписи стоят узкой колонкой справа).
QString stats_text(const Experiment& exp, Quantity q)
{
    const Histogram& hist = exp.hist.at(q);
    double s = exp.scale(q.obj, q.kind);
    QString theory = QString::fromUtf8("<span style='color:%1'>(теор.&nbsp;%2)</span>").arg(style::THEORY);
    int digits = q.kind == Kind::Energy ? 2 : 0;
    QString unit = labels::unit(q.kind);
    QString mean = nowrap(QString::fromUtf8("⟨%1⟩ = <b>%2</b> %3")
                              .arg(labels::quantity(q.obj, q.kind), style::fmt(hist.mean(), digits), unit))
                   + " " + nowrap(theory.arg(style::fmt(theory::mean(q.kind, s), digits)));
    double divisor = labels::variance_divisor(q.kind);
    QString var_unit = labels::variance_unit(q.kind).replace(" ", "&nbsp;");
    QString variance = nowrap(QString("D = <b>%1</b>%2").arg(style::fmt(hist.variance() / divisor, 1), var_unit))
                       + " " + nowrap(theory.arg(style::fmt(theory::variance(q.kind, s) / divisor, 1)));
    return mean + "<br>" + variance;
}
