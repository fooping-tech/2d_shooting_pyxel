from __future__ import annotations

from dataclasses import dataclass

from src.core.types import Rect, Vec2


@dataclass
class Enemy:
    active: bool
    kind: str
    pos: Vec2
    vel: Vec2
    hp: int
    timer: int
    pattern: str
    w: int
    h: int
    score: int
    shoot_cooldown: int = 0
    burn_timer: int = 0
    burn_tick: int = 0

    def rect(self) -> Rect:
        return Rect(self.pos.x, self.pos.y, self.w, self.h)
