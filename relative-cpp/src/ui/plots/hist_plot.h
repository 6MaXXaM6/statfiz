// Распределение вероятностей: столбики эксперимента и кривая теории.

#pragma once

#include <QToolButton>
#include <optional>
#include <vector>

#include "model/stats.h"
#include "ui/plots/plot_base.h"

// Гистограмма + теория.
//
// sideways=true — распределение "лёжа на боку": значение величины по вертикали
// (так его можно поставить рядом с графиком во времени с общей осью),
// плотность вероятности — по горизонтали. sideways=false — обычный вид.
//
// Масштаб осей задаётся только в configure() по теории и во время опыта не меняется.
// Столбик выше края обрезается, а на краю рисуется треугольник-метка.
// Кнопка ↻ в углу отправляет сигнал rotate_clicked.
class HistPlot : public PlotBase {
    Q_OBJECT
public:
    explicit HistPlot(bool sideways = true, QWidget* parent = nullptr);

    bool sideways() const { return sideways_; }
    void set_orientation(bool sideways);

    // value_label — подпись оси значений с единицами; xs, pdf — теоретическая кривая;
    // peak — максимум плотности для масштаба оси; rescale — показывать плотность в 10ⁿ единиц
    // (для скоростей плотность ~10⁻³ с/м, для энергии этого не нужно).
    void configure(const QString& value_label, const std::vector<double>& xs, const std::vector<double>& pdf,
                   double peak, const QString& density_unit, bool rescale);

    // highlight — подсветить столбик, в который попало текущее значение.
    void update_view(const Histogram& hist, std::optional<double> current, bool highlight);

    QToolButton* rotate_button;

signals:
    void rotate_clicked();

protected:
    void draw_data(QPainter& p) override;
    void resizeEvent(QResizeEvent* event) override;

private:
    QPointF point(double value, double density) const;  // единственное место, где важна ориентация
    QRectF bar(double from, double to, double height) const;
    void apply_axes();

    bool sideways_ = true;
    QString value_label_, density_unit_;
    double low_ = 0, high_ = 1;
    int exponent_ = 0;     // плотность показывается в единицах 10^exponent
    double top_ = 1;       // верх оси плотности (в показанных единицах)
    std::vector<double> xs_, pdf_;

    // Последний кадр
    double hist_low_ = 0, hist_width_ = 1;
    std::vector<double> shown_;   // высоты столбиков (в показанных единицах)
    std::vector<double> flash_;   // яркость подсветки каждого столбика, 0..1
    std::optional<double> current_;
};
