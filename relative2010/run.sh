#!/bin/bash
# Запуск Relative (physics.exe) под Wine в отдельном префиксе
export WINEPREFIX="$HOME/.wine-relative"
export WINEDEBUG=-all
cd "$(dirname "$(readlink -f "$0")")" || exit 1
exec wine physics.exe "$@"
