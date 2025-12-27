from __future__ import annotations

from dataclasses import dataclass
from random import Random

from src.core.types import Vec2
from src.entities.enemy import Enemy


@dataclass(frozen=True)
class SpawnSpec:
    kind: str
    pattern: str


class Spawner:
    def __init__(self, rng: Random, screen_w: int, screen_h: int) -> None:
        self._rng = rng
        self._w = screen_w
        self._h = screen_h
        self._formation_timer = 0

    def update(self, spawn_rate: float, enemies: list[Enemy], section_name: str) -> None:
        self._formation_timer = max(0, self._formation_timer - 1)
        if self._formation_timer == 0 and self._rng.random() < spawn_rate * 0.12:
            self._formation_timer = 120
            self._spawn_formation(enemies, section_name)
            return
        if self._rng.random() >= spawn_rate:
            return
        spec = self._choose_enemy(section_name)
        x = self._w + 10
        y = self._rng.randint(8, self._h - 32)
        enemies.append(self._create_enemy(spec, x, y))

    def _choose_enemy(self, section_name: str) -> SpawnSpec:
        r = self._rng.random()
        if section_name == "moon":
            if r < 0.65:
                return SpawnSpec(kind="drone", pattern="straight")
            if r < 0.88:
                return SpawnSpec(kind="fighter", pattern="sine")
            return SpawnSpec(kind="turret", pattern="stop_shoot")
        if section_name == "space":
            if r < 0.55:
                return SpawnSpec(kind="fighter", pattern="sine")
            if r < 0.80:
                return SpawnSpec(kind="drone", pattern="dash")
            return SpawnSpec(kind="turret", pattern="stop_shoot")
        if section_name == "planet1":
            if r < 0.45:
                return SpawnSpec(kind="drone", pattern="wave")
            if r < 0.78:
                return SpawnSpec(kind="fighter", pattern="sine")
            return SpawnSpec(kind="turret", pattern="stop_shoot")
        # planet2
        if r < 0.35:
            return SpawnSpec(kind="drone", pattern="dash")
        if r < 0.70:
            return SpawnSpec(kind="fighter", pattern="sine")
        return SpawnSpec(kind="turret", pattern="stop_shoot")

    def _create_enemy(self, spec: SpawnSpec, x: int, y: int) -> Enemy:
        if spec.kind == "turret":
            hp = 4
            score = 2
        elif spec.kind == "fighter":
            hp = 3
            score = 1
        else:
            hp = 2
            score = 1
        return Enemy(
            active=True,
            kind=spec.kind,
            pos=Vec2(float(x), float(y)),
            vel=Vec2(-1.4, 0.0),
            hp=hp,
            timer=0,
            pattern=spec.pattern,
            w=12,
            h=8,
            score=score,
            shoot_cooldown=60,
        )

    def _spawn_formation(self, enemies: list[Enemy], section_name: str) -> None:
        base_y = self._rng.randint(12, self._h - 48)
        kinds = ["drone", "fighter", "drone"] if section_name != "moon" else ["drone", "drone", "drone"]
        for i, kind in enumerate(kinds):
            spec = SpawnSpec(kind=kind, pattern="formation")
            enemies.append(self._create_enemy(spec, self._w + 10 + i * 20, base_y + i * 10))
