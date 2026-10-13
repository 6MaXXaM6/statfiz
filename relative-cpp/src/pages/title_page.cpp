// Титульная страница (см. title_page.h).

#include "pages/title_page.h"

#include <QPainter>

#include "settings.h"
#include "ui/icons.h"
#include "ui/style.h"
#include "ui/widgets.h"

static const char* TITLE = "Относительная скорость движения\nмолекул идеального газа";
static const char* SUBTITLE = "Компьютерная презентация по статистической физике";

// Пунктирный круг с подписью — если файла эмблемы нет.
static QPixmap emblem_placeholder(int size)
{
    QPixmap pix(size, size);
    pix.fill(Qt::transparent);
    QPainter p(&pix);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(QPen(QColor("#8a9bb8"), 4, Qt::DashLine));
    p.drawEllipse(4, 4, size - 8, size - 8);
    p.setFont(style::font(0.8));
    p.drawText(pix.rect(), Qt::AlignCenter, QString::fromUtf8("эмблема\nфакультета"));
    return pix;
}

static QLabel* emblem(const QString& filename)
{
    int size = style::px(settings::EMBLEM_SIZE);
    auto* w = new QLabel;
    w->setAlignment(Qt::AlignCenter);
    QPixmap pix = load_pixmap(filename, size, size);
    w->setPixmap(pix.isNull() ? emblem_placeholder(size) : pix);
    return w;
}

TitlePage::TitlePage(std::function<void()> on_demo, std::function<void()> on_theory,
                     std::function<void()> on_authors, std::function<void()> on_exit)
{
    QLabel* title = label(QString::fromUtf8(TITLE), settings::TITLE_FONT, true);
    center(title);
    set_color(title, style::DARK);
    make_shrinkable(title);
    title->setMinimumHeight(style::px(6));
    QLabel* subtitle = label(QString::fromUtf8(SUBTITLE), settings::SUBTITLE_FONT);
    center(subtitle);
    subtitle->setWordWrap(true);

    auto* buttons = vbox({}, style::px(0.8));
    const std::vector<Action> actions = {
        {QString::fromUtf8("Презентация"), on_demo},
        {QString::fromUtf8("Теория по теме"), on_theory},
        {QString::fromUtf8("Авторы"), on_authors},
        {QString::fromUtf8("Выход"), on_exit},
    };
    for (const auto& [text, callback] : actions) {
        QPushButton* b = button(text, callback);
        b->setObjectName("big");
        b->setMinimumWidth(style::px(16));
        buttons->addWidget(b, 0, Qt::AlignHCenter);
    }
    int m = style::px(2);
    setLayout(vbox({hbox({emblem("emblem_left.png"), {title, 1}, emblem("emblem_right.png")}),
                    subtitle, Item::spring(1), buttons, Item::spring(2)},
                   -1, QMargins(m, style::px(1.5), m, style::px(1.5))));
}
