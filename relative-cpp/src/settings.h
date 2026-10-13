// ===========================================================================
//  НАСТРОЙКИ ПРОГРАММЫ — всё, что удобно менять "на лету", в одном файле.
//  Поменяли число → `make run` (пересборка ~10 с) → смотрим. Не понравилось —
//  вернули как было (или `git checkout -- src/settings.h`). Шпаргалка: ПРАВКИ.md.
//
//  Размеры на экране заданы в "базовых шрифтах" (BASE — размер обычного текста
//  в пикселях, подбирается под экран): 2.0 значит "две высоты обычной буквы".
// ===========================================================================

#pragma once

namespace settings {

// --------------------------------------------------------------------------
// Шрифты и размеры на экране
// --------------------------------------------------------------------------
// Размер обычного текста: BASE = min(высота / LINES_PER_SCREEN, ширина / COLUMNS_PER_SCREEN) · FONT_SCALE.
// При 1024×768 и FONT_SCALE = 1.15 получается 18 px, при 1920×1080 — 30 px.
constexpr double FONT_SCALE = 1.15;      // крупнее всё сразу — увеличьте (1.0 — как было раньше)
constexpr double LINES_PER_SCREEN = 42;  // сколько строк текста помещается по высоте экрана
constexpr double COLUMNS_PER_SCREEN = 64;
constexpr int FONT_MIN = 12, FONT_MAX = 46;  // пределы BASE в пикселях

constexpr double MIDDLE_MIN = 24;        // наименьшая ширина колонки с графиками (в BASE)
constexpr double SIDE_STATS_WIDTH = 14;  // ширина подписей справа от графиков в режиме "на весь экран" (в BASE)
constexpr double CARD_MARGIN = 0.35;     // поля внутри белых карточек (в BASE); меньше — больше места графикам
constexpr double VECTOR_RADIUS = 2.6;    // масштаб векторной диаграммы: радиус в единицах наибольшей sqrt(kT/m)
constexpr double ARROW_LENGTH = 12.0;    // длина стрелки скорости в сосуде (нм) для скорости sqrt(kT/m)

// --------------------------------------------------------------------------
// Размеры шрифтов отдельных элементов (в BASE: 1.0 — обычный текст)
// --------------------------------------------------------------------------
constexpr double TITLE_FONT = 2.1;        // название на титульной странице
constexpr double SUBTITLE_FONT = 1.2;     // подзаголовок на титульной странице
constexpr double MENU_BUTTON_FONT = 1.5;  // большие кнопки титульной страницы ("Презентация", ...)
constexpr double EMBLEM_SIZE = 7.0;       // эмблемы факультетов на титуле (сторона, в BASE)
constexpr double HEADER_FONT = 1.25;      // заголовок вверху каждой страницы
constexpr double RUN_BUTTON_FONT = 1.0;   // кнопки "Старт / Пауза / Стоп"
constexpr double SELECTOR_FONT = 1.1;     // список величин над графиком (|vотн|, |v₁|, ...)
constexpr double VALUE_FONT = 1.2;        // текущее значение над графиком ("= 424 м/с")
constexpr double STATS_FONT = 0.85;       // среднее и дисперсия под графиком
constexpr double SIDE_STATS_FONT = 1.0;   // то же, когда графики на весь экран (подписи справа)
constexpr double RATIO_FONT = 1.0;        // строка сравнения "⟨|vотн|⟩ / ⟨|v₁|⟩ = 1.414"
constexpr double GAS_PANEL_FONT = 0.85;   // панель "Газ" справа
constexpr double LEGEND_FONT = 1.1;       // подпись под векторной диаграммой
constexpr double AXIS_NUMBERS_FONT = 0.8; // числа на осях графиков
constexpr double AXIS_LABEL_FONT = 0.85;  // подписи осей ("|vотн|, м/с")
constexpr double THEORY_TEXT_FONT = 1.0;  // текст теории
constexpr double THEORY_FORMULA_FONT = 1.25;  // формулы отдельной строкой в теории

// --------------------------------------------------------------------------
// Цвета (формат "#rrggbb"; подобрать: любой "color picker" в интернете)
// --------------------------------------------------------------------------
constexpr const char* COLOR_MOL1 = "#d7191c";     // молекула 1 и её скорость — красный
constexpr const char* COLOR_MOL2 = "#1f4fd1";     // молекула 2 и её скорость — синий
constexpr const char* COLOR_REL = "#000000";      // относительная скорость — чёрный
constexpr const char* COLOR_GAS_A = "#6b7a90";    // остальные молекулы газа A — серо-синий
constexpr const char* COLOR_GAS_B = "#1a9641";    // молекулы газа B — зелёный
constexpr const char* COLOR_THEORY = "#d7191c";   // теоретические кривые
constexpr const char* COLOR_HILITE = "#ff8c00";   // текущее значение — оранжевый
constexpr const char* COLOR_BAR = "#b8c7e0";      // столбики гистограммы
constexpr const char* COLOR_BAR_EDGE = "#7f93b5"; // края столбиков
constexpr const char* COLOR_PROJ = "#8e24aa";     // проекция скорости — фиолетовый
constexpr const char* COLOR_PAGE = "#eef1f6";     // фон страниц (карточки на нём белые)
constexpr const char* COLOR_DARK = "#1c3f7a";     // заголовки, значки
constexpr const char* COLOR_RANGE = "#d5dbe6";    // график во времени: полоса min…max
constexpr const char* COLOR_SPREAD = "#9aa7bf";   // график во времени: полоса среднее ± σ

// --------------------------------------------------------------------------
// Линии и графики (толщины — в BASE: 0.1 ≈ десятая высоты буквы)
// --------------------------------------------------------------------------
constexpr double THEORY_LINE = 0.18;     // теоретическая кривая на гистограмме
constexpr double CURVE_LINE = 0.08;      // кривая величины во времени
constexpr double CURRENT_LINE = 0.12;    // пунктир текущего значения
constexpr double AXIS_WIDTH = 4.2;       // ширина левой оси графиков (числа + подпись)
constexpr double AXIS_HEIGHT = 2.6;      // высота нижней оси
constexpr double HIST_HEADROOM = 1.35;   // ось плотности выше пика теории во столько раз
constexpr double FLASH_DECAY = 0.90;     // подсветка нового отсчёта гаснет за кадр во столько раз (ближе к 1 — дольше)
constexpr double VECTOR_SIZE = 10;       // векторная диаграмма: желаемая сторона (в BASE)
constexpr double VECTOR_MIN_SIZE = 4;    //                        наименьшая, если мало места
constexpr double ARROW_HEAD = 3.0;       // наконечник стрелки в сосуде, нм
constexpr double CLICK_DISTANCE = 4.0;   // щелчок выбирает молекулу не дальше стольких нм

// --------------------------------------------------------------------------
// Страница "Теория"
// --------------------------------------------------------------------------
constexpr double DRAWER_WIDTH = 17;      // ширина выдвижного списка разделов (в BASE)
constexpr double THEORY_AXIS_ROOM = 1.6; // ось x живых графиков шире кривой во столько раз
constexpr int SAMPLES_PER_TICK = 20;     // "▶ Набирать": отсчётов за 50 мс

// --------------------------------------------------------------------------
// Газ по умолчанию (то, что видно сразу после запуска)
// --------------------------------------------------------------------------
constexpr int START_TEMPERATURE = 300;   // К
constexpr int START_N = 150;             // число молекул
constexpr int START_MASS_A = 28;         // а.е.м. (азот)
constexpr int START_MASS_B = 4;          // а.е.м. (гелий)
constexpr int START_N_B = 50;            // молекул B в смеси

// --------------------------------------------------------------------------
// Диапазоны движков
// --------------------------------------------------------------------------
constexpr int TEMPERATURE_MIN = 50, TEMPERATURE_MAX = 1500;  // К
constexpr int N_MIN = 2, N_MAX = 300;                        // N_MAX не больше physics::MAX_PARTICLES
constexpr int MASS_MIN = 1, MASS_MAX = 200;                  // а.е.м.
constexpr int BINS_MIN = 10, BINS_MAX = 80, START_BINS = 30; // столбиков в гистограммах
// Память статистики — в столкновениях молекулы 1 (см. Histogram::forget).
// 300 подобрано тестом (шум ↔ скорость реакции); в опыте "Все одинаковые" ставится RELAX_MEMORY.
constexpr int MEMORY_MIN = 1, MEMORY_MAX = 5000, START_MEMORY = 300;
constexpr int RELAX_MEMORY = 3;

// --------------------------------------------------------------------------
// Сосуд и молекулы
// --------------------------------------------------------------------------
constexpr double BOX_SIZE = 100.0;       // сторона сосуда, нм
constexpr int MAX_PARTICLES = 300;
constexpr double R_MAX = 2.4;            // радиус самой тяжёлой молекулы (массой M_MAX), нм; r ∝ m^(1/3)
constexpr double M_MAX = 200.0;          // а.е.м.
constexpr double BEAM_ANGLE = 30.0;      // опыт "Все одинаковые": направление общей скорости, градусов от оси x

// --------------------------------------------------------------------------
// Ход расчёта
// --------------------------------------------------------------------------
constexpr int FRAME_MS = 16;             // кадр раз в 16 мс (~60 кадров/с)
constexpr int MIN_IDLE_MS = 5;           // после кадра хотя бы столько мс свободно (чтобы работали движки)
constexpr double FAST_BUDGET = 0.020;    // быстрый режим: секунд расчёта на кадр
constexpr int ENSEMBLE_EVERY = 10;       // статистика по всем молекулам — раз в столько шагов
// Медленный режим: шагов dt за кадр при положениях движка "Скорость" 1..12
constexpr double SLOW_FACTORS[] = {0.05, 0.1, 0.15, 0.25, 0.4, 0.6, 1.0, 1.5, 2.5, 4.0, 10.0, 25.0};
constexpr int SLOW_COUNT = sizeof(SLOW_FACTORS) / sizeof(SLOW_FACTORS[0]);
constexpr int START_SPEED = 7;           // начальное положение движка "Скорость": 7 → 1.0 шаг за кадр
constexpr int RELAX_SPEED = 11;          // в опыте "Все одинаковые": 11 → 10 шагов за кадр (равновесие за ~3 с)

// --------------------------------------------------------------------------
// Что показывать при открытии "Презентации"
// --------------------------------------------------------------------------
constexpr bool AUTOSTART = true;         // опыт запускается сам
constexpr bool START_ENSEMBLE = false;    // статистика сразу по всем молекулам (гистограммы набираются за секунды)
constexpr bool START_TWO_PANELS = true;  // два графика: |v_отн| и |v₁| (видно отношение √2)

}  // namespace settings
