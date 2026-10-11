// Общие элементы интерфейса: готовые подписи, кнопки, ряды/столбцы, карточки,
// параметр с движком (ParamControl) и ряд кнопок-переключателей (Choice).

#pragma once

#include <QBoxLayout>
#include <QButtonGroup>
#include <QFrame>
#include <QLabel>
#include <QPushButton>
#include <QSlider>
#include <QSpinBox>
#include <QTimer>
#include <QToolButton>
#include <functional>
#include <initializer_list>
#include <map>
#include <vector>

// ----------------------------------------------------------------------
// Фабрики: одна строчка вместо пяти одинаковых настроек у каждого виджета
// ----------------------------------------------------------------------

// Надпись. size — размер шрифта относительно базового (0 — как у родителя).
QLabel* label(const QString& text = "", double size = 0, bool bold = false);
void center(QLabel* w);                          // текст по центру
void set_color(QLabel* w, const char* color);    // цвет текста
// Длинная надпись может сжиматься и переноситься — окно не станет шире экрана.
void make_shrinkable(QLabel* w);

// Кнопка, которая не перехватывает фокус клавиатуры (чтобы работали F11/Esc).
QPushButton* button(const QString& text, std::function<void()> on_click = {}, bool checkable = false);

// Элемент ряда/столбца: виджет, вложенный layout или пустое растяжение, у каждого — свой stretch.
struct Item {
    Item(QWidget* w, int stretch = 0) : widget(w), stretch(stretch) {}
    Item(QLayout* l, int stretch = 0) : layout(l), stretch(stretch) {}
    static Item spring(int stretch = 1) { Item it(static_cast<QWidget*>(nullptr), stretch); return it; }

    QWidget* widget = nullptr;
    QLayout* layout = nullptr;
    int stretch = 0;
};

QHBoxLayout* hbox(std::initializer_list<Item> items, int spacing = -1, QMargins margins = {});
QVBoxLayout* vbox(std::initializer_list<Item> items, int spacing = -1, QMargins margins = {});
void add_items(QBoxLayout* layout, const std::vector<Item>& items);

// Белая карточка со скруглёнными углами; внутри — элементы столбиком.
QFrame* card(std::initializer_list<Item> items, const QString& title = "", int spacing = -1);
QLabel* section_title(const QString& text);

// Маленькая кнопка поверх виджета (например, графика); место задаёт place_overlay().
QToolButton* overlay_button(QWidget* parent, const QString& text, const QString& tooltip,
                            std::function<void()> on_click);
void place_overlay(QToolButton* b, QWidget* parent);  // в правый верхний угол (из resizeEvent)

QString html_color(const QString& text, const char* color, bool bold = true);

// Верхняя полоса страницы: кнопка "На главную", заголовок, доп. кнопки справа.
using Action = std::pair<QString, std::function<void()>>;
QWidget* header_bar(const QString& title, std::function<void()> back, const std::vector<Action>& extra = {});

// ----------------------------------------------------------------------
// Составные элементы
// ----------------------------------------------------------------------

// Параметр с "движком" и полем для точного ввода числа.
// Значение всегда в диапазоне [minimum, maximum]. Сигнал changed отправляется с небольшой
// задержкой после последнего изменения, чтобы не перезапускать модель на каждом шаге движка.
class ParamControl : public QWidget {
    Q_OBJECT
public:
    ParamControl(const QString& title, int minimum, int maximum, int initial,
                 bool show_number = true, bool show_slider = true);

    int value() const { return spin->value(); }
    void set_range(int minimum, int maximum);
    void set_value_silently(int value);

    QSpinBox* spin;
    QSlider* slider;

signals:
    void changed(int value);

private:
    QTimer delay_;
};

// Подпись и ряд кнопок, из которых нажата ровно одна. Ключ кнопки — строка.
class Choice : public QWidget {
    Q_OBJECT
public:
    Choice(const QString& title, const std::vector<std::pair<QString, QString>>& options);

    QString value() const;
    void set_value(const QString& key);
    void set_enabled_options(const std::vector<QString>& keys);

    std::map<QString, QPushButton*> buttons;

signals:
    void changed(const QString& key);
};
