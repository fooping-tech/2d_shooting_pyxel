from __future__ import annotations

from dataclasses import dataclass

from src.core.types import Vec2


@dataclass
class Particle:
    active: bool
    pos: Vec2
    vel: Vec2
    lifetime: int
