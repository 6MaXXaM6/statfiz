#!/usr/bin/env bash
# Проверка собранной программы: scripts/smoke_test.sh linux|windows
# Программа сама открывает все страницы, считает 4 с и пишет результат в файл.
# Windows-версия запускается под wine в чистом префиксе (как на "голом" компьютере).
set -euo pipefail
cd "$(dirname "$0")/.."

report=build/smoke-$1.txt
rm -f "$report"
case "$1" in
    linux)
        timeout 60 dist/linux/relative/relative.sh --smoke-test "$report" 2>/dev/null || true ;;
    windows)
        export WINEPREFIX=${WINEPREFIX:-$HOME/.wine-relative-test} WINEDEBUG=-all
        timeout 120 wine dist/windows/Relative.exe --smoke-test "$(winepath -w "$report")" || true ;;
    *)
        echo "использование: $0 linux|windows" >&2; exit 2 ;;
esac
if grep -q '^OK' "$report" 2>/dev/null; then
    echo "smoke $1: $(cat "$report")"
else
    echo "smoke $1: ОШИБКА" >&2
    exit 1
fi
