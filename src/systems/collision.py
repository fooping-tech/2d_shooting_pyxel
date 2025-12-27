from __future__ import annotations

from src.core.types import Rect


def aabb(a: Rect, b: Rect) -> bool:
    return a.intersects(b)

