// Страница "Презентация". Собирает части и связывает их с экспериментом:
//
//     слева    — сосуд с молекулами и кнопки хода расчёта;
//     в центре — один или два графика (по умолчанию |v_отн|; "+ График" — второй),
//                под ними — число столбиков, память статистики и кнопка "на весь экран";
//     справа   — параметры газа и векторная диаграмма скоростей.

#pragma once

#include <QFrame>
#include <QLabel>
#include <QPushButton>
#include <QVBoxLayout>
#include <QWidget>
#include <functional>
#include <optional>
#include <vector>

#include "model/experiment.h"
#include "pages/demo/gas_panel.h"
#include "pages/demo/graph_panel.h"
#include "pages/demo/run_controls.h"
#include "ui/plots/box_view.h"
#include "ui/plots/vector_view.h"
#include "ui/widgets.h"

class DemoPage : public QWidget {
    Q_OBJECT
public:
    DemoPage(std::function<void()> go_home, std::function<void()> go_theory);

    void pause() { run->pause(); }
    void add_panel(Quantity q);
    void remove_panel(GraphPanel* panel);
    void toggle_graphs_zoom();

    // Открыты для проверок (--smoke-test, --layout-check)
    Experiment exp;
    RunControls* run;
    std::vector<GraphPanel*> panels;
    QPushButton* add_button;
    QPushButton* zoom_button;
    ParamControl* bins;
    ParamControl* memory;
    GasPanel* gas;

protected:
    void resizeEvent(QResizeEvent* event) override;
    void showEvent(QShowEvent* event) override;

private:
    void fit_box();
    std::function<void()> leaving(std::function<void()> go);

    void on_start();
    void on_tick(bool fast, double factor);
    void on_mode_changed(bool fast);
    void on_gas_changed();
    void on_box_clicked(double x, double y, int which);
    void changed(std::function<void()> action);
    void on_experiment_changed();

    std::vector<Quantity> comparisons() const;
    void configure_plots();
    void refresh();

    BoxView* box_;
    VectorView* vectors_;
    QLabel* legend_;
    QLabel* ratio_;
    QVBoxLayout* panels_box_;
    QFrame* middle_;
    QFrame* box_card_;
    QFrame* run_card_;
    QWidget* left_;
    QWidget* right_;
    QWidget* header_;
    int right_width_ = 0;
    bool autostarted_ = false;
    std::optional<Obj> projection_of_;
};
