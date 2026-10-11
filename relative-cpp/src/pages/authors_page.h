// Страница "Авторы": имена и фотографии из assets/authors.json.

#pragma once

#include <QWidget>
#include <functional>

class AuthorsPage : public QWidget {
public:
    explicit AuthorsPage(std::function<void()> go_home);
};
