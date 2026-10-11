// Ход расчёта: состояния "стоп / идёт / пауза" и кадры по таймеру.

#include "pages/demo/run_controls.h"

#include <QElapsedTimer>
#include <algorithm>

#include "settings.h"
#include "ui/style.h"

RunControls::RunControls()
{
    timer.setTimerType(Qt::PreciseTimer);
    timer.setSingleShot(true);  // следующий кадр планируется после окончания текущего
    connect(&timer, &QTimer::timeout, this, &RunControls::frame);

    btn_start = button(QString::fromUtf8("▶  Старт"), [this] { start(); });
    btn_pause = button(QString::fromUtf8("❚❚  Пауза"), [this] { toggle_pause(); });
    btn_stop = button(QString::fromUtf8("■  Стоп"), [this] { stop(); });
    for (QPushButton* b : {btn_start, btn_pause, btn_stop})
        b->setFont(style::font(1.0, true));
    mode = new Choice("", {{"slow", QString::fromUtf8("Медленно")}, {"fast", QString::fromUtf8("Быстро")}});
    speed = new ParamControl(QString::fromUtf8("Скорость"), 1, settings::SLOW_COUNT, settings::START_SPEED, false);

    // Статистика по всем молекулам того же сорта, что выбранные: гистограммы набираются
    // в сотни раз быстрее. В быстром режиме включается сама.
    ensemble_box = new QCheckBox(QString::fromUtf8("Статистика по всем молекулам"));
    ensemble_box->setFocusPolicy(Qt::NoFocus);
    ensemble_box->setChecked(settings::START_ENSEMBLE);
    ensemble_box->setToolTip(QString::fromUtf8(
        "Включено — в гистограммы идут скорости всех молекул того же сорта (быстро набирается).\n"
        "Выключено — только выбранные молекулы 1 и 2 (как следить за одной молекулой)."));
    connect(ensemble_box, &QCheckBox::toggled, this, &RunControls::ensemble_changed);
    connect(mode, &Choice::changed, this, [this] {
        if (fast())
            ensemble_box->setChecked(true);
        update_buttons();
        emit mode_changed(fast());
    });

    setLayout(vbox({hbox({btn_start, btn_pause, btn_stop}),
                    hbox({{mode, 2}, {speed, 3}}),
                    ensemble_box},
                   style::px(0.2)));
    update_buttons();
}

void RunControls::start()
{
    emit started();
    set_state(State::Running);
}

void RunControls::toggle_pause()
{
    if (state_ == State::Running)
        set_state(State::Paused);
    else if (state_ == State::Paused)
        set_state(State::Running);
}

void RunControls::pause()
{
    if (state_ == State::Running)
        set_state(State::Paused);
}

void RunControls::stop()
{
    set_state(State::Stopped);
}

void RunControls::set_state(State state)
{
    state_ = state;
    if (state == State::Running)
        timer.start(settings::FRAME_MS);
    else
        timer.stop();
    update_buttons();
}

void RunControls::update_buttons()
{
    btn_start->setEnabled(state_ == State::Stopped);
    btn_pause->setEnabled(state_ != State::Stopped);
    btn_pause->setText(QString::fromUtf8(state_ == State::Paused ? "▶  Продолжить" : "❚❚  Пауза"));
    btn_stop->setEnabled(state_ != State::Stopped);
    // В быстром режиме движок скорости не нужен (считаем сколько успеем), а статистика — всегда по всем
    speed->setEnabled(!fast());
    ensemble_box->setEnabled(!fast());
}

void RunControls::frame()
{
    QElapsedTimer clock;
    clock.start();
    emit tick(fast(), settings::SLOW_FACTORS[speed->value() - 1]);
    if (state_ == State::Running) {
        int spent = static_cast<int>(clock.elapsed());
        timer.start(std::max(settings::MIN_IDLE_MS, settings::FRAME_MS - spent));
    }
}
