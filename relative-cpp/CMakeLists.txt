# Сборка презентации "Относительная скорость молекул".
#   model  — библиотека физики и статистики (без Qt), её же проверяют тесты;
#   relative — приложение (Qt5 Widgets);
#   test_model — тесты модели.

cmake_minimum_required(VERSION 3.16)
project(relative LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# --- модель: чистый C++ ---
add_library(model STATIC
    src/model/physics.cpp
    src/model/theory.cpp
    src/model/stats.cpp
    src/model/experiment.cpp
)
target_include_directories(model PUBLIC src)
target_compile_options(model PRIVATE -Wall -Wextra)

add_executable(test_model tests/test_model.cpp)
target_link_libraries(test_model PRIVATE model)

# --- приложение ---
find_package(Qt5 5.12 REQUIRED COMPONENTS Widgets)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

add_executable(relative WIN32
    src/main.cpp
    src/main_window.cpp
    src/checks.cpp
    src/ui/style.cpp
    src/ui/widgets.cpp
    src/ui/labels.cpp
    src/ui/icons.cpp
    src/ui/drawer.cpp
    src/ui/plots/plot_base.cpp
    src/ui/plots/time_plot.cpp
    src/ui/plots/hist_plot.cpp
    src/ui/plots/box_view.cpp
    src/ui/plots/vector_view.cpp
    src/ui/plots/curve_plot.cpp
    src/pages/title_page.cpp
    src/pages/authors_page.cpp
    src/pages/theory/theory_page.cpp
    src/pages/theory/section_view.cpp
    src/pages/theory/curve_demo.cpp
    src/pages/theory/sampling_demo.cpp
    src/pages/theory/collision_sketch.cpp
    src/pages/demo/demo_page.cpp
    src/pages/demo/graph_panel.cpp
    src/pages/demo/gas_panel.cpp
    src/pages/demo/run_controls.cpp
    src/pages/demo/readouts.cpp
    # заголовки с Q_OBJECT — чтобы AUTOMOC их точно нашёл
    src/ui/widgets.h
    src/ui/plots/hist_plot.h
    src/ui/plots/box_view.h
    resources.qrc
)
target_link_libraries(relative PRIVATE model Qt5::Widgets)
target_compile_options(relative PRIVATE -Wall -Wextra)

if(UNIX)
    # Linux: библиотеки Qt ищутся сначала в папке lib рядом с программой (см. scripts/build_linux.sh)
    set_target_properties(relative PROPERTIES BUILD_RPATH "\$ORIGIN/lib")
endif()

if(WIN32)
    # Один exe без DLL: статический Qt (MXE) и статические библиотеки компилятора.
    set_target_properties(relative PROPERTIES OUTPUT_NAME Relative)
    target_link_options(relative PRIVATE -static -static-libgcc -static-libstdc++ -s)
    # Модуль платформы Windows вшивается в exe (см. Q_IMPORT_PLUGIN в main.cpp)
    target_link_libraries(relative PRIVATE Qt5::QWindowsIntegrationPlugin)
endif()
