# Запуск на macOS (Apple Silicon)

Команды выполняются из корня проекта `statfiz`.

## C++

Установлены CMake и Qt 5 через Homebrew; компилятор Apple Clang — из Command Line Tools.

```sh
make -C relative-cpp dev    # собрать
make -C relative-cpp run    # собрать и открыть окно
make -C relative-cpp test   # тесты модели
```

Исполняемый файл: `relative-cpp/build/dev/relative`.

## Python

Используется Python 3.9.6 из Command Line Tools. Зависимости из
`relative/requirements-dev.txt` установлены в `relative/.venv-macos`.
Окружение `.venv` из Linux сохранено, на macOS оно не используется.

```sh
make -C relative run        # открыть окно
make -C relative test       # тесты модели и pyflakes
make -C relative macos      # собрать самостоятельный исполняемый файл
```

Собранный Python-вариант: `relative/dist/macos/relative`.

Для повторного создания окружения:

```sh
/usr/bin/python3 -m venv relative/.venv-macos
relative/.venv-macos/bin/python -m pip install -r relative/requirements-dev.txt
```

Цели `linux` и `windows` предназначены для других платформ, для сборки на этом Mac
используйте команды выше.
