// Рисованные значки и загрузка встроенных картинок.

#include "ui/icons.h"

#include <QPainter>
#include <algorithm>

#include "ui/style.h"

// Четыре стрелки по углам: наружу ("развернуть") или внутрь ("свернуть").
static QPixmap corner_arrows(int size, const QColor& color, bool outward)
{
    QPixmap pix(size, size);
    pix.fill(Qt::transparent);
    QPainter p(&pix);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(QPen(color, std::max(2.0, size / 11.0), Qt::SolidLine, Qt::RoundCap, Qt::RoundJoin));
    double half = size / 2.0;
    double m = size * 0.14;      // отступ от края
    double inner = size * 0.40;  // где кончается стрелка ближе к центру
    double head = size * 0.22;   // длина "уголка" наконечника
    for (int sx : {-1, 1}) {
        for (int sy : {-1, 1}) {
            QPointF corner(half + sx * (half - m), half + sy * (half - m));
            QPointF inner_end(half + sx * (half - inner), half + sy * (half - inner));
            p.drawLine(corner, inner_end);
            QPointF tip = outward ? corner : inner_end;
            int d = outward ? -1 : 1;  // уголок смотрит в сторону острия
            p.drawLine(tip, QPointF(tip.x() + d * sx * head, tip.y()));
            p.drawLine(tip, QPointF(tip.x(), tip.y() + d * sy * head));
        }
    }
    return pix;
}

QIcon zoom_icon(int size)
{
    QIcon icon;
    icon.addPixmap(corner_arrows(size, QColor(style::DARK), true), QIcon::Normal, QIcon::Off);
    icon.addPixmap(corner_arrows(size, Qt::white, false), QIcon::Normal, QIcon::On);
    return icon;
}

QPixmap load_pixmap(const QString& filename, int width, int height)
{
    if (filename.isEmpty())
        return {};
    QPixmap pix(":/assets/" + filename);
    if (pix.isNull())
        return {};
    return pix.scaled(width, height, Qt::KeepAspectRatio, Qt::SmoothTransformation);
}
