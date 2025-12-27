from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyxel


def _keycode(name: str) -> int:
    normalized = name.strip().upper()
    if normalized.startswith("KEY_"):
        normalized = normalized[4:]
    attr = f"KEY_{normalized}"
    if hasattr(pyxel, attr):
        return int(getattr(pyxel, attr))
    raise KeyError(f"unknown key name: {name}")


@dataclass
class InputState:
    held: dict[str, bool]
    pressed: dict[str, bool]

    def is_held(self, action: str) -> bool:
        return bool(self.held.get(action, False))

    def is_pressed(self, action: str) -> bool:
        return bool(self.pressed.get(action, False))


class Input:
    def __init__(self, config: dict[str, Any]) -> None:
        mapping = dict(config.get("input", {}))
        self._bindings: dict[str, int] = {}
        self._warnings: list[str] = []
        for action, key_name in mapping.items():
            try:
                self._bindings[action] = _keycode(str(key_name))
            except Exception as exc:
                self._warnings.append(f"invalid key for {action}: {key_name} ({exc})")
        self.state = InputState(held={}, pressed={})

    @property
    def warnings(self) -> list[str]:
        return list(self._warnings)

    def update(self) -> None:
        held: dict[str, bool] = {}
        pressed: dict[str, bool] = {}
        for action, key in self._bindings.items():
            held[action] = pyxel.btn(key)
            pressed[action] = pyxel.btnp(key)
        self.state = InputState(held=held, pressed=pressed)
