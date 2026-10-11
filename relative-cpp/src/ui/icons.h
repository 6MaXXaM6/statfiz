// Значки и картинки: значки нарисованы программой (чётко при любом масштабе),
// картинки (эмблемы, фото) встроены в программу через resources.qrc.

#pragma once

#include <QIcon>
#include <QPixmap>
#include <QString>

// Значок кнопки "на весь экран": обычное состояние — стрелки наружу (тёмные),
// нажатая кнопка — стрелки внутрь (белые, на синем фоне нажатой кнопки).
QIcon zoom_icon(int size);

// Картинка из папки assets, вписанная в width×height; пустая, если файла нет.
QPixmap load_pixmap(const QString& filename, int width, int height);
