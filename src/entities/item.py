from __future__ import annotations

from dataclasses import dataclass

from src.core.types import Rect, Vec2


@dataclass
class Item:
    active: bool
    kind: str  # "heal" | "power" | "speed"
    pos: Vec2
    vel: Vec2
    w: int
    h: int
    lifetime: int

    def rect(self) -> Rect:
        return Rect(self.pos.x, self.pos.y, self.w, self.h)
