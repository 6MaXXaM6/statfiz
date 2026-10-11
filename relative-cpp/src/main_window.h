// Главное окно: стопка страниц (титул, презентация, теория, авторы); F11 / Esc — полный экран.

#pragma once

#include <QMainWindow>
#include <QStackedWidget>

#include "pages/authors_page.h"
#include "pages/demo/demo_page.h"
#include "pages/theory/theory_page.h"
#include "pages/title_page.h"

class MainWindow : public QMainWindow {
public:
    MainWindow();

    void show_title();
    void show_demo();
    void show_theory();
    void show_authors();

    DemoPage* demo;
    TheoryPage* theory;

protected:
    void keyPressEvent(QKeyEvent* event) override;

private:
    QStackedWidget* stack_;
    TitlePage* title_;
    AuthorsPage* authors_;
};
