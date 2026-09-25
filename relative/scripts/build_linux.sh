#!/usr/bin/env bash
# Сборка для Linux: один исполняемый файл dist/linux/relative.
# Нужен Python 3.8 (ставится через pyenv, если его нет) — те же версии библиотек, что и в exe.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON_VERSION=3.8.20
VENV=.venv

if [ ! -x "$VENV/bin/python" ]; then
    echo "==> Создаю окружение $VENV (Python $PYTHON_VERSION)"
    if command -v pyenv >/dev/null; then
        pyenv install -s "$PYTHON_VERSION"
        PY="$(pyenv root)/versions/$PYTHON_VERSION/bin/python"
    else
        PY=python3.8
    fi
    "$PY" -m venv "$VENV"
fi

echo "==> Ставлю зависимости"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r requirements-dev.txt

echo "==> Собираю dist/linux/relative"
"$VENV/bin/python" -m PyInstaller --noconfirm --clean --log-level WARN \
    --distpath dist/linux --workpath build/linux packaging/relative.spec

scripts/smoke_test.sh linux
