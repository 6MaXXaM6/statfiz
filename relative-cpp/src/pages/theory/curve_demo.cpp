// Живые графики раздела теории (см. curve_demo.h). Все формулы — из model/theory.h.

#include "pages/theory/curve_demo.h"

#include <QSpinBox>
#include <cmath>

#include "model/experiment.h"
#include "ui/labels.h"
#include "settings.h"
#include "ui/style.h"

using theory::Kind;

constexpr int START_T = settings::START_TEMPERATURE;  // начальные параметры (серая кривая)
constexpr int START_M = settings::START_MASS_A;
constexpr int CURVE_POINTS = 300;
constexpr double AXIS_ROOM = 1.6;   // ось x с запасом: кривая может расшириться, не выходя за край

// Кривая f(x) для x от low до high
static CurvePlot::Curve curve(Kind kind, double s, double low, double high, const QColor& color,
                              bool dashed, const QString& label)
{
    CurvePlot::Curve c;
    c.color = color;
    c.dashed = dashed;
    c.label = label;
    for (int k = 0; k < CURVE_POINTS; ++k) {
        double x = low + (high - low) * k / (CURVE_POINTS - 1);
        c.xs.push_back(x);
        c.ys.push_back(theory::pdf(kind, x, s));
    }
    return c;
}

static double kT(double temperature)  // kT в единицах 10⁻²¹ Дж
{
    return physics::K_B * temperature / ENERGY_UNIT;
}

CurveDemo::CurveDemo(Variant variant) : variant_(variant)
{
    start_m2_ = variant == Variant::Mixture ? 4 : START_M;
    temperature = new ParamControl(QString::fromUtf8("Температура T, К"), settings::TEMPERATURE_MIN,
                                   settings::TEMPERATURE_MAX, START_T);
    bool two = variant == Variant::Relative || variant == Variant::Mixture;
    mass_1 = new ParamControl(QString::fromUtf8(two ? "Масса m₁, а.е.м." : "Масса m, а.е.м."),
                              settings::MASS_MIN, settings::MASS_MAX, START_M);
    mass_2 = new ParamControl(QString::fromUtf8("Масса m₂, а.е.м."), settings::MASS_MIN, settings::MASS_MAX, start_m2_);
    mass_2->setVisible(two);
    plot_ = new CurvePlot;
    plot_->setMinimumHeight(style::px(12));
    readout_ = label("", 0.95);
    readout_->setWordWrap(true);
    readout_->setTextFormat(Qt::RichText);

    // Перерисовка сразу при движении движка или вводе числа (без задержки — это просто формулы)
    for (ParamControl* c : {temperature, mass_1, mass_2}) {
        connect(c->slider, &QSlider::valueChanged, this, [this] { update_view(); });
        connect(c->spin, QOverload<int>::of(&QSpinBox::valueChanged), this, [this] { update_view(); });
    }
    QPushButton* fit = button(QString::fromUtf8("Подогнать масштаб"), [this] { fit_axis(); });
    QPushButton* again = button(QString::fromUtf8("Сбросить"), [this] { reset(); });

    setLayout(vbox({{plot_, 1}, readout_, temperature, mass_1, mass_2,
                    hbox({Item::spring(), fit, again}, style::px(0.4))},
                   style::px(0.3)));
    reset();
}

void CurveDemo::reset()
{
    temperature->set_value_silently(START_T);
    mass_1->set_value_silently(START_M);
    mass_2->set_value_silently(start_m2_);
    fit_axis();
}

// Правый край оси x, в котором помещаются все кривые при текущих параметрах.
double CurveDemo::scale_range() const
{
    double t = temperature->value();
    double m1 = mass_1->value(), m2 = mass_2->value();
    switch (variant_) {
    case Variant::Energy:
        return theory::value_range(Kind::Energy, kT(t)).second;
    case Variant::Relative:
    case Variant::Mixture: {
        // самая широкая из кривых |v₁|, |v₂|, |v_отн| — у v_отн (μ меньше обеих масс)
        double mu = theory::reduced_mass(m1, m2);
        return theory::value_range(Kind::Modulus, theory::sigma_for(mu, t)).second;
    }
    case Variant::Projection:
    case Variant::Modulus:
        break;
    }
    Kind kind = variant_ == Variant::Projection ? Kind::Projection : Kind::Modulus;
    return theory::value_range(kind, theory::sigma_for(m1, t)).second;
}

void CurveDemo::fit_axis()
{
    x_high_ = scale_range() * AXIS_ROOM;
    update_view();
}

void CurveDemo::update_view()
{
    double t = temperature->value();
    double m1 = mass_1->value(), m2 = mass_2->value();
    double low = variant_ == Variant::Projection ? -x_high_ : 0.0;
    QColor grey("#9a9a9a");
    std::vector<CurvePlot::Curve> curves;
    std::vector<CurvePlot::Marker> markers;
    QString text;
    QString start = QString::fromUtf8("T = %1 К, m = %2").arg(START_T).arg(START_M);

    switch (variant_) {
    case Variant::Projection: {
        double s = theory::sigma_for(m1, t);
        curves.push_back(curve(Kind::Projection, theory::sigma_for(START_M, START_T), low, x_high_, grey, true, start));
        curves.push_back(curve(Kind::Projection, s, low, x_high_, style::PROJ, false, QString::fromUtf8("f(v<sub>x</sub>)")));
        markers = {{-s, style::PROJ, QString::fromUtf8("−σ")}, {s, style::PROJ, QString::fromUtf8("+σ")}};
        text = QString::fromUtf8("σ = √(kT/m) = <b>%1</b> м/с &nbsp; ⟨v<sub>x</sub>⟩ = 0 &nbsp; "
                                 "D = σ² = <b>%2</b>·10³ (м/с)²")
                   .arg(style::fmt(s), style::fmt(s * s / 1e3, 1));
        break;
    }
    case Variant::Modulus: {
        double s = theory::sigma_for(m1, t);
        curves.push_back(curve(Kind::Modulus, theory::sigma_for(START_M, START_T), low, x_high_, grey, true, start));
        curves.push_back(curve(Kind::Modulus, s, low, x_high_, style::REL, false, QString::fromUtf8("f(|v|)")));
        double mean = theory::mean(Kind::Modulus, s), rms = s * std::sqrt(2.0);
        markers = {{s, style::MOL2, QString::fromUtf8("v<sub>вер</sub>")},
                   {mean, style::THEORY, QString::fromUtf8("⟨v⟩")},
                   {rms, style::PROJ, QString::fromUtf8("√⟨v²⟩")}};
        text = QString::fromUtf8("<span style='color:%1'>v<sub>вер</sub> = √(kT/m) = <b>%2</b></span> &nbsp; "
                                 "<span style='color:%3'>⟨v⟩ = <b>%4</b></span> &nbsp; "
                                 "<span style='color:%5'>√⟨v²⟩ = <b>%6</b></span> м/с")
                   .arg(style::MOL2, style::fmt(s), style::THEORY, style::fmt(mean), style::PROJ, style::fmt(rms));
        break;
    }
    case Variant::Relative:
    case Variant::Mixture: {
        double mu = theory::reduced_mass(m1, m2);
        double s1 = theory::sigma_for(m1, t), s2 = theory::sigma_for(m2, t), sr = theory::sigma_for(mu, t);
        double start_mu = theory::reduced_mass(START_M, start_m2_);
        curves.push_back(curve(Kind::Modulus, theory::sigma_for(start_mu, START_T), low, x_high_, grey, true,
                               QString::fromUtf8("v<sub>отн</sub> в начале")));
        curves.push_back(curve(Kind::Modulus, s1, low, x_high_, style::MOL1, false, QString::fromUtf8("|v<sub>1</sub>|")));
        curves.push_back(curve(Kind::Modulus, s2, low, x_high_, style::MOL2, m1 == m2, QString::fromUtf8("|v<sub>2</sub>|")));
        curves.push_back(curve(Kind::Modulus, sr, low, x_high_, style::REL, false, QString::fromUtf8("|v<sub>отн</sub>|")));
        double mean_1 = theory::mean(Kind::Modulus, s1), mean_r = theory::mean(Kind::Modulus, sr);
        markers = {{mean_1, style::MOL1, QString::fromUtf8("⟨|v<sub>1</sub>|⟩")},
                   {mean_r, style::REL, QString::fromUtf8("⟨|v<sub>отн</sub>|⟩")}};
        QString ratio = m1 == m2 ? QString::fromUtf8("√2 ≈ 1.414")
                                 : QString::fromUtf8("√(m₁/μ) = %1").arg(std::sqrt(m1 / mu), 0, 'f', 3);
        text = QString::fromUtf8("μ = m₁m₂/(m₁+m₂) = <b>%1</b> а.е.м.<br>"
                                 "⟨|v<sub>1</sub>|⟩ = %2, ⟨|v<sub>2</sub>|⟩ = %3, ⟨|v<sub>отн</sub>|⟩ = <b>%4</b> м/с<br>"
                                 "⟨|v<sub>отн</sub>|⟩ / ⟨|v<sub>1</sub>|⟩ = <b>%5</b>")
                   .arg(style::fmt(mu, 1), style::fmt(mean_1), style::fmt(theory::mean(Kind::Modulus, s2)),
                        style::fmt(mean_r), ratio);
        break;
    }
    case Variant::Energy: {
        double s = kT(t);
        curves.push_back(curve(Kind::Energy, kT(START_T), low, x_high_, grey, true, QString::fromUtf8("T = %1 К").arg(START_T)));
        curves.push_back(curve(Kind::Energy, s, low, x_high_, style::THEORY, false, QString::fromUtf8("f(E)")));
        markers = {{s, style::REL, QString::fromUtf8("⟨E⟩ = kT")}};
        text = QString::fromUtf8("kT = <b>%1</b>·10⁻²¹ Дж &nbsp; ⟨E⟩ = kT &nbsp; D = (kT)²<br>"
                                 "Масса m = %2 а.е.м. в формулу не входит — подвигайте её движок.")
                   .arg(style::fmt(s, 2)).arg(m1);
        break;
    }
    }

    // Ось плотности: для скоростей плотность ~10⁻³ с/м, поэтому показываем её в единицах 10ⁿ
    double peak = 0;
    for (const CurvePlot::Curve& c : curves)
        for (double y : c.ys)
            peak = std::max(peak, y);
    int exponent = variant_ == Variant::Energy ? 0 : static_cast<int>(std::floor(std::log10(peak)));
    double factor = std::pow(10.0, -exponent);
    for (CurvePlot::Curve& c : curves)
        for (double& y : c.ys)
            y *= factor;
    plot_->set_x_range(low, x_high_);
    plot_->set_y_range(0, peak * factor * 1.15);
    Kind kind = variant_ == Variant::Energy ? Kind::Energy : variant_ == Variant::Projection ? Kind::Projection : Kind::Modulus;
    QString value = variant_ == Variant::Energy ? "E" : variant_ == Variant::Projection ? "v<sub>x</sub>" : "|v|";
    QString power = exponent ? "10" + style::sup(exponent) + " " : "";
    plot_->set_axis_label(PlotBase::Axis::Bottom, value + ", " + labels::unit(kind));
    plot_->set_axis_label(PlotBase::Axis::Left, "f, " + power + labels::density_unit(kind));
    plot_->set_curves(std::move(curves));
    plot_->set_markers(std::move(markers));
    readout_->setText(text);
}
