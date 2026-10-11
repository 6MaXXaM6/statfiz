// Самопроверки собранной программы (запускаются ключами командной строки, без окна на экране):
//
//   --smoke-test файл     — открыть все страницы, посчитать 4 с в быстром режиме с двумя
//                           графиками, записать в файл "OK collisions=… panels=…";
//   --layout-check [WxH]  — пройти по всем кнопкам страницы "Презентация" и проверить, что
//                           ничего не вылезает за экран и графики не "ездят";
//   --screenshot WxH страница кадров файл.png [настройки] — снимок окна.

#pragma once

#include <QApplication>
#include <QStringList>

class MainWindow;

void smoke_test(QApplication& app, MainWindow& window, const QString& report_path);
int layout_check(QApplication& app, const QStringList& screens);
int screenshot(QApplication& app, const QStringList& args);
