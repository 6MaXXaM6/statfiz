// Страница "Авторы" (см. authors_page.h).

#include "pages/authors_page.h"

#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPainter>

#include "ui/icons.h"
#include "ui/style.h"
#include "ui/widgets.h"

static QJsonObject load_authors()
{
    QFile file(":/assets/authors.json");
    file.open(QIODevice::ReadOnly);
    return QJsonDocument::fromJson(file.readAll()).object();
}

// Серый силуэт — пока нет фотографии.
static QPixmap photo_placeholder(int size)
{
    QPixmap pix(size * 8 / 10, size);
    pix.fill(QColor("#e4e8f0"));
    QPainter p(&pix);
    p.setRenderHint(QPainter::Antialiasing);
    p.setPen(Qt::NoPen);
    p.setBrush(QColor("#b0bac9"));
    double w = pix.width();
    p.drawEllipse(QRectF(w * 0.3, size * 0.15, w * 0.4, w * 0.4));
    p.drawEllipse(QRectF(w * 0.1, size * 0.6, w * 0.8, size * 0.6));
    return pix;
}

static QWidget* person_card(const QJsonObject& person, int size)
{
    auto* photo = new QLabel;
    photo->setAlignment(Qt::AlignCenter);
    QPixmap pix = load_pixmap(person["photo"].toString(), size, size);
    photo->setPixmap(pix.isNull() ? photo_placeholder(size) : pix);
    QLabel* name = label(person["name"].toString(), 1.2, true);
    center(name);
    name->setWordWrap(true);
    auto* layout = vbox({photo, name});
    if (!person["info"].toString().isEmpty()) {
        QLabel* info = label(person["info"].toString());
        center(info);
        info->setWordWrap(true);
        layout->addWidget(info);
    }
    auto* card = new QWidget;
    card->setLayout(layout);
    return card;
}

AuthorsPage::AuthorsPage(std::function<void()> go_home)
{
    QJsonObject data = load_authors();
    auto* layout = vbox({header_bar(QString::fromUtf8("Авторы"), go_home), Item::spring(1)},
                        style::px(0.5), QMargins(0, 0, 0, style::px(1)));

    auto* cards = hbox({Item::spring()});
    for (const QJsonValue& person : data["authors"].toArray())
        cards->addWidget(person_card(person.toObject(), style::px(11)));
    cards->addStretch(1);
    layout->addLayout(cards);

    QJsonObject sup = data["supervisor"].toObject();
    if (!sup.isEmpty()) {
        QString info = sup["info"].toString().isEmpty() ? "" : ", " + sup["info"].toString();
        QLabel* w = label(QString::fromUtf8("Преподаватель: <b>%1</b>%2").arg(sup["name"].toString(), info), 1.2);
        center(w);
        w->setWordWrap(true);
        layout->addWidget(w);
    }
    for (const QJsonValue& note : data["notes"].toArray()) {
        QLabel* w = label(note.toString());
        center(w);
        w->setWordWrap(true);
        set_color(w, "#555555");
        layout->addWidget(w);
    }
    layout->addStretch(2);
    setLayout(layout);
}
