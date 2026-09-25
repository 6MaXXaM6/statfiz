#!/usr/bin/env bash
# Сборка для Windows из Linux: один файл dist/windows/Relative.exe (работает начиная с Windows 7).
# Внутри wine ставится Windows-версия Python 3.8, и PyInstaller запускается уже в ней.
set -euo pipefail
cd "$(dirname "$0")/.."

export WINEDEBUG=-all
BUILD_PREFIX="${BUILD_PREFIX:-$HOME/.wine-build}"   # wine с Python для сборки
CACHE="$HOME/.cache/relative-build"
PY_EXE="python-3.8.10-amd64.exe"
PY_URL="https://www.python.org/ftp/python/3.8.10/$PY_EXE"
PY_SHA256="7628244cb53408b50639d2c1287c659f4e29d3dfdb9084b11aed5870c0c6a48a"

command -v wine >/dev/null || { echo "Нужен wine: sudo apt install wine"; exit 1; }

win_python() {
    WINEPREFIX="$BUILD_PREFIX" wine 'C:\Python38\python.exe' "$@" 2> >(grep -v -e dbus -e 'D-Bus' >&2)
}

if [ ! -f "$BUILD_PREFIX/drive_c/Python38/python.exe" ]; then
    echo "==> Ставлю Windows Python 3.8 в $BUILD_PREFIX"
    mkdir -p "$CACHE"
    [ -f "$CACHE/$PY_EXE" ] || curl -fsSL -o "$CACHE/$PY_EXE" "$PY_URL"
    echo "$PY_SHA256  $CACHE/$PY_EXE" | sha256sum -c --quiet
    WINEPREFIX="$BUILD_PREFIX" WINEARCH=win64 wineboot -i >/dev/null 2>&1
    WINEPREFIX="$BUILD_PREFIX" wine "$CACHE/$PY_EXE" /quiet InstallAllUsers=0 'TargetDir=C:\Python38' \
        PrependPath=0 Include_test=0 Include_doc=0 Include_tcltk=0 Include_launcher=0
fi

echo "==> Ставлю зависимости (в wine)"
# PyQt5-Qt5 5.15.2 — последняя версия Qt 5 с готовыми файлами для Windows
win_python -m pip install -q --no-warn-script-location -r requirements-build.txt "PyQt5-Qt5==5.15.2"

echo "==> Собираю dist/windows/Relative.exe"
win_python -m PyInstaller --noconfirm --clean --log-level WARN \
    --distpath dist/windows --workpath build/windows packaging/relative.spec

scripts/smoke_test.sh windows
