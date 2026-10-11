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
qt_lib=$(ldd "$BUILD/relative" | awk '/libQt5Core/ {print $3}' | xargs dirname)
qt_plugins=$(dirname "$qt_lib")/plugins
# xcb — обычный экран, offscreen — для самопроверок без окна (--smoke-test)
cp "$qt_plugins/platforms/libqxcb.so" "$qt_plugins/platforms/libqoffscreen.so" "$OUT/plugins/platforms/"
# Библиотеки Qt (и ICU), от которых зависят программа и модули платформы
for f in "$BUILD/relative" "$OUT"/plugins/platforms/*.so; do
    ldd "$f" | awk -v dir="$qt_lib" 'index($3, dir) == 1 {print $3}'
done | sort -u | xargs -I{} cp -L {} "$OUT/lib/"
printf '[Paths]\nPrefix = .\nPlugins = plugins\n' > "$OUT/qt.conf"

# Программа и так ищет библиотеки в ./lib (RPATH задан в CMakeLists.txt);
# скрипт — запасной способ запуска, если файл переложили без папки lib.
cat > "$OUT/relative.sh" <<'EOF'
#!/bin/sh
here=$(dirname "$(readlink -f "$0")")
LD_LIBRARY_PATH="$here/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" exec "$here/relative" "$@"
EOF
chmod +x "$OUT/relative.sh"

tar -C dist/linux -cJf dist/linux/relative.tar.xz relative
echo "Готово: $OUT ($(du -sh "$OUT" | cut -f1)), архив $(du -h dist/linux/relative.tar.xz | cut -f1)"
