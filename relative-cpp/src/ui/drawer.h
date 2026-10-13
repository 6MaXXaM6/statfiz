// Выдвижная панель: выезжает слева поверх страницы, фон за ней затемняется.
// Закрывается щелчком по затемнению, клавишей Esc или вызовом close().
// Страница не перекладывается — панель лежит сверху, поэтому место под содержимое не уменьшается.

#pragma once

#include <QPropertyAnimation>
#include <QWidget>

class Drawer : public QWidget {
public:
    // host — над каким виджетом выезжать; top — отступ сверху (например, под заголовком страницы);
    // content — что показать в панели; width — ширина панели в базовых шрифтах.
    Drawer(QWidget* host, QWidget* content, double width);

    void open();
    void close();
    void toggle() { is_open() ? close() : open(); }
    bool is_open() const { return open_; }
    void set_top(int top);

protected:
    bool eventFilter(QObject* watched, QEvent* event) override;  // размер страницы изменился
    void keyPressEvent(QKeyEvent* event) override;                 // Esc закрывает панель

private:
    void place();  // размеры и положение под текущий размер host

    QWidget* host_;
    QWidget* shade_;   // затемнение остальной страницы (щелчок по нему закрывает панель)
    QPropertyAnimation slide_;
    int top_ = 0;
    bool open_ = false;
};
