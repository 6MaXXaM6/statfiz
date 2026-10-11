// Кнопки Старт / Пауза / Стоп, режимы "медленно / быстро", "статистика по всем молекулам"
// и таймер кадров.

#pragma once

#include <QCheckBox>
#include <QPushButton>
#include <QTimer>
#include <QWidget>

#include "ui/widgets.h"

// Управляет ходом расчёта.
//   started — нажата "Старт" (нужно начать новый опыт);
//   mode_changed(fast) — переключён режим "медленно / быстро";
//   ensemble_changed(on) — включена/выключена статистика по всем молекулам;
//   tick(fast, factor) — пора сделать очередной кадр: в быстром режиме считать сколько
//   успеем, в медленном — смоделировать factor шагов dt.
class RunControls : public QWidget {
    Q_OBJECT
public:
    enum class State { Stopped, Running, Paused };

    RunControls();

    bool fast() const { return mode->value() == "fast"; }
    bool ensemble() const { return ensemble_box->isChecked(); }
    State state() const { return state_; }
    void start();
    void toggle_pause();
    void pause();
    void stop();
    void frame();  // один кадр (его же вызывает таймер)

    QPushButton* btn_start;
    QPushButton* btn_pause;
    QPushButton* btn_stop;
    Choice* mode;
    QCheckBox* ensemble_box;  // "по всем молекулам того же сорта"
    ParamControl* speed;      // движок "Скорость" медленного режима (положение 1..SLOW_COUNT)
    QTimer timer;

signals:
    void started();
    void tick(bool fast, double factor);
    void mode_changed(bool fast);
    void ensemble_changed(bool on);

private:
    void set_state(State state);
    void update_buttons();

    State state_ = State::Stopped;
};
