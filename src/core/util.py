from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", int, float)


def clamp(value: T, minimum: T, maximum: T) -> T:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def approach(value: float, target: float, delta: float) -> float:
    if value < target:
        return min(value + delta, target)
    return max(value - delta, target)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

