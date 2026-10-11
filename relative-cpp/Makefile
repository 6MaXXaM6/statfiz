# Короткие команды для сборки и проверки:
#   make linux    — dist/linux/relative/ (+ архив) и smoke-тест
#   make windows  — dist/windows/Relative.exe (MXE) и smoke-тест под wine
#   make test     — тесты модели
#   make layout   — проверка компоновки на трёх разрешениях
#   make run      — запустить в окне

QT_DIR ?= $(HOME)/Qt/5.15.2/gcc_64
DEV     = build/dev
CMAKE_DEV = cmake -S . -B $(DEV) -DCMAKE_BUILD_TYPE=Release $(if $(wildcard $(QT_DIR)),-DCMAKE_PREFIX_PATH=$(QT_DIR))

.PHONY: all linux windows test layout run dev clean

all: test linux windows

dev:
	@$(CMAKE_DEV) >/dev/null
	@cmake --build $(DEV) -j$$(nproc)

test: dev
	$(DEV)/test_model

layout: dev
	$(DEV)/relative --layout-check

run: dev
	$(DEV)/relative --window

linux:
	scripts/build_linux.sh
	scripts/smoke_test.sh linux

windows:
	scripts/build_windows.sh
	scripts/smoke_test.sh windows

clean:
	rm -rf build dist
