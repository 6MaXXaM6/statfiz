// Страница "Теория по теме": слева список разделов, справа текст раздела и живой пример
// (движки T и масс, кривые распределений, набор статистики). Внизу — "Назад / Далее".

#pragma once

#include <QButtonGroup>
#include <QPushButton>
#include <QStackedWidget>
#include <QWidget>
#include <functional>
#include <vector>

class TheoryPage : public QWidget {
public:
    TheoryPage(std::function<void()> go_home, std::function<void()> go_demo);

    void show_section(int index);
    int section_count() const { return stack->count(); }

    QStackedWidget* stack;  // открыто для проверок (--layout-check, --screenshot)

private:
    std::vector<QPushButton*> nav_;
    QPushButton* back_;
    QPushButton* next_;
};
