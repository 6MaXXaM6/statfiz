// Страница теории (см. theory_page.h). Список разделов — в таблице SECTIONS.

#include "pages/theory/theory_page.h"

#include "pages/theory/collision_sketch.h"
#include "pages/theory/curve_demo.h"
#include "pages/theory/sampling_demo.h"
#include "pages/theory/section_view.h"
#include "settings.h"
#include "ui/style.h"
#include "ui/widgets.h"

// Раздел: название в списке, файл с текстом и какой живой пример показать рядом
struct Section {
    const char* title;
    const char* file;
    std::function<QWidget*()> make_demo;  // пусто — без примера
};

static std::vector<Section> sections()
{
    using V = CurveDemo::Variant;
    auto curve = [](V v) { return [v]() -> QWidget* { return new CurveDemo(v); }; };
    return {
        {"1. Модель газа", "01_model.html", [] { return new CollisionSketch; }},
        {"2. Проекция скорости", "02_projection.html", curve(V::Projection)},
        {"3. Модуль скорости", "03_modulus.html", curve(V::Modulus)},
        {"4. Относительная скорость", "04_relative.html", curve(V::Relative)},
        {"5. Кинетическая энергия", "05_energy.html", curve(V::Energy)},
        {"6. Смесь газов", "06_mixture.html", curve(V::Mixture)},
        {"7. Как устроен опыт", "07_experiment.html", [] { return new SamplingDemo; }},
    };
}

TheoryPage::TheoryPage(std::function<void()> go_home, std::function<void()> go_demo)
{
    stack = new QStackedWidget;

    // Список разделов — в выдвижной панели
    auto* nav = vbox({}, style::px(0.3));
    nav->addWidget(section_title(QString::fromUtf8("Разделы")));
    auto* group = new QButtonGroup(this);
    for (const Section& s : sections()) {
        int index = stack->count();
        stack->addWidget(new SectionView(s.file, s.make_demo ? s.make_demo() : nullptr));
        QPushButton* b = button(QString::fromUtf8(s.title), [this, index] {
            show_section(index);
            drawer->close();
        }, true);
        b->setStyleSheet("text-align: left; padding-left: 0.5em;");
        group->addButton(b);
        nav->addWidget(b);
        nav_.push_back(b);
    }
    nav->addStretch(1);
    auto* nav_widget = new QWidget;
    nav_widget->setLayout(nav);

    // Внизу: "☰ Разделы", "◀ Назад", название текущего раздела, "Далее ▶"
    QPushButton* menu = button(QString::fromUtf8("☰  Разделы"), [this] { drawer->toggle(); });
    back_ = button(QString::fromUtf8("◀ Назад"), [this] { show_section(stack->currentIndex() - 1); });
    next_ = button(QString::fromUtf8("Далее ▶"), [this] { show_section(stack->currentIndex() + 1); });
    caption_ = label("", 1.0, true);
    center(caption_);
    make_shrinkable(caption_);

    header_ = header_bar(QString::fromUtf8("Теория по теме"), go_home, {{QString::fromUtf8("Презентация ▶"), go_demo}});
    int m = style::px(0.4);
    setLayout(vbox({header_,
                    {vbox({{stack, 1}, hbox({menu, back_, {caption_, 1}, next_}, style::px(0.4))},
                          m, QMargins(m, 0, m, m)), 1}},
                   0));
    drawer = new Drawer(this, nav_widget, settings::DRAWER_WIDTH);  // создаётся последним — лежит поверх страницы
    show_section(0);
}

void TheoryPage::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    drawer->set_top(header_->height());  // панель выезжает под заголовком страницы
}

void TheoryPage::show_section(int index)
{
    if (index < 0 || index >= stack->count())
        return;
    stack->setCurrentIndex(index);
    nav_[index]->setChecked(true);
    back_->setEnabled(index > 0);
    next_->setEnabled(index + 1 < stack->count());
    // Название без номера в начале ("4. Относительная скорость" → "Относительная скорость")
    QString title = nav_[index]->text().section(". ", 1);
    caption_->setText(QString("%1 / %2 · %3").arg(index + 1).arg(stack->count()).arg(title));
}
