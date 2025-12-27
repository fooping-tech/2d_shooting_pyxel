from __future__ import annotations

from dataclasses import dataclass

from src.core.types import Rect, Vec2


@dataclass
class Projectile:
    active: bool
    kind: str
    owner: str  # "player" | "enemy"
    pos: Vec2
    vel: Vec2
    w: int
    h: int
    damage: int
    lifetime: int
    radius: int = 0

    def rect(self) -> Rect:
        return Rect(self.pos.x, self.pos.y, self.w, self.h)


@dataclass
class LaserBeam:
    active: bool
    x: float
    y: float
    length: int
    width: int
    damage: int
    duration: int
    tick_interval: int
    _tick: int = 0

    def rect(self) -> Rect:
        return Rect(self.x, self.y - self.width / 2, self.length, self.width)

    def can_tick(self) -> bool:
        return self.active and self._tick <= 0

    def consume_tick(self) -> None:
        self._tick = self.tick_interval

    def step(self) -> None:
        if not self.active:
            return
        self.duration -= 1
        self._tick -= 1
        if self.duration <= 0:
            self.active = False


@dataclass
class FlameStream:
    active: bool
    x: float
    y: float
    length: int
    width: int
    damage: int
    tick_interval: int
    _tick: int = 0

    def rect(self) -> Rect:
        return Rect(self.x, self.y - self.width / 2, self.length, self.width)

    def can_tick(self) -> bool:
        return self.active and self._tick <= 0

    def consume_tick(self) -> None:
        self._tick = self.tick_interval

    def step(self) -> None:
        if not self.active:
            return
        self._tick -= 1
