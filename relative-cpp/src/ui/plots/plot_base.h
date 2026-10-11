// Общая основа всех графиков презентации (вместо библиотеки pyqtgraph в Python-версии).
//
//   PlotBase   — график с осями: числа на делениях, подписи осей (HTML: индексы, степени),
//                диапазоны задаются явно и сами не меняются (ничего "не скачет").
//   CanvasBase — "холст" без осей с одинаковым масштабом по x и y
//                (сосуд с молекулами и векторная диаграмма).
//
// Наследник рисует свои данные в draw_data(), пользуясь map()/map_x()/map_y().

#pragma once

#include <QPainter>
#include <QWidget>
#include <vector>

constexpr double AXIS_WIDTH = 4.2;   // ширина левой оси (подпись + числа вроде "-1000"), в базовых шрифтах
constexpr double AXIS_HEIGHT = 2.6;  // высота нижней оси (числа + подпись)

// Перо для линий; width — в долях базового шрифта (линии толще на больших экранах).
QPen make_pen(const QColor& color, double width = 0.12, Qt::PenStyle line = Qt::SolidLine);

// Стрелка из from в to; head — длина наконечника в пикселях.
void draw_arrow(QPainter& p, QPointF from, QPointF to, double head, const QColor& color, double width = 0.22);

class PlotBase : public QWidget {
public:
    enum class Axis { Left, Bottom };

    explicit PlotBase(QWidget* parent = nullptr);

    void set_x_range(double low, double high);
    void set_y_range(double low, double high);
    void set_axis_label(Axis axis, const QString& html);
    void show_left_axis(bool show);

protected:
    void paintEvent(QPaintEvent*) override;
    virtual void draw_data(QPainter& p) = 0;

    QRectF data_rect() const;  // где на виджете область данных
    double map_x(double x) const;
    double map_y(double y) const;
    QPointF map(double x, double y) const { return {map_x(x), map_y(y)}; }

    double x_low_ = 0, x_high_ = 1, y_low_ = 0, y_high_ = 1;

private:
    void draw_axes(QPainter& p);
    void draw_label(QPainter& p, const QString& html, QPointF center, bool vertical);

    QString left_label_, bottom_label_;
    bool left_axis_ = true;
};

class CanvasBase : public QWidget {
public:
    explicit CanvasBase(QWidget* parent = nullptr);

    // Какой квадрат мира показывать (x и y от low до high); по краям — запас margin (доля).
    void set_world(double low_x, double high_x, double low_y, double high_y, double margin = 0.01);

protected:
    void paintEvent(QPaintEvent*) override;
    virtual void draw_world(QPainter& p) = 0;

    QPointF map(double x, double y) const;      // мир -> экран (y вверх)
    QPointF unmap(QPointF screen) const;        // экран -> мир (для щелчков мышью)
    double scale() const;                       // пикселей на единицу мира

private:
    double low_x_ = 0, high_x_ = 1, low_y_ = 0, high_y_ = 1;
};
