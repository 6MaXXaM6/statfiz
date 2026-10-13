// Самопроверки собранной программы (см. checks.h).

#include "checks.h"

#include <QElapsedTimer>
#include <QFile>
#include <QTextStream>
#include <QTimer>
#include <cstdio>
#include <functional>
#include <vector>

#include "main_window.h"
#include "ui/style.h"

using theory::Kind;

// ----------------------------------------------------------------------
// --smoke-test
// ----------------------------------------------------------------------

void smoke_test(QApplication& app, MainWindow& window, const QString& report_path)
{
    QTimer::singleShot(500, &window, [&app, &window, report_path] {
        window.show_theory();
        window.show_authors();
        window.show_title();
        window.show_demo();
        DemoPage* demo = window.demo;
        demo->add_button->click();
        demo->panels[1]->show_quantity({Obj::Single, Kind::Energy});
        demo->run->mode->buttons.at("fast")->click();
        demo->run->btn_start->click();
        QTimer::singleShot(4000, &window, [&app, demo, report_path] {
            QFile file(report_path);
            file.open(QIODevice::WriteOnly | QIODevice::Text);
            QTextStream out(&file);
            long long collisions = demo->exp.gas->collisions;
            if (collisions > 0 && demo->panels.size() == 2)
                out << "OK collisions=" << collisions << " panels=" << demo->panels.size() << "\n";
            else
                out << "FAIL\n";
            file.close();
            app.quit();
        });
    });
}

// ----------------------------------------------------------------------
// --layout-check
// ----------------------------------------------------------------------

using Step = std::pair<QString, std::function<void()>>;

// Как будто пользователь ввёл число: значение + сигнал без задержки.
static std::function<void()> set_param(ParamControl* control, int value)
{
    return [control, value] {
        control->spin->setValue(value);
        emit control->changed(value);
    };
}

// Действия пользователя по порядку (как в tools/layout_check.py Python-версии).
static std::vector<Step> scenario(DemoPage* page)
{
    RunControls* run = page->run;
    GasPanel* gas = page->gas;
    auto click = [](QAbstractButton* b) { return [b] { b->click(); }; };
    auto rotate = [page](size_t n) { return [page, n] { page->panels[n]->hist_plot->rotate_button->click(); }; };
    auto show = [page](size_t n, Quantity q) { return [page, n, q] { page->panels[n]->show_quantity(q); }; };

    std::vector<Step> steps = {
        {"Старт", click(run->btn_start)},
        {"Быстро", click(run->mode->buttons.at("fast"))},
        {"Медленно", click(run->mode->buttons.at("slow"))},
        {"Пауза", click(run->btn_pause)},
        {"Продолжить", click(run->btn_pause)},
        {"↻ график 1 (только распределение)", rotate(0)},
        {"↻ график 1 обратно", rotate(0)},
        {"Добавить график 2", click(page->add_button)},
        {"график 2: E₁", show(1, {Obj::Single, Kind::Energy})},
        {"↻ график 2", rotate(1)},
        {"график 2: v₂,x", show(1, {Obj::Second, Kind::Projection})},
        {"Смесь", click(gas->gas_mode->buttons.at("mix"))},
        {"Пара A–B", click(gas->pair->buttons.at("AB"))},
        {"график 1: E₂", show(0, {Obj::Second, Kind::Energy})},
        {"Быстро (2 графика)", click(run->mode->buttons.at("fast"))},
        {"Один газ", click(gas->gas_mode->buttons.at("pure"))},
        {"✕ график 2", [page] { page->remove_panel(page->panels[1]); }},
        {"Добавить график 2 снова", click(page->add_button)},
        {"Медленно", click(run->mode->buttons.at("slow"))},
        {"Стоп", click(run->btn_stop)},
        {"Старт снова", click(run->btn_start)},
        {"⛶ графики на весь экран", click(page->zoom_button)},
        {"↻ график 1 (на весь экран)", rotate(0)},
        {"↙ вернуть", click(page->zoom_button)},
        // Крайние значения параметров и выбор молекул мышью
        {"T = 1500", set_param(gas->temperature, 1500)},
        {"m_A = 1", set_param(gas->mass_a, 1)},
        {"N = 300", set_param(gas->n_total, 300)},
        {"m_A = 200", set_param(gas->mass_a, 200)},
        {"T = 50", set_param(gas->temperature, 50)},
        {"Смесь, m_B = 1", [gas] { gas->gas_mode->buttons.at("mix")->click(); set_param(gas->mass_b, 1)(); }},
        {"N_B = 1 (одна чужая)", set_param(gas->n_b, 1)},
        {"N = 2", set_param(gas->n_total, 2)},
        {"столбиков: 80", set_param(page->bins, 80)},
        {"столбиков: 10", set_param(page->bins, 10)},
        {"память: 5000", set_param(page->memory, 5000)},
        {"память: 10", set_param(page->memory, 10)},
        {"Один газ, N = 150", [gas] { gas->gas_mode->buttons.at("pure")->click(); set_param(gas->n_total, 150)(); }},
        {"Все одинаковые", click(gas->start->buttons.at("beam"))},
        {"без столкновений", [gas] { gas->collisions->setChecked(false); }},
        {"со столкновениями", [gas] { gas->collisions->setChecked(true); }},
        {"не по всем молекулам", [run] { run->ensemble_box->setChecked(false); }},
        {"Максвелл", click(gas->start->buttons.at("maxwell"))},
    };
    for (size_t n = 0; n < QUANTITIES.size(); ++n) {
        steps.push_back({QString("график 1: величина %1").arg(n), show(0, QUANTITIES[n])});
        steps.push_back({QString("график 2: величина %1").arg(n), show(1, QUANTITIES[n])});
    }
    return steps;
}

// Нарушения компоновки в текущем состоянии окна.
static QStringList problems(MainWindow& win, QWidget* page)
{
    QStringList found;
    QSize hint = page->minimumSizeHint();
    if (hint.width() > page->width() || hint.height() > page->height())
        found << QString("страница требует %1x%2, а есть %3x%4")
                     .arg(hint.width()).arg(hint.height()).arg(page->width()).arg(page->height());
    QRect area(0, 0, win.width(), win.height());
    for (QWidget* w : page->findChildren<QWidget*>()) {
        bool control = qobject_cast<QAbstractButton*>(w) || qobject_cast<QComboBox*>(w)
                       || qobject_cast<QSlider*>(w) || qobject_cast<QSpinBox*>(w);
        if (!control || !w->isVisibleTo(&win))
            continue;
        QRect r(w->mapTo(&win, QPoint(0, 0)), w->size());
        if (!area.contains(r)) {
            auto* b = qobject_cast<QAbstractButton*>(w);
            found << QString("за краем: %1 (%2, %3, %4x%5)")
                         .arg(b ? b->text().left(25) : w->metaObject()->className())
                         .arg(r.x()).arg(r.y()).arg(r.width()).arg(r.height());
        }
    }
    return found;
}

// Где на экране графики (чтобы заметить, если они "ездят" во время расчёта).
static std::vector<QRect> plot_areas(DemoPage* page)
{
    std::vector<QRect> areas;
    for (GraphPanel* panel : page->panels)
        for (QWidget* plot : std::initializer_list<QWidget*>{panel->time_plot, panel->hist_plot})
            areas.emplace_back(plot->mapTo(page, QPoint(0, 0)), plot->size());
    return areas;
}

static void settle(QApplication& app)
{
    for (int k = 0; k < 3; ++k) {  // отложенные перекладки виджетов, как в настоящем цикле событий
        QApplication::sendPostedEvents();
        app.processEvents();
    }
}

// Страница теории: каждый раздел, движки в крайних положениях — ничего не должно вылезать за окно.
static int check_theory(QApplication& app, MainWindow& win, const QString& screen)
{
    win.show_theory();
    TheoryPage* page = win.theory;
    int bad = 0;
    for (int k = 0; k < page->section_count(); ++k) {
        page->show_section(k);
        if (k == 0)
            page->drawer->open();  // список разделов тоже должен помещаться
        else
            page->drawer->close();
        QElapsedTimer wait;  // дождаться, пока панель доедет (анимация ~0.2 с)
        wait.start();
        while (wait.elapsed() < 300)
            app.processEvents();
        for (int extreme : {0, 1}) {
            for (ParamControl* c : page->stack->widget(k)->findChildren<ParamControl*>())
                c->spin->setValue(extreme ? c->spin->maximum() : c->spin->minimum());
            settle(app);
            QStringList found = problems(win, page);
            if (!found.isEmpty()) {
                ++bad;
                std::printf("  [%s] теория, раздел %d:\n", qPrintable(screen), k + 1);
                for (const QString& f : found.mid(0, 8))
                    std::printf("       %s\n", qPrintable(f));
            }
        }
    }
    win.show_demo();
    return bad;
}

static int check_screen(QApplication& app, const QString& screen)
{
    QStringList wh = screen.split('x');
    qputenv("RELATIVE_SCREEN", screen.toUtf8());
    style::init_style(app);
    MainWindow win;
    win.setFixedSize(wh[0].toInt(), wh[1].toInt());  // как на весь экран: окно больше экрана не станет
    win.show();
    win.show_demo();
    settle(app);
    DemoPage* page = win.demo;
    int bad = 0;
    for (const auto& [name, action] : scenario(page)) {
        action();
        page->run->timer.stop();
        settle(app);
        QStringList found;
        if (page->run->state() == RunControls::State::Running) {
            auto before = plot_areas(page);
            bool moved = false;
            for (int k = 0; k < 30; ++k) {
                page->run->frame();
                page->run->timer.stop();  // кадры считаем вручную
                app.processEvents();
                moved = moved || plot_areas(page) != before;
            }
            if (moved)
                found << "графики сдвигаются во время расчёта";
        }
        found += problems(win, page);
        if (!found.isEmpty()) {
            ++bad;
            std::printf("  [%s] %s:\n", qPrintable(screen), qPrintable(name));
            for (const QString& f : found.mid(0, 8))
                std::printf("       %s\n", qPrintable(f));
        }
    }
    bad += check_theory(app, win, screen);
    std::printf("%s: %s\n", qPrintable(screen),
                bad ? qPrintable(QString("проблем после %1 действий").arg(bad)) : "OK");
    return bad;
}

int layout_check(QApplication& app, const QStringList& screens)
{
    QStringList list = screens.isEmpty() ? QStringList{"1024x768", "1366x768", "1920x1080"} : screens;
    int total = 0;
    for (const QString& s : list)
        total += check_screen(app, s);
    return total ? 1 : 0;
}

// ----------------------------------------------------------------------
// --screenshot WxH страница кадров файл.png [fast] [add=v1] [first=vrelx] [rotate] [mix] [zoom] [beam] [nocoll]
// ----------------------------------------------------------------------

int screenshot(QApplication& app, const QStringList& args)
{
    if (args.size() < 4) {
        std::printf("--screenshot WxH title|demo|theory|authors кадров файл.png [настройки]\n");
        return 2;
    }
    QStringList wh = args[0].split('x');
    qputenv("RELATIVE_SCREEN", args[0].toUtf8());
    style::init_style(app);
    MainWindow win;
    win.resize(wh[0].toInt(), wh[1].toInt());
    win.show();
    QString page = args[1];
    int frames = args[2].toInt();
    if (page == "demo") win.show_demo();
    if (page == "theory") win.show_theory();
    for (const QString& opt : args.mid(4))
        if (opt.startsWith("section="))
            win.theory->show_section(opt.section('=', 1).toInt() - 1);
    if (args.mid(4).contains("drawer")) {
        win.theory->drawer->open();
        QElapsedTimer wait;  // дать панели доехать
        wait.start();
        while (wait.elapsed() < 400)
            app.processEvents();
    }
    if (page == "authors") win.show_authors();

    const std::map<QString, Quantity> names = {
        {"vrel", {Obj::Pair, Kind::Modulus}},   {"vrelx", {Obj::Pair, Kind::Projection}},
        {"v1", {Obj::Single, Kind::Modulus}},   {"v1x", {Obj::Single, Kind::Projection}},
        {"v2", {Obj::Second, Kind::Modulus}},   {"v2x", {Obj::Second, Kind::Projection}},
        {"e1", {Obj::Single, Kind::Energy}},    {"e2", {Obj::Second, Kind::Energy}},
    };
    DemoPage* d = win.demo;
    for (const QString& opt : args.mid(4)) {
        QString key = opt.section('=', 0, 0), value = opt.section('=', 1);
        if (key == "fast") d->run->mode->buttons.at("fast")->click();
        if (key == "add") d->add_panel(names.at(value));
        if (key == "first") d->panels[0]->show_quantity(names.at(value));
        if (key == "rotate") d->panels[0]->rotate();
        if (key == "mix") d->gas->gas_mode->buttons.at("mix")->click();
        if (key == "zoom") d->zoom_button->click();
        if (key == "beam") d->gas->start->buttons.at("beam")->click();
        if (key == "nocoll") d->gas->collisions->setChecked(false);
    }
    if (page == "demo") {
        d->run->start();
        d->run->timer.stop();
        QElapsedTimer clock;
        clock.start();
        for (int k = 0; k < frames; ++k) {
            d->run->frame();
            d->run->timer.stop();  // кадры считаем вручную
            app.processEvents();
        }
        std::printf("ms/frame: %.1f\n", clock.elapsed() / double(std::max(frames, 1)));
    }
    app.processEvents();
    win.grab().save(args[3]);
    std::printf("saved %s\n", qPrintable(args[3]));
    return 0;
}
