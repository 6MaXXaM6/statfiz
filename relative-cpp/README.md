# Относительная скорость молекул — C++ / Qt5

Новая версия презентации 2010 года. Устройство программы описано в [ARCHITECTURE.md](ARCHITECTURE.md),
а как быстро что-то поменять (шрифты, диапазоны, цвета) — в [ПРАВКИ.md](ПРАВКИ.md).

## Команды

```
make test      # тесты модели (физика, теория, статистика)
make run       # запустить в окне (F11 — полный экран)
make layout    # проверить компоновку на 1024×768, 1366×768, 1920×1080
make linux     # dist/linux/relative/ + relative.tar.xz, затем smoke-тест
make windows   # dist/windows/Relative.exe, затем smoke-тест под wine
```

## Что нужно один раз

**Linux:** cmake, g++ и Qt 5.15. Qt можно поставить без sudo:
```
python3 -m venv ~/.aqt-venv && ~/.aqt-venv/bin/pip install aqtinstall
~/.aqt-venv/bin/aqt install-qt linux desktop 5.15.2 gcc_64 -O ~/Qt
```
или системный: `sudo apt install qtbase5-dev`.

**Windows (сборка на Linux):** статический Qt из [MXE](https://mxe.cc). Около 1 часа один раз:
```
sudo apt install autoconf automake autopoint bison flex g++-multilib gettext gperf intltool \
    libc6-dev-i386 libgdk-pixbuf-2.0-dev libltdl-dev libpcre2-dev libtool-bin lzip p7zip-full \
    python-is-python3 sqlite3
git clone https://github.com/mxe/mxe.git ~/mxe
make -C ~/mxe MXE_TARGETS=x86_64-w64-mingw32.static qtbase -j$(nproc)
```
Для smoke-теста Windows-версии нужен wine.
