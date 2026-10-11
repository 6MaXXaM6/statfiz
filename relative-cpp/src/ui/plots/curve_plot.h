// График теоретических кривых для страницы "Теория": несколько кривых, вертикальные
// метки характерных значений (с подписями) и легенда.

#pragma once

#include <QColor>
#include <QString>
#include <vector>

#include "ui/plots/plot_base.h"

class CurvePlot : public PlotBase {
public:
    struct Curve {
        std::vector<double> xs, ys;
        QColor color;
        bool dashed = false;
        QString label;   // в легенде (HTML); пустая — кривая без подписи
    };
    struct Marker {
        double x;
        QColor color;
        QString label;   // подпись у верхнего края (HTML)
    };

    explicit CurvePlot(QWidget* parent = nullptr);

    void set_curves(std::vector<Curve> curves);
    void set_markers(std::vector<Marker> markers);

protected:
    void draw_data(QPainter& p) override;

private:
    void draw_html(QPainter& p, const QString& html, QPointF top_left, const QColor& color);

    std::vector<Curve> curves_;
    std::vector<Marker> markers_;
};
