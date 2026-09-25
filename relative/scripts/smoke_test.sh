#!/usr/bin/env bash
# Проверка собранного файла: запустить с --smoke-test (все страницы, 4 графика, расчёт ~4 с)
# и убедиться, что программа записала "OK". Окно не показывается (QT_QPA_PLATFORM=offscreen).
#   scripts/smoke_test.sh linux | windows
# exe проверяется в отдельном "чистом" wine без Python — как на компьютере пользователя.
set -euo pipefail
cd "$(dirname "$0")/.."

report="build/smoke-$1.txt"
mkdir -p build
rm -f "$report"
export QT_QPA_PLATFORM=offscreen

case "$1" in
    linux)
        timeout 120 dist/linux/relative --smoke-test "$report" 2>/dev/null || true
        ;;
    windows)
        export WINEDEBUG=-all
        export WINEPREFIX="${TEST_PREFIX:-$HOME/.wine-relative-test}"
        [ -d "$WINEPREFIX" ] || WINEARCH=win64 wineboot -i >/dev/null 2>&1
        timeout 180 wine dist/windows/Relative.exe --smoke-test "$report" >/dev/null 2>&1 || true
        ;;
    *)
        echo "использование: $0 linux|windows"; exit 2
        ;;
esac

if grep -q '^OK' "$report" 2>/dev/null; then
    echo "==> Проверка $1: $(cat "$report")"
else
    echo "==> Проверка $1 НЕ ПРОЙДЕНА (программа не записала OK в $report)"
    exit 1
fi
