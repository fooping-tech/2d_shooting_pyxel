from __future__ import annotations

from random import Random


def roll_drop(rng: Random, drop_chance: float) -> str | None:
    if rng.random() >= drop_chance:
        return None
    r = rng.random()
    if r < 0.40:
        return "heal"
    if r < 0.78:
        return "power"
    return "speed"

