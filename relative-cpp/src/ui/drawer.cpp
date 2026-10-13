// Выдвижная панель (см. drawer.h).

#include "ui/drawer.h"

#include <QEvent>
#include <QKeyEvent>
#include <QVBoxLayout>

#include "ui/style.h"

constexpr int SLIDE_MS = 180;  // сколько длится выезд панели

// Затемнение: полупрозрачный слой, щелчок по нему закрывает панель
class Shade : public QWidget {
public:
    Shade(QWidget* parent, Drawer* drawer) : QWidget(parent), drawer_(drawer)
    {
        setStyleSheet("background: rgba(20, 30, 50, 90);");
        setAttribute(Qt::WA_StyledBackground);
    }

protected:
    void mousePressEvent(QMouseEvent*) override { drawer_->close(); }

private:
    Drawer* drawer_;
};

Drawer::Drawer(QWidget* host, QWidget* content, double width)
    : QWidget(host), host_(host), slide_(this, "pos")
{
    shade_ = new Shade(host, this);
    shade_->hide();
    setObjectName("drawer");
    setFocusPolicy(Qt::StrongFocus);  // чтобы получать Esc
    setAttribute(Qt::WA_StyledBackground);
    setStyleSheet("QWidget#drawer { background: #ffffff; border-right: 2px solid #8a9bb8; }");
    int m = style::px(0.5);
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(m, m, m, m);
    layout->addWidget(content);
    setFixedWidth(style::px(width));
    hide();

    slide_.setDuration(SLIDE_MS);
    slide_.setEasingCurve(QEasingCurve::OutCubic);
    connect(&slide_, &QPropertyAnimation::finished, this, [this] {
        if (!open_) {
            hide();
            shade_->hide();
        }
    });
    host->installEventFilter(this);  // следим за размером страницы
}

void Drawer::set_top(int top)
{
    top_ = top;
    place();
}

void Drawer::place()
{
    int height = host_->height() - top_;
    resize(width(), height);
    shade_->setGeometry(0, top_, host_->width(), height);
    move(open_ ? 0 : -width(), top_);
}

void Drawer::open()
{
    if (open_)
        return;
    open_ = true;
    place();
    move(-width(), top_);
    shade_->show();
    shade_->raise();
    show();
    raise();
    setFocus();
    slide_.stop();
    slide_.setStartValue(pos());
    slide_.setEndValue(QPoint(0, top_));
    slide_.start();
}

void Drawer::close()
{
    if (!open_)
        return;
    open_ = false;
    slide_.stop();
    slide_.setStartValue(pos());
    slide_.setEndValue(QPoint(-width(), top_));
    slide_.start();
}

bool Drawer::eventFilter(QObject* watched, QEvent* event)
{
    if (watched == host_ && event->type() == QEvent::Resize)
        place();
    return QWidget::eventFilter(watched, event);
}

void Drawer::keyPressEvent(QKeyEvent* event)
{
    if (event->key() == Qt::Key_Escape)
        close();
    else
        QWidget::keyPressEvent(event);
}
