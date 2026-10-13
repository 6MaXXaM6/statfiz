// Раздел теории (см. section_view.h).

#include "pages/theory/section_view.h"

#include <QFile>
#include <QTextBrowser>

#include "settings.h"
#include "ui/style.h"
#include "ui/widgets.h"

SectionView::SectionView(const QString& html_file, QWidget* demo)
{
    auto* text = new QTextBrowser;
    text->setOpenExternalLinks(true);
    text->document()->setDefaultFont(style::font(settings::THEORY_TEXT_FONT));
    text->document()->setDocumentMargin(style::px(0.8));
    // Оформление формул и заголовков — одно на все разделы
    text->document()->setDefaultStyleSheet(QString(
        "h2 { color: %1; }"
        ".f { font-size: %2px; }"               // формула отдельной строкой
        ".note { color: #555555; }"
        ".try { color: %3; }")                  // "Попробуйте: ..."
        .arg(style::DARK).arg(style::px(settings::THEORY_FORMULA_FONT)).arg(style::MOL2));
    QFile file(":/assets/theory/" + html_file);
    file.open(QIODevice::ReadOnly);
    text->setHtml(QString::fromUtf8(file.readAll()));

    auto* layout = hbox({{text, 1}}, style::px(0.5));
    if (demo)
        layout->addWidget(card({demo}), 1);
    setLayout(layout);
}
