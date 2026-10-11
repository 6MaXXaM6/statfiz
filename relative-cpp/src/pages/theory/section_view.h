// Один раздел теории: текст (HTML из assets/theory) слева и живой пример справа.

#pragma once

#include <QWidget>

class SectionView : public QWidget {
public:
    // demo — живой пример (или nullptr: тогда текст на всю ширину)
    SectionView(const QString& html_file, QWidget* demo);
};
