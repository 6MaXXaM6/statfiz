// Правая колонка: параметры газа. Настройки смеси видны только в режиме "Смесь".

#pragma once

#include <QCheckBox>
#include <QWidget>

#include "model/experiment.h"
#include "ui/widgets.h"

class GasPanel : public QWidget {
    Q_OBJECT
public:
    explicit GasPanel(const Experiment& exp);

    GasParams params() const;              // что сейчас выбрано в панели
    void sync_with(const Experiment& exp); // показать настройки смеси и доступные пары

    // Элементы панели (открыты для проверок --layout-check)
    Choice* gas_mode;
    ParamControl* temperature;
    ParamControl* n_total;
    ParamControl* mass_a;
    ParamControl* mass_b;
    ParamControl* n_b;
    Choice* pair;
    // Выбор опыта; страница показывает их под кнопками "Старт / Пауза" (не в этой панели)
    Choice* start;           // начальные скорости: Максвелл / все одинаковые
    QCheckBox* collisions;   // сталкиваются ли молекулы

signals:
    void gas_changed();
    void pair_chosen(const QString& pair_type);
    void temperature_changed(int temperature);
};
