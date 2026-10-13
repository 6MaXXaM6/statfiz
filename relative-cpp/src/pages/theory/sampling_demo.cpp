// Набор статистики из случайных отсчётов (см. sampling_demo.h).

#include "pages/theory/sampling_demo.h"

#include <cmath>

#include "model/theory.h"
#include "settings.h"
#include "ui/labels.h"
#include "ui/style.h"
#include "ui/widgets.h"

using theory::Kind;

constexpr int BINS = 30;

SamplingDemo::SamplingDemo()
    : sigma_(theory::sigma_for(28, 300)),
      hist_(0, theory::value_range(Kind::Modulus, sigma_).second, BINS)
{
    plot_ = new HistPlot(false);
    plot_->rotate_button->hide();  // здесь поворачивать нечего
    plot_->setMinimumHeight(style::px(12));
    std::vector<double> xs, pdf;
    for (int k = 0; k <= 300; ++k) {
        xs.push_back(hist_.high() * k / 300);
        pdf.push_back(theory::pdf(Kind::Modulus, xs.back(), sigma_));
    }
    plot_->configure(QString::fromUtf8("|v|, м/с"), xs, pdf, theory::peak(Kind::Modulus, sigma_),
                     labels::density_unit(Kind::Modulus), true);
    readout_ = label("", 0.95);
    readout_->setWordWrap(true);

    auto_button_ = button(QString::fromUtf8("▶ Набирать"), {}, true);
    connect(auto_button_, &QPushButton::toggled, this, [this](bool on) {
        if (on)
            timer_.start(50);
        else
            timer_.stop();
    });
    connect(&timer_, &QTimer::timeout, this, [this] { add_samples(settings::SAMPLES_PER_TICK); });

    auto* buttons = hbox({button("+10", [this] { add_samples(10); }),
                          button("+100", [this] { add_samples(100); }),
                          button("+1000", [this] { add_samples(1000); }),
                          auto_button_, Item::spring(),
                          button(QString::fromUtf8("Сбросить"), [this] { reset(); })},
                         style::px(0.3));
    setLayout(vbox({{plot_, 1}, readout_, buttons}, style::px(0.3)));
    update_view();
}

// Случайное |v| по распределению Рэлея: если U равномерно на (0, 1], то σ·√(−2 ln U)
// распределено с плотностью v/σ² · exp(−v²/2σ²) (обратная функция распределения).
void SamplingDemo::add_samples(int n)
{
    std::uniform_real_distribution<double> uniform(0.0, 1.0);
    for (int k = 0; k < n; ++k)
        hist_.add(sigma_ * std::sqrt(-2.0 * std::log(1.0 - uniform(rng_))));
    update_view();
}

void SamplingDemo::reset()
{
    auto_button_->setChecked(false);
    hist_.reset();
    update_view();
}

void SamplingDemo::update_view()
{
    plot_->update_view(hist_, std::nullopt, false);
    // Насколько гистограмма отличается от теории: L1 = Σ |f_опыт − f_теор| · ширина столбика
    std::vector<double> dens = hist_.density();
    double distance = 0;
    for (int k = 0; k < hist_.bins(); ++k)
        distance += std::fabs(dens[k] - theory::pdf(Kind::Modulus, hist_.center(k), sigma_)) * hist_.width();
    long long n = static_cast<long long>(hist_.total());
    readout_->setText(QString::fromUtf8(
        "N = <b>%1</b> отсчётов &nbsp; ⟨|v|⟩ = <b>%2</b> м/с (теор. %3)<br>"
        "отличие от теории L1 = <b>%4</b> (≈ 1/√N: чтобы уменьшить вдвое, нужно вчетверо больше отсчётов)")
        .arg(style::fmt(n), style::fmt(hist_.mean()), style::fmt(theory::mean(Kind::Modulus, sigma_)),
             n ? style::fmt(distance, 3) : QString::fromUtf8("—")));
}
