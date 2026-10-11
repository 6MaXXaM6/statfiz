// Подписи: легенда к векторной диаграмме и сравнение двух величин (√2).

#pragma once

#include <QString>
#include <optional>

#include "model/experiment.h"

// Цветная подпись к векторной диаграмме; projection_of — чья проекция показана (или пусто).
QString vector_legend(std::optional<Obj> projection_of);

// Во сколько раз относительная скорость больше скорости молекулы obj — опыт и теория.
QString ratio_text(const Experiment& exp, Obj obj, theory::Kind kind);
