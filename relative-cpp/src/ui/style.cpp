// Размеры, палитра и таблица стилей приложения.

#include "ui/style.h"

#include "settings.h"

#include <QScreen>
#include <QStyleFactory>
#include <algorithm>
#include <cmath>


namespace style {

int BASE = 20;

int px(double k)
{
    return std::max(1, static_cast<int>(std::lround(BASE * k)));
}

QFont font(double k, bool bold)
{
    QFont f;
    f.setPixelSize(px(k));
    f.setBold(bold);
    return f;
}

// Светлая палитра для всех виджетов: тёмная тема системы не должна "протекать".
QPalette light_palette()
{
    const std::pair<QPalette::ColorRole, const char*> colors[] = {
        {QPalette::Window, PAGE_BG},           {QPalette::WindowText, "#111111"},
        {QPalette::Base, "#ffffff"},           {QPalette::AlternateBase, "#f3f5f9"},
        {QPalette::Text, "#111111"},           {QPalette::PlaceholderText, "#b8c0cc"},
        {QPalette::Button, "#eef2f8"},         {QPalette::ButtonText, "#111111"},
        {QPalette::Highlight, "#2d5fb3"},      {QPalette::HighlightedText, "#ffffff"},
        {QPalette::ToolTipBase, "#ffffe8"},    {QPalette::ToolTipText, "#111111"},
        {QPalette::Light, "#ffffff"},          {QPalette::Midlight, "#e4e8f0"},
        {QPalette::Mid, "#b0bac9"},            {QPalette::Dark, "#8a9bb8"},
        {QPalette::Shadow, "#5a6a8a"},
    };
    QPalette palette;
    for (const auto& [role, color] : colors) {
        palette.setColor(QPalette::All, role, QColor(color));
    }
    for (auto role : {QPalette::WindowText, QPalette::Text, QPalette::ButtonText})
        palette.setColor(QPalette::Disabled, role, QColor("#999999"));
    return palette;
}

void init_style(QApplication& app)
{
    QRect screen = app.primaryScreen()->availableGeometry();
    int width = screen.width(), height = screen.height();
    // Для снимков экрана (--screenshot) размер "экрана" можно задать вручную.
    QString forced = qEnvironmentVariable("RELATIVE_SCREEN");
    if (!forced.isEmpty()) {
        QStringList wh = forced.split('x');
        width = wh.value(0).toInt();
        height = wh.value(1).toInt();
    }
    // Размер обычного текста от экрана (правило и множитель — в settings.h):
    // LINES_PER_SCREEN строк по высоте, COLUMNS_PER_SCREEN — по ширине, всё умножено на FONT_SCALE.
    using namespace settings;
    double fit = std::min(height / LINES_PER_SCREEN, width / COLUMNS_PER_SCREEN) * FONT_SCALE;
    BASE = std::clamp(static_cast<int>(std::lround(fit)), FONT_MIN, FONT_MAX);

    QFont f = app.font();
    f.setPixelSize(BASE);
    app.setFont(f);
    app.setStyle(QStyleFactory::create("Fusion"));
    app.setPalette(light_palette());

    app.setStyleSheet(QString(R"(
        QMainWindow { background: %1; }
        QWidget { color: #111111; }
        QFrame#card { background: #ffffff; border: 1px solid #d3dae6; border-radius: %2px; }
        QLabel#section { color: #1c3f7a; font-weight: bold; }
        QPushButton {
            background: #eef2f8; border: 2px solid #8a9bb8; border-radius: %3px;
            padding: %4px %5px;
        }
        QPushButton:hover { background: #dde6f5; }
        QPushButton:checked { background: #2d5fb3; color: white; border-color: #1c3f7a; }
        QPushButton:disabled { color: #999999; border-color: #cccccc; }
        QToolButton#overlay {
            background: rgba(255, 255, 255, 220); border: 2px solid #8a9bb8; border-radius: %3px;
            font-size: %6px; font-weight: bold; padding: 0px %4px;
        }
        QToolButton#overlay:hover { background: #dde6f5; }
        QPushButton#big {
            font-size: %7px; font-weight: bold; padding: %8px;
            border-width: 3px; border-radius: %9px;
        }
        QSpinBox, QComboBox {
            border: 2px solid #8a9bb8; border-radius: %3px; padding: 2px; background: #ffffff; color: #111111;
        }
        QSlider::groove:horizontal { height: %10px; background: #d0d8e8; border-radius: %11px; }
        QSlider::handle:horizontal {
            background: #2d5fb3; width: %12px; margin: -%13px 0; border-radius: %14px;
        }
        QTextBrowser { border: none; }
    )")
        .arg(PAGE_BG).arg(px(0.4)).arg(px(0.3)).arg(px(0.25)).arg(px(0.5))
        .arg(px(0.9)).arg(px(settings::MENU_BUTTON_FONT)).arg(px(0.6)).arg(px(0.5))
        .arg(px(0.4)).arg(px(0.2)).arg(px(1.0)).arg(px(0.35)).arg(px(0.5)));
}

QString sup(int n)
{
    const QString digits = QString::fromUtf8("⁰¹²³⁴⁵⁶⁷⁸⁹");
    QString s = QString::number(n), out;
    for (QChar c : s)
        out += c == '-' ? QString::fromUtf8("⁻") : QString(digits[c.digitValue()]);
    return out;
}

QString fmt(double x, int digits)
{
    if (std::isnan(x))
        return QString::fromUtf8("—");
    QString s = QString::number(std::fabs(x), 'f', digits);
    // Разделяем разряды целой части пробелами по три цифры.
    int point = s.indexOf('.');
    for (int k = (point < 0 ? s.size() : point) - 3; k > 0; k -= 3)
        s.insert(k, ' ');
    // Минус — типографский, и только если число после округления не ноль.
    bool negative = x < 0 && s.contains(QRegExp("[1-9]"));
    return (negative ? QString::fromUtf8("−") : QString()) + s;
}

}  // namespace style
