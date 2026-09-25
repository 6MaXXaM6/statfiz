# Команды проекта. Самое нужное:
#   make           — собрать оба файла: dist/windows/Relative.exe и dist/linux/relative
#   make windows   — только exe для Windows (через wine)
#   make linux     — только исполняемый файл для Linux
#   make run       — запустить из исходников в окне
#   make test      — тесты физики + проверка компоновки на разных экранах
#   make clean     — удалить результаты сборки

PYTHON := .venv/bin/python

.PHONY: all windows linux run test layout clean

all: linux windows

windows:
	scripts/build_windows.sh

linux:
	scripts/build_linux.sh

run:
	$(PYTHON) main.py --window

test:
	$(PYTHON) -m pytest -q tests
	$(PYTHON) -m pyflakes main.py model ui pages tools tests

layout:
	$(PYTHON) tools/layout_check.py

clean:
	rm -rf build dist
