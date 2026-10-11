#!/usr/bin/env bash
# Сборка для Windows (7 и новее) на Linux: один файл dist/windows/Relative.exe без DLL.
#
# Компилятор и статический Qt 5.15 — из MXE (https://mxe.cc), один раз собираются так:
#     sudo apt install <пакеты из README.md>
#     git clone https://github.com/mxe/mxe.git ~/mxe
#     make -C ~/mxe MXE_TARGETS=x86_64-w64-mingw32.static qtbase -j32
set -euo pipefail
cd "$(dirname "$0")/.."

MXE=${MXE:-$HOME/mxe}
TARGET=x86_64-w64-mingw32.static
BUILD=build/windows

if [ ! -x "$MXE/usr/bin/$TARGET-cmake" ]; then
    echo "Нет MXE с Qt в $MXE — см. начало этого скрипта." >&2
    exit 1
fi
export PATH="$MXE/usr/bin:$PATH"
"$TARGET-cmake" -S . -B "$BUILD" -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$BUILD" -j"$(nproc)"

mkdir -p dist/windows
cp "$BUILD/Relative.exe" dist/windows/
echo "Готово: dist/windows/Relative.exe ($(du -h dist/windows/Relative.exe | cut -f1))"
