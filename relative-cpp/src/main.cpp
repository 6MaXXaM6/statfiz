// Презентация "Относительная скорость движения молекул идеального газа".
// Запуск: relative   (F11 — полный экран / окно, Esc — выйти из полного экрана)
//         relative --window                      — в окне 1024×768
//         relative --smoke-test файл | --layout-check [WxH…] | --screenshot …  — проверки (см. checks.h)

#include <QApplication>

#include "checks.h"
#include "main_window.h"
#include "ui/style.h"

#ifdef QT_STATIC
// Статическая сборка (Windows, один exe): модуль платформы нужно подключить явно.
#include <QtPlugin>
Q_IMPORT_PLUGIN(QWindowsIntegrationPlugin)
#endif

int main(int argc, char* argv[])
{
    QStringList args;
    for (int k = 1; k < argc; ++k)
        args << QString::fromLocal8Bit(argv[k]);
    bool check = args.contains("--smoke-test") || args.contains("--layout-check") || args.contains("--screenshot");
    // Проверки идут без окна на экране. Задаём это здесь, а не переменной окружения:
    // под wine переменные Linux в Windows-программу не передаются.
    if (check)
        qputenv("QT_QPA_PLATFORM", "offscreen");

    // Масштабирование для экранов с увеличенным DPI (до создания приложения).
    QApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QApplication::setAttribute(Qt::AA_UseHighDpiPixmaps);
    QApplication app(argc, argv);

    if (args.contains("--layout-check"))
        return layout_check(app, args.mid(args.indexOf("--layout-check") + 1));
    if (args.contains("--screenshot"))
        return screenshot(app, args.mid(args.indexOf("--screenshot") + 1));

    style::init_style(app);
    MainWindow window;
    if (args.contains("--window") || args.contains("--smoke-test")) {
        window.resize(1024, 768);
        window.show();
    } else {
        window.showFullScreen();
    }
    if (args.contains("--smoke-test"))
        smoke_test(app, window, args.value(args.indexOf("--smoke-test") + 1));
    return app.exec();
}
