// Страница "Презентация": компоновка, события и отрисовка кадра.

#include "pages/demo/demo_page.h"

#include <algorithm>

#include "pages/demo/readouts.h"
#include "settings.h"
#include "ui/icons.h"
#include "ui/style.h"

using theory::Kind;

constexpr size_t MAX_PANELS = 2;
// Второй график сначала показывает |v₁| — для сравнения с |v_отн|
constexpr Quantity SECOND_PANEL = {Obj::Single, Kind::Modulus};

DemoPage::DemoPage(std::function<void()> go_home, std::function<void()> go_theory)
{
    // --- части страницы ---
    box_ = new BoxView;
    run = new RunControls;
    vectors_ = new VectorView;
    legend_ = label("", settings::LEGEND_FONT);
    center(legend_);
    gas = new GasPanel(exp);
    bins = new ParamControl(QString::fromUtf8("Столбиков"), settings::BINS_MIN, settings::BINS_MAX, exp.bins, true, false);
    bins->setToolTip(QString::fromUtf8("Число столбиков в гистограммах; накопленная статистика сохраняется"));
    memory = new ParamControl(QString::fromUtf8("Память"), settings::MEMORY_MIN, settings::MEMORY_MAX,
                              exp.memory_collisions, true, false);
    memory->spin->setSingleStep(50);
    memory->setToolTip(QString::fromUtf8(
        "Сколько столкновений помнит статистика: старые отсчёты забываются как exp(−t/τ).\n"
        "Меньше — гистограмма быстрее перестраивается (например, после смены T), но шумнее.\n"
        "Больше — глаже, но дольше помнит старое. 300 — подобрано статистическим тестом."));
    panels_box_ = vbox({}, style::px(0.5));
    // Коротко, чтобы "Столбиков", "Память" и кнопки поместились в одну строку и на 1024×768
    add_button = button(QString::fromUtf8("+  График"), [this] { add_panel(SECOND_PANEL); });
    add_button->setToolTip(QString::fromUtf8("Добавить второй график"));
    // Кнопка "графики на весь экран": квадратная, той же высоты, что "+ График"
    zoom_button = button("", [this] { toggle_graphs_zoom(); }, true);
    int side = add_button->sizeHint().height();
    zoom_button->setFixedSize(side, side);
    zoom_button->setIcon(zoom_icon(side));
    zoom_button->setIconSize(QSize(side * 6 / 10, side * 6 / 10));
    zoom_button->setToolTip(QString::fromUtf8("Графики на весь экран (сосуд и настройки скрываются)"));
    ratio_ = label("", settings::RATIO_FONT);
    make_shrinkable(ratio_);
    // Высота строки сравнения постоянная (две строки), чтобы графики не прыгали, когда она появляется.
    ratio_->setFixedHeight(2 * ratio_->fontMetrics().lineSpacing() + style::px(0.3));

    // Слева: сосуд (квадратный, размер задаёт fit_box) и кнопки хода расчёта
    box_card_ = card({box_});
    box_card_->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Ignored);
    // Под кнопками хода — выбор опыта: начальные скорости и столкновения (из панели "Газ")
    run_card_ = card({run, gas->start, gas->collisions});
    run_card_->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
    left_ = new QWidget;
    left_->setLayout(vbox({{box_card_, 1}, run_card_}));

    // Справа: параметры газа и векторы (векторы сжимаются, если места мало)
    auto* vectors_box = vbox({vectors_, {legend_, 1}});
    vectors_box->setAlignment(vectors_, Qt::AlignHCenter);
    QFrame* vectors_card = card({vectors_box}, QString::fromUtf8("Скорости"));
    vectors_card->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Maximum);
    right_ = new QWidget;
    right_->setLayout(vbox({gas, vectors_card, Item::spring()}));
    // Ширину правой колонки считаем сразу — пока видны и настройки смеси,
    // чтобы при переключении "Один газ / Смесь" графики не сдвигались.
    right_width_ = right_->sizeHint().width();
    right_->setFixedWidth(right_width_);

    // Под графиками: строка сравнения (√2) или "+ График", затем число столбиков, память и "на весь экран"
    // "+ График" — в строке сравнения: она пуста, пока график один, а при двух кнопка скрыта
    middle_ = card({{panels_box_, 1}, hbox({{ratio_, 1}, add_button}, style::px(0.4)),
                           hbox({bins, memory, Item::spring(), zoom_button}, style::px(0.6))},
                          "", style::px(0.3));
    int m = style::px(0.4);
    auto* body = hbox({left_, {middle_, 1}, right_}, m, QMargins(m, 0, m, m));
    header_ = header_bar(QString::fromUtf8("Относительная скорость молекул идеального газа"), leaving(go_home),
                         {{QString::fromUtf8("Теория"), leaving(go_theory)}});
    setLayout(vbox({header_, {body, 1}}, 0));

    // --- связи ---
    connect(run, &RunControls::started, this, &DemoPage::on_start);
    connect(run, &RunControls::tick, this, &DemoPage::on_tick);
    connect(run, &RunControls::mode_changed, this, &DemoPage::on_mode_changed);
    connect(run, &RunControls::ensemble_changed, this, [this](bool on) {
        exp.ensemble = on;
        refresh();
    });
    connect(box_, &BoxView::clicked, this, &DemoPage::on_box_clicked);
    connect(gas, &GasPanel::gas_changed, this, &DemoPage::on_gas_changed);
    connect(gas, &GasPanel::pair_chosen, this, [this](const QString& key) {
        changed([this, key] { exp.choose_pair(key.toStdString()); });
    });
    connect(gas, &GasPanel::temperature_changed, this, [this](int t) {
        changed([this, t] { exp.set_temperature(t); });
    });
    connect(bins, &ParamControl::changed, this, [this](int n) { changed([this, n] { exp.set_bins(n); }); });
    connect(memory, &ParamControl::changed, this, [this](int n) { exp.set_memory(n); });

    // Что видно сразу: |v_отн| и (если включено в settings.h) |v₁| — для сравнения, √2
    exp.ensemble = run->ensemble();
    add_panel({Obj::Pair, Kind::Modulus});
    if (settings::START_TWO_PANELS)
        add_panel(SECOND_PANEL);
}

// Первый показ страницы: опыт запускается сам (settings::AUTOSTART), чтобы сразу было что смотреть.
void DemoPage::showEvent(QShowEvent* event)
{
    QWidget::showEvent(event);
    if (settings::AUTOSTART && !autostarted_ && run->state() == RunControls::State::Stopped) {
        autostarted_ = true;
        run->start();
    }
}

// ----------------------------------------------------------------------
// Компоновка
// ----------------------------------------------------------------------

void DemoPage::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    fit_box();
}

// Графики на всю ширину: сосуд и колонка настроек скрываются (расчёт продолжается).
void DemoPage::toggle_graphs_zoom()
{
    bool zoomed = zoom_button->isChecked();
    left_->setVisible(!zoomed);
    right_->setVisible(!zoomed);
    for (GraphPanel* panel : panels)
        panel->set_side_stats(zoomed);  // во всю ширину подписи — справа от графиков
    zoom_button->setToolTip(QString::fromUtf8(zoomed ? "Вернуть сосуд и настройки"
                                                     : "Графики на весь экран (сосуд и настройки скрываются)"));
}

// Сосуд квадратный: ширина левой колонки = высота места под сосудом,
// но не меньше, чем нужно кнопкам, и так, чтобы средней колонке хватило места.
void DemoPage::fit_box()
{
    QMargins margins = box_card_->layout()->contentsMargins();
    int spacing = left_->layout()->spacing();
    int gap = style::px(0.4);
    // Высота — из высоты страницы, а не текущей высоты колонки (иначе сосуд не уменьшится).
    int free_height = height() - header_->height() - gap - run_card_->sizeHint().height() - spacing;
    int side = free_height - (margins.top() + margins.bottom()) + margins.left() + margins.right();
    // Средней колонке — не меньше, чем ей реально нужно (строка под графиками бывает широкой)
    int middle = std::max(style::px(settings::MIDDLE_MIN), middle_->minimumSizeHint().width());
    int room = width() - right_width_ - middle - 4 * gap;
    int w = std::max(std::min(side, room), run_card_->minimumSizeHint().width());
    int h = std::min(w, free_height);
    // Меняем размеры только если они другие — иначе Qt будет бесконечно перекладывать виджеты.
    if (left_->width() != w || left_->minimumWidth() != w)
        left_->setFixedWidth(w);
    if (box_card_->maximumHeight() != h)
        box_card_->setMaximumHeight(std::max(h, 1));
}

// Переход на другую страницу ставит расчёт на паузу.
std::function<void()> DemoPage::leaving(std::function<void()> go)
{
    return [this, go] {
        run->pause();
        go();
    };
}

// ----------------------------------------------------------------------
// Панели графиков
// ----------------------------------------------------------------------

void DemoPage::add_panel(Quantity q)
{
    if (panels.size() >= MAX_PANELS)
        return;
    auto* panel = new GraphPanel(q, !panels.empty());
    panel->set_side_stats(zoom_button->isChecked());
    connect(panel, &GraphPanel::quantity_changed, this, &DemoPage::on_experiment_changed);
    connect(panel, &GraphPanel::close_clicked, this, [this, panel] { remove_panel(panel); });
    panels.push_back(panel);
    panels_box_->addWidget(panel, 1);
    on_experiment_changed();
}

void DemoPage::remove_panel(GraphPanel* panel)
{
    panels.erase(std::find(panels.begin(), panels.end(), panel));
    panels_box_->removeWidget(panel);
    // Убираем с экрана сразу: deleteLater удалит виджет только на следующем цикле событий.
    panel->hide();
    panel->deleteLater();
    on_experiment_changed();
}

// ----------------------------------------------------------------------
// События
// ----------------------------------------------------------------------

void DemoPage::on_start()
{
    exp.rebuild();  // новый опыт: газ заново, статистика с нуля
    on_experiment_changed();
}

void DemoPage::on_tick(bool fast, double factor)
{
    if (fast)
        exp.advance_for_seconds(settings::FAST_BUDGET);
    else
        exp.advance_by(factor);
    refresh();
}

// Быстрый режим — для набора статистики (по всем молекулам: галочку включает RunControls).
// История во времени при смене режима начинается заново (см. Experiment::restart_history).
void DemoPage::on_mode_changed(bool)
{
    exp.ensemble = run->ensemble();
    exp.restart_history();
    on_experiment_changed();
}

void DemoPage::on_gas_changed()
{
    GasParams p = gas->params();
    // Опыт "Все одинаковые": короткая память, чтобы гистограмма показывала распределение
    // "сейчас" и было видно, как столбик расплывается в кривую Максвелла.
    // И побыстрее: чтобы пучок успел долететь до стенок и молекулы сделали по нескольку ударов.
    if (p.start != exp.params.start) {
        bool beam = p.start == physics::Start::Beam;
        int k = beam ? settings::RELAX_MEMORY : settings::START_MEMORY;
        memory->set_value_silently(k);
        exp.set_memory(k);
        run->speed->set_value_silently(beam ? settings::RELAX_SPEED : settings::START_SPEED);
    }
    exp.configure_gas(p);
    on_experiment_changed();
}

void DemoPage::on_box_clicked(double x, double y, int which)
{
    int k = exp.gas->nearest(x, y, settings::CLICK_DISTANCE);
    if (k >= 0)
        changed([this, k, which] { exp.select(k, which); });
}

// Выполнить действие над экспериментом и перестроить графики.
void DemoPage::changed(std::function<void()> action)
{
    action();
    on_experiment_changed();
}

// Изменились газ, выбор молекул или графики: заново настроить масштабы и подписи.
void DemoPage::on_experiment_changed()
{
    gas->sync_with(exp);
    configure_plots();
    refresh();
}

// ----------------------------------------------------------------------
// Отрисовка
// ----------------------------------------------------------------------

// Пары графиков "молекула — относительная скорость" одного вида (только скорости):
// возвращает величину молекулы, для которой на экране есть пара.
std::vector<Quantity> DemoPage::comparisons() const
{
    std::vector<Quantity> shown, result;
    for (GraphPanel* p : panels)
        shown.push_back(p->quantity());
    for (Quantity q : shown) {
        bool has_pair = std::find(shown.begin(), shown.end(), Quantity{Obj::Pair, q.kind}) != shown.end();
        if (q.obj != Obj::Pair && q.kind != Kind::Energy && has_pair)
            result.push_back(q);
    }
    return result;
}

void DemoPage::configure_plots()
{
    for (GraphPanel* panel : panels) {
        Kind kind = panel->quantity().kind;
        // Графики одного вида — в общем масштабе, чтобы разницу (например, в √2) было видно на глаз.
        double scale = 0, peak = 0;
        for (GraphPanel* other : panels) {
            Quantity q = other->quantity();
            if (q.kind != kind)
                continue;
            double s = exp.scale(q.obj, kind);
            scale = std::max(scale, s);
            peak = std::max(peak, theory::peak(kind, s));
        }
        auto [low, high] = theory::value_range(kind, scale);
        panel->configure(exp, low, high, peak);
    }

    double speed_scale = exp.max_speed_scale();
    box_->configure(exp.gas->box, speed_scale);
    vectors_->set_radius(settings::VECTOR_RADIUS * speed_scale);
    projection_of_.reset();
    for (GraphPanel* p : panels) {
        if (p->quantity().kind == Kind::Projection) {
            projection_of_ = p->quantity().obj;
            break;
        }
    }
    legend_->setText(vector_legend(projection_of_));
    add_button->setVisible(panels.size() < MAX_PANELS);
    if (comparisons().empty())
        ratio_->setText("");
}

void DemoPage::refresh()
{
    box_->update_view(exp, true);
    vectors_->update_view(exp, projection_of_);
    for (GraphPanel* panel : panels)
        panel->refresh(exp, run->fast());
    auto pairs = comparisons();
    if (!pairs.empty())
        ratio_->setText(ratio_text(exp, pairs.front().obj, pairs.front().kind));
}
