// Общий стиль: размеры шрифтов и линий зависят от разрешения экрана,
// чтобы презентация одинаково читалась на ноутбуке и на проекторе.

#pragma once

#include <QApplication>
#include <QFont>
#include <QPalette>
#include <QString>

#include "settings.h"

namespace style {

// Базовый размер шрифта в пикселях. Пересчитывается в init_style().
extern int BASE;

// Цвета — задаются в settings.h (здесь короткие имена для кода)
inline const char* MOL1 = settings::COLOR_MOL1;
inline const char* MOL2 = settings::COLOR_MOL2;
inline const char* REL = settings::COLOR_REL;
inline const char* GAS_A = settings::COLOR_GAS_A;
inline const char* GAS_B = settings::COLOR_GAS_B;
inline const char* THEORY = settings::COLOR_THEORY;
inline const char* HILITE = settings::COLOR_HILITE;
inline const char* BAR = settings::COLOR_BAR;
inline const char* BAR_EDGE = settings::COLOR_BAR_EDGE;
inline const char* PROJ = settings::COLOR_PROJ;
inline const char* PAGE_BG = settings::COLOR_PAGE;
inline const char* DARK = settings::COLOR_DARK;

int px(double k = 1.0);                   // размер в пикселях, пропорциональный базовому шрифту
QFont font(double k = 1.0, bool bold = false);
QPalette light_palette();
void init_style(QApplication& app);       // подобрать BASE под экран и настроить внешний вид

QString sup(int n);                       // число верхним индексом: -3 -> "⁻³"
QString fmt(double x, int digits = 0);    // число с разделением разрядов: 134000 -> "134 000"

}  // namespace style
