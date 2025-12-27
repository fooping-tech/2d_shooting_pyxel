from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass
class Vec2:
    x: float
    y: float

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def length(self) -> float:
        return hypot(self.x, self.y)

    def normalized(self) -> Vec2:
        length = self.length()
        if length <= 1e-9:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / length, self.y / length)


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    def intersects(self, other: Rect) -> bool:
        return (
            self.x < other.x + other.w
            and self.x + self.w > other.x
            and self.y < other.y + other.h
            and self.y + self.h > other.y
        )

    def moved(self, dx: float, dy: float) -> Rect:
        return Rect(self.x + dx, self.y + dy, self.w, self.h)
