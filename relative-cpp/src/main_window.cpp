// Главное окно (см. main_window.h).

#include "main_window.h"

#include <QKeyEvent>

MainWindow::MainWindow()
{
    setWindowTitle(QString::fromUtf8("Относительная скорость молекул"));
    stack_ = new QStackedWidget;
    setCentralWidget(stack_);

    title_ = new TitlePage([this] { show_demo(); }, [this] { show_theory(); },
                           [this] { show_authors(); }, [this] { close(); });
    demo = new DemoPage([this] { show_title(); }, [this] { show_theory(); });
    theory = new TheoryPage([this] { show_title(); }, [this] { show_demo(); });
    authors_ = new AuthorsPage([this] { show_title(); });
    for (QWidget* page : std::initializer_list<QWidget*>{title_, demo, theory, authors_})
        stack_->addWidget(page);
}

void MainWindow::show_title() { stack_->setCurrentWidget(title_); }
void MainWindow::show_demo() { stack_->setCurrentWidget(demo); }
void MainWindow::show_authors() { stack_->setCurrentWidget(authors_); }

void MainWindow::show_theory()
{
    demo->pause();
    stack_->setCurrentWidget(theory);
}

void MainWindow::keyPressEvent(QKeyEvent* event)
{
    if (event->key() == Qt::Key_F11) {
        if (isFullScreen())
            showMaximized();
        else
            showFullScreen();
    } else if (event->key() == Qt::Key_Escape && isFullScreen()) {
        showMaximized();
    } else {
        QMainWindow::keyPressEvent(event);
    }
}
