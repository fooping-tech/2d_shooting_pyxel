from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.types import Rect, Vec2
from src.core.util import clamp


@dataclass
class Player:
    ship: str
    pos: Vec2
    w: int
    h: int
    life: int
    max_life: int
    invincible: int
    speed: float
    max_speed: float
    weapon_level: int
    laser_maxed: bool = False
    bomb_radius_maxed: bool = False
    bomb_homing: bool = False
    bomb_big: bool = False
    flame_upgraded: bool = False
    cooldown_cannon: int = 0
    cooldown_missile: int = 0
    cooldown_bomb: int = 0
    cooldown_laser: int = 0

    def rect(self) -> Rect:
        # forgiving hitbox
        return Rect(self.pos.x + 3, self.pos.y + 3, self.w - 6, self.h - 6)

    def apply_damage(self, amount: int, inv_frames: int) -> bool:
        if self.invincible > 0:
            return False
        self.life = max(0, self.life - amount)
        self.invincible = inv_frames
        return True

    def heal(self, amount: int) -> None:
        self.life = int(clamp(self.life + amount, 0, self.max_life))

    def power_up(self, amount: int, max_level: int) -> None:
        self.weapon_level = int(clamp(self.weapon_level + amount, 1, max_level))

    def speed_up(self, amount: float) -> None:
        self.speed = float(clamp(self.speed + amount, 0.2, self.max_speed))

    def step_cooldowns(self) -> None:
        self.cooldown_cannon = max(0, self.cooldown_cannon - 1)
        self.cooldown_missile = max(0, self.cooldown_missile - 1)
        self.cooldown_bomb = max(0, self.cooldown_bomb - 1)
        self.cooldown_laser = max(0, self.cooldown_laser - 1)
        self.invincible = max(0, self.invincible - 1)

    @staticmethod
    def from_config(config: dict[str, Any], ship: str, start_x: int, start_y: int) -> Player:
        p = config.get("player", {})
        max_life = int(p.get("max_life", 100))
        base_speed = float(p.get("base_speed", 1.6))
        max_speed = float(p.get("max_speed", 3.2))
        return Player(
            ship=ship,
            pos=Vec2(float(start_x), float(start_y)),
            w=16,
            h=16,
            life=max_life,
            max_life=max_life,
            invincible=0,
            speed=base_speed,
            max_speed=max_speed,
            weapon_level=1,
        )
