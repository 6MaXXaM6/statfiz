// Общий стиль: размеры шрифтов и линий зависят от разрешения экрана,
// чтобы презентация одинаково читалась на ноутбуке и на проекторе.

#pragma once

#include <QApplication>
#include <QFont>
#include <QPalette>
#include <QString>

namespace style {

// Базовый размер шрифта в пикселях. Пересчитывается в init_style().
extern int BASE;

// Цвета (яркие и контрастные — для проектора)
inline const char* MOL1 = "#d7191c";      // молекула 1 и её скорость — красный
inline const char* MOL2 = "#1f4fd1";      // молекула 2 и её скорость — синий
inline const char* REL = "#000000";       // относительная скорость — чёрный
inline const char* GAS_A = "#6b7a90";     // молекулы газа A — серо-синий
inline const char* GAS_B = "#1a9641";     // молекулы газа B — зелёный
inline const char* THEORY = "#d7191c";    // теоретическая кривая
inline const char* HILITE = "#ff8c00";    // подсветка текущего значения — оранжевый
inline const char* BAR = "#b8c7e0";       // столбики гистограммы
inline const char* BAR_EDGE = "#7f93b5";  // края столбиков
inline const char* PROJ = "#8e24aa";      // проекция — фиолетовый
inline const char* PAGE_BG = "#eef1f6";   // фон страниц (карточки на нём — белые)
inline const char* DARK = "#1c3f7a";      // тёмно-синий: заголовки, значки

int px(double k = 1.0);                   // размер в пикселях, пропорциональный базовому шрифту
QFont font(double k = 1.0, bool bold = false);
QPalette light_palette();
void init_style(QApplication& app);       // подобрать BASE под экран и настроить внешний вид

QString sup(int n);                       // число верхним индексом: -3 -> "⁻³"
QString fmt(double x, int digits = 0);    // число с разделением разрядов: 134000 -> "134 000"

}  // namespace style
