// Общие элементы интерфейса (см. widgets.h).

#include "ui/widgets.h"

#include <QSignalBlocker>
#include <algorithm>

#include "settings.h"
#include "ui/style.h"

QLabel* label(const QString& text, double size, bool bold)
{
    auto* w = new QLabel(text);
    if (size > 0)
        w->setFont(style::font(size, bold));
    return w;
}

void center(QLabel* w)
{
    w->setAlignment(Qt::AlignCenter);
}

void set_color(QLabel* w, const char* color)
{
    w->setStyleSheet(QString("color: %1;").arg(color));
}

void make_shrinkable(QLabel* w)
{
    w->setWordWrap(true);
    w->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Preferred);
}

QPushButton* button(const QString& text, std::function<void()> on_click, bool checkable)
{
    auto* b = new QPushButton(text);
    b->setFocusPolicy(Qt::NoFocus);
    b->setCheckable(checkable);
    if (on_click)
        QObject::connect(b, &QPushButton::clicked, b, [on_click] { on_click(); });
    return b;
}

void add_items(QBoxLayout* layout, const std::vector<Item>& items)
{
    for (const Item& it : items) {
        if (it.widget)
            layout->addWidget(it.widget, it.stretch);
        else if (it.layout)
            layout->addLayout(it.layout, it.stretch);
        else
            layout->addStretch(it.stretch ? it.stretch : 1);
    }
}

static void setup(QBoxLayout* layout, std::initializer_list<Item> items, int spacing, QMargins margins)
{
    layout->setContentsMargins(margins);
    if (spacing >= 0)
        layout->setSpacing(spacing);
    add_items(layout, items);
}

QHBoxLayout* hbox(std::initializer_list<Item> items, int spacing, QMargins margins)
{
    auto* layout = new QHBoxLayout;
    setup(layout, items, spacing, margins);
    return layout;
}

QVBoxLayout* vbox(std::initializer_list<Item> items, int spacing, QMargins margins)
{
    auto* layout = new QVBoxLayout;
    setup(layout, items, spacing, margins);
    return layout;
}

QFrame* card(std::initializer_list<Item> items, const QString& title, int spacing)
{
    auto* frame = new QFrame;
    frame->setObjectName("card");
    int m = style::px(settings::CARD_MARGIN);
    auto* layout = vbox({}, spacing, QMargins(m, m, m, m));
    if (!title.isEmpty())
        layout->addWidget(section_title(title));
    add_items(layout, items);
    frame->setLayout(layout);
    return frame;
}

QLabel* section_title(const QString& text)
{
    QLabel* w = label(text, 1.0);
    w->setObjectName("section");
    return w;
}

QToolButton* overlay_button(QWidget* parent, const QString& text, const QString& tooltip,
                            std::function<void()> on_click)
{
    auto* b = new QToolButton(parent);
    b->setObjectName("overlay");
    b->setText(text);
    b->setToolTip(tooltip);
    b->setFocusPolicy(Qt::NoFocus);
    QObject::connect(b, &QToolButton::clicked, b, [on_click] { on_click(); });
    return b;
}

void place_overlay(QToolButton* b, QWidget* parent)
{
    int m = style::px(0.3);
    b->adjustSize();
    b->move(parent->width() - b->width() - m, m);
    b->raise();
}

QString html_color(const QString& text, const char* color, bool bold)
{
    return QString("<span style=\"color:%1; font-weight:%2\">%3</span>")
        .arg(color, bold ? "bold" : "normal", text);
}

QWidget* header_bar(const QString& title, std::function<void()> back, const std::vector<Action>& extra)
{
    auto* bar = new QWidget;
    QLabel* caption = label(title, 1.25, true);
    center(caption);
    make_shrinkable(caption);
    int m = style::px(0.3);
    auto* row = hbox({button(QString::fromUtf8("◀  На главную"), back), {caption, 1}},
                     -1, QMargins(m, style::px(0.2), m, style::px(0.2)));
    for (const auto& [text, callback] : extra)
        row->addWidget(button(text, callback));
    bar->setLayout(row);
    return bar;
}

// ----------------------------------------------------------------------
// ParamControl
// ----------------------------------------------------------------------

ParamControl::ParamControl(const QString& title, int minimum, int maximum, int initial,
                           bool show_number, bool show_slider)
    : spin(new QSpinBox), slider(new QSlider(Qt::Horizontal))
{
    spin->setMinimumWidth(style::px(3.6));
    spin->setAlignment(Qt::AlignRight);
    spin->setKeyboardTracking(false);  // число применяется после Enter
    spin->setVisible(show_number);
    slider->setVisible(show_slider);   // без движка — компактно: подпись и число в одну строку
    set_range(minimum, maximum);
    set_value_silently(initial);

    // Движок и поле показывают одно и то же; изменение любого запускает задержку.
    connect(slider, &QSlider::valueChanged, this, [this](int v) {
        QSignalBlocker block(spin);
        spin->setValue(v);
        delay_.start();
    });
    connect(spin, QOverload<int>::of(&QSpinBox::valueChanged), this, [this](int v) {
        QSignalBlocker block(slider);
        slider->setValue(v);
        delay_.start();
    });

    delay_.setSingleShot(true);
    delay_.setInterval(250);
    connect(&delay_, &QTimer::timeout, this, [this] { emit changed(value()); });

    setLayout(vbox({hbox({{label(title), 1}, spin}), slider}, 0,
                   QMargins(0, style::px(0.1), 0, style::px(0.1))));
}

void ParamControl::set_range(int minimum, int maximum)
{
    QSignalBlocker a(slider), b(spin);
    slider->setRange(minimum, maximum);
    spin->setRange(minimum, maximum);
}

void ParamControl::set_value_silently(int value)
{
    QSignalBlocker a(slider), b(spin);
    slider->setValue(value);
    spin->setValue(value);
}

// ----------------------------------------------------------------------
// Choice
// ----------------------------------------------------------------------

Choice::Choice(const QString& title, const std::vector<std::pair<QString, QString>>& options)
{
    auto* group = new QButtonGroup(this);
    group->setExclusive(true);
    auto* row = hbox({}, style::px(0.2));
    for (const auto& [key, text] : options) {
        QString k = key;
        QPushButton* b = button(text, [this, k] { emit changed(k); }, true);
        group->addButton(b);
        buttons[key] = b;
        row->addWidget(b);
    }
    auto* layout = vbox({}, style::px(0.1), QMargins(0, style::px(0.15), 0, style::px(0.15)));
    if (!title.isEmpty())
        layout->addWidget(label(title));
    layout->addLayout(row);
    setLayout(layout);
    set_value(options.front().first);
}

QString Choice::value() const
{
    for (const auto& [key, b] : buttons)
        if (b->isChecked())
            return key;
    return {};
}

void Choice::set_value(const QString& key)
{
    buttons.at(key)->setChecked(true);
}

void Choice::set_enabled_options(const std::vector<QString>& keys)
{
    for (const auto& [key, b] : buttons)
        b->setEnabled(std::find(keys.begin(), keys.end(), key) != keys.end());
}
