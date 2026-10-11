// Двумерный вектор: положение (нм) или скорость (м/с) молекулы.

#pragma once

#include <cmath>

struct Vec2 {
    double x = 0.0;
    double y = 0.0;

    Vec2() = default;
    Vec2(double x_, double y_) : x(x_), y(y_) {}

    Vec2 operator+(Vec2 o) const { return {x + o.x, y + o.y}; }
    Vec2 operator-(Vec2 o) const { return {x - o.x, y - o.y}; }
    Vec2 operator*(double k) const { return {x * k, y * k}; }
    Vec2& operator+=(Vec2 o) { x += o.x; y += o.y; return *this; }
    Vec2& operator-=(Vec2 o) { x -= o.x; y -= o.y; return *this; }
    Vec2& operator*=(double k) { x *= k; y *= k; return *this; }

    double dot(Vec2 o) const { return x * o.x + y * o.y; }
    double length_sq() const { return x * x + y * y; }
    double length() const { return std::hypot(x, y); }
};
