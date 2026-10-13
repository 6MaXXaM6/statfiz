// Панель "Газ": режим, температура, число молекул, массы, пара молекул.

#include "pages/demo/gas_panel.h"

#include "settings.h"
#include "ui/style.h"

static const QString PURE = "pure", MIX = "mix", MAXWELL = "maxwell", BEAM = "beam";

GasPanel::GasPanel(const Experiment& exp)
{
    const GasParams& p = exp.params;
    gas_mode = new Choice("", {{PURE, QString::fromUtf8("Один газ")}, {MIX, QString::fromUtf8("Смесь A + B")}});
    using namespace settings;
    temperature = new ParamControl(QString::fromUtf8("Температура T, К"), TEMPERATURE_MIN, TEMPERATURE_MAX,
                                   static_cast<int>(exp.temperature));
    n_total = new ParamControl(QString::fromUtf8("Число молекул N"), N_MIN, N_MAX, p.n_total);
    mass_a = new ParamControl(QString::fromUtf8("Масса A, а.е.м."), MASS_MIN, MASS_MAX, static_cast<int>(p.mass_a));
    mass_b = new ParamControl(QString::fromUtf8("Масса B, а.е.м."), MASS_MIN, MASS_MAX, static_cast<int>(p.mass_b));
    n_b = new ParamControl(QString::fromUtf8("Молекул B"), 1, p.n_total - 1, p.n_b);
    n_b->setToolTip(QString::fromUtf8("1 — в газе A одна «чужая» молекула B"));
    pair = new Choice(QString::fromUtf8("Пара молекул"),
                       {{"AA", QString::fromUtf8("A – A")}, {"AB", QString::fromUtf8("A – B")}, {"BB", QString::fromUtf8("B – B")}});

    // Опыт из лекции 8: все молекулы стартуют с одной скоростью в одну сторону —
    // распределение Максвелла устанавливается только благодаря столкновениям.
    start = new Choice(QString::fromUtf8("Начальные скорости"),
                       {{MAXWELL, QString::fromUtf8("Максвелл")}, {BEAM, QString::fromUtf8("Все одинаковые")}});
    start->setToolTip(QString::fromUtf8("«Все одинаковые»: молекулы летят в одну сторону с одной скоростью.\n"
                                        "Посмотрите, как столкновения превращают это в распределение Максвелла."));
    collisions = new QCheckBox(QString::fromUtf8("Столкновения молекул"));
    collisions->setChecked(true);
    collisions->setFocusPolicy(Qt::NoFocus);
    collisions->setToolTip(QString::fromUtf8("Выключено — молекулы пролетают сквозь друг друга, отражаются только от стенок:\n"
                                             "модули скоростей тогда не меняются и равновесие не наступает."));

    connect(gas_mode, &Choice::changed, this, &GasPanel::gas_changed);
    connect(start, &Choice::changed, this, &GasPanel::gas_changed);
    connect(collisions, &QCheckBox::toggled, this, &GasPanel::gas_changed);
    for (ParamControl* c : {mass_a, mass_b, n_total, n_b})
        connect(c, &ParamControl::changed, this, &GasPanel::gas_changed);
    connect(n_total, &ParamControl::changed, this, [this](int n) { n_b->set_range(1, std::max(1, n - 1)); });
    connect(pair, &Choice::changed, this, &GasPanel::pair_chosen);
    connect(temperature, &ParamControl::changed, this, &GasPanel::temperature_changed);

    setFont(style::font(settings::GAS_PANEL_FONT));
    // start и collisions в карточку "Газ" не входят: их ставит страница под кнопки
    // "Старт / Пауза" (это выбор опыта, а справа при смеси и так тесно).
    setLayout(vbox({card({gas_mode, temperature, n_total, mass_a, mass_b, n_b, pair},
                         QString::fromUtf8("Газ"), style::px(0.1))}));
}

GasParams GasPanel::params() const
{
    GasParams p;
    p.mode = gas_mode->value() == MIX ? GasMode::Mix : GasMode::Pure;
    p.mass_a = mass_a->value();
    p.mass_b = mass_b->value();
    p.n_total = n_total->value();
    p.n_b = n_b->value();
    p.start = start->value() == BEAM ? physics::Start::Beam : physics::Start::Maxwell;
    p.collisions = collisions->isChecked();
    return p;
}

void GasPanel::sync_with(const Experiment& exp)
{
    bool mix = exp.params.mode == GasMode::Mix;
    for (QWidget* w : std::initializer_list<QWidget*>{mass_b, n_b, pair})
        w->setVisible(mix);
    std::vector<QString> types;
    for (const std::string& t : exp.available_pair_types())
        types.push_back(QString::fromStdString(t));
    pair->set_enabled_options(types);
    pair->set_value(QString::fromStdString(exp.pair_type));
}
