// Страница "Теория по теме": текст раздела и живой пример (движки T и масс, кривые
// распределений, набор статистики) на всю ширину. Список разделов — в выдвижной панели
// слева (кнопка "☰ Разделы"); внизу — "Назад / Далее" и название раздела.

#pragma once

#include <QButtonGroup>
#include <QLabel>
#include <QPushButton>
#include <QStackedWidget>
#include <QWidget>
#include <functional>
#include <vector>

#include "ui/drawer.h"

class TheoryPage : public QWidget {
public:
    TheoryPage(std::function<void()> go_home, std::function<void()> go_demo);

    void show_section(int index);
    int section_count() const { return stack->count(); }

    QStackedWidget* stack;  // открыто для проверок (--layout-check, --screenshot)
    Drawer* drawer;         // выдвижной список разделов

protected:
    void resizeEvent(QResizeEvent* event) override;

private:
    std::vector<QPushButton*> nav_;
    QPushButton* back_;
    QPushButton* next_;
    QLabel* caption_;        // "3 / 7 · Относительная скорость"
    QWidget* header_;
};
