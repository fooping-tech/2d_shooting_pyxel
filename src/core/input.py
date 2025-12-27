from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pyxel


def _keycode(name: str) -> int:
    normalized = name.strip().upper()
    if normalized.startswith("KEY_"):
        normalized = normalized[4:]
    if normalized.startswith("GAMEPAD"):
        attr = normalized
        if hasattr(pyxel, attr):
            return int(getattr(pyxel, attr))
        raise KeyError(f"unknown gamepad name: {name}")
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
        self._bindings: dict[str, list[int]] = {}
        self._warnings: list[str] = []
        for action, key_name in mapping.items():
            codes: list[int] = []
            for spec in _iter_binding_specs(key_name):
                try:
                    codes.append(_keycode(str(spec)))
                except Exception as exc:
                    self._warnings.append(f"invalid key for {action}: {spec} ({exc})")
            if codes:
                self._bindings[action] = codes
        self.state = InputState(held={}, pressed={})

    @property
    def warnings(self) -> list[str]:
        return list(self._warnings)

    def update(self) -> None:
        held: dict[str, bool] = {}
        pressed: dict[str, bool] = {}
        for action, keys in self._bindings.items():
            held[action] = any(pyxel.btn(key) for key in keys)
            pressed[action] = any(pyxel.btnp(key) for key in keys)
        self.state = InputState(held=held, pressed=pressed)


def _iter_binding_specs(value: Any) -> Iterable[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]
