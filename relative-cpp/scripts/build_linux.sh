#!/usr/bin/env bash
# Сборка для Linux: dist/linux/relative/ — программа и нужные ей библиотеки Qt рядом
# (запускается и там, где Qt не установлен), плюс архив dist/linux/relative.tar.xz.
#
# Qt берётся из QT_DIR (по умолчанию ~/Qt/5.15.2/gcc_64, скачанный aqtinstall),
# а если его нет — системный (пакет qtbase5-dev).
set -euo pipefail
cd "$(dirname "$0")/.."

QT_DIR=${QT_DIR:-$HOME/Qt/5.15.2/gcc_64}
BUILD=build/linux
OUT=dist/linux/relative

prefix=()
[ -d "$QT_DIR" ] && prefix=(-DCMAKE_PREFIX_PATH="$QT_DIR")
cmake -S . -B "$BUILD" -DCMAKE_BUILD_TYPE=Release "${prefix[@]}" >/dev/null
cmake --build "$BUILD" -j"$(nproc)"

# Программа ищет библиотеки в ./lib, а модуль платформы — в ./plugins (см. qt.conf).
rm -rf "$OUT"
mkdir -p "$OUT/lib" "$OUT/plugins/platforms"
cp "$BUILD/relative" "$OUT/"
strip "$OUT/relative"
qt_lib=$(ldd "$BUILD/relative" | awk '/libQt5Core/ {print $3}' | xargs readlink -f | xargs dirname)
qt_plugins=$(dirname "$qt_lib")/plugins
# xcb — обычный экран, offscreen — для самопроверок без окна (--smoke-test)
cp "$qt_plugins/platforms/libqxcb.so" "$qt_plugins/platforms/libqoffscreen.so" "$OUT/plugins/platforms/"
# Библиотеки Qt (и ICU), от которых зависят программа и модули платформы.
# ldd — по ОРИГИНАЛАМ модулей в папке Qt: у копий рядом ещё нет наших библиотек,
# и ldd нашёл бы системный Qt (другой версии) — такие библиотеки в папку не попали бы.
for f in "$BUILD/relative" "$qt_plugins/platforms/libqxcb.so" "$qt_plugins/platforms/libqoffscreen.so"; do
    ldd "$f" | awk '$3 ~ /^\// {print $3}' | xargs readlink -f | grep "^$qt_lib/" || true
done | sort -u | while read -r lib; do
    # копия под именем, которое ищет загрузчик (libQt5Core.so.5, а не libQt5Core.so.5.15.2)
    soname=$(readelf -d "$lib" | sed -n 's/.*SONAME.*\[\(.*\)\]/\1/p')
    cp "$lib" "$OUT/lib/$soname"
done
printf '[Paths]\nPrefix = .\nPlugins = plugins\n' > "$OUT/qt.conf"

# Программа и так ищет библиотеки в ./lib (RPATH задан в CMakeLists.txt);
# скрипт — запасной способ запуска, если файл переложили без папки lib.
cat > "$OUT/relative.sh" <<'EOF'
#!/bin/sh
here=$(dirname "$(readlink -f "$0")")
LD_LIBRARY_PATH="$here/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" exec "$here/relative" "$@"
EOF
chmod +x "$OUT/relative.sh"

# Проверка: всё, что относится к Qt, берётся из папки lib, а не из системы
# (иначе "Cannot mix incompatible Qt library" на компьютере, где стоит другой Qt).
for f in "$OUT/relative" "$OUT"/plugins/platforms/*.so; do
    bad=$(ldd "$f" | grep -E 'libQt5|libicu' | awk '{print $3}' | xargs readlink -f | grep -v "^$(readlink -f "$OUT/lib")/" || true)
    missing=$(ldd "$f" | grep 'not found' || true)
    if [ -n "$bad$missing" ]; then
        echo "ОШИБКА: $f берёт библиотеки не из папки lib:" >&2
        echo "$bad$missing" >&2
        exit 1
    fi
done

tar -C dist/linux -cJf dist/linux/relative.tar.xz relative
echo "Готово: $OUT ($(du -sh "$OUT" | cut -f1)), архив $(du -h dist/linux/relative.tar.xz | cut -f1)"
