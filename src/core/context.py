from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

from src.core.input import Input


@dataclass
class GameContext:
    config: dict[str, Any]
    input: Input
    rng: Random
    debug_enabled: bool
    assets: Any
