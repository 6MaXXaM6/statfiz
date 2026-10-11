// Титульная страница: название, эмблемы факультетов и четыре кнопки.

#pragma once

#include <QWidget>
#include <functional>

class TitlePage : public QWidget {
public:
    TitlePage(std::function<void()> on_demo, std::function<void()> on_theory,
              std::function<void()> on_authors, std::function<void()> on_exit);
};
