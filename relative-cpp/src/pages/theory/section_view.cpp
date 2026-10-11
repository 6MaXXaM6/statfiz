// Раздел теории (см. section_view.h).

#include "pages/theory/section_view.h"

#include <QFile>
#include <QTextBrowser>

#include "ui/style.h"
#include "ui/widgets.h"

SectionView::SectionView(const QString& html_file, QWidget* demo)
{
    auto* text = new QTextBrowser;
    text->setOpenExternalLinks(true);
    text->document()->setDefaultFont(style::font(1.0));
    text->document()->setDocumentMargin(style::px(0.8));
    // Оформление формул и заголовков — одно на все разделы
    text->document()->setDefaultStyleSheet(QString(
        "h2 { color: %1; }"
        ".f { font-size: %2px; }"               // формула отдельной строкой
        ".note { color: #555555; }"
        ".try { color: %3; }")                  // "Попробуйте: ..."
        .arg(style::DARK).arg(style::px(1.25)).arg(style::MOL2));
    QFile file(":/assets/theory/" + html_file);
    file.open(QIODevice::ReadOnly);
    text->setHtml(QString::fromUtf8(file.readAll()));

    auto* layout = hbox({{text, 1}}, style::px(0.5));
    if (demo)
        layout->addWidget(card({demo}), 1);
    setLayout(layout);
}
