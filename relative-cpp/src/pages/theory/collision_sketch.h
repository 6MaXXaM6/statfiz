// Схема упругого удара двух дисков для раздела "Модель газа":
// линия центров n, скорости до удара (сплошные) и после (пунктир).
// Скорости после удара считаются по той же формуле, что в Gas::collide.

#pragma once

#include <QWidget>

class CollisionSketch : public QWidget {
public:
    CollisionSketch();

protected:
    void paintEvent(QPaintEvent*) override;
};
