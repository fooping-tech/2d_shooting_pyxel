from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def default_config() -> dict[str, Any]:
    return {
        "window": {"width": 256, "height": 144, "fps": 60, "title": "Side-Scrolling Shooter"},
        "debug": {"enabled": False},
        "input": {
            "up": ["W", "UP", "GAMEPAD1_BUTTON_DPAD_UP"],
            "down": ["S", "DOWN", "GAMEPAD1_BUTTON_DPAD_DOWN"],
            "left": ["A", "LEFT", "GAMEPAD1_BUTTON_DPAD_LEFT"],
            "right": ["D", "RIGHT", "GAMEPAD1_BUTTON_DPAD_RIGHT"],
            "confirm": ["J", "Z", "GAMEPAD1_BUTTON_A"],
            "back": ["O", "X", "GAMEPAD1_BUTTON_BACK"],
            "pause": "RETURN",
            "fire_cannon": ["J", "Z", "GAMEPAD1_BUTTON_A"],
            "fire_missile": ["K", "X", "GAMEPAD1_BUTTON_B"],
            "fire_bomb": ["L", "C", "GAMEPAD1_BUTTON_X"],
            "fire_laser": ["U", "V", "GAMEPAD1_BUTTON_Y"],
            "fire_flame": ["I", "B", "GAMEPAD1_BUTTON_START"],
            "toggle_debug": "TAB",
        },
        "player": {"max_life": 100, "invincible_frames": 60, "base_speed": 1.6, "max_speed": 3.2},
        "weapons": {
            "max_level": 50,
            "cannon": {"cooldown_frames": 8, "damage": 1, "speed": 4.0},
            "missile": {
                "cooldown_frames": 18,
                "cooldown_reduction_per_level": 2,
                "min_cooldown_frames": 8,
                "damage": 2,
                "speed": 3.0,
                "turn_rate": 0.12,
            },
            "bomb": {
                "cooldown_frames": 28,
                "damage": 3,
                "speed": 2.4,
                "radius": 18,
                "radius_increase_per_level": 3,
                "max_radius": 36,
                "homing_turn_rate": 0.10,
            },
            "laser": {
                "cooldown_frames": 40,
                "damage": 1,
                "max_damage": 8,
                "beam_length": 140,
                "beam_length_increase_per_level": 10,
                "max_beam_length": 220,
                "beam_width": 4,
                "beam_width_increase_per_level": 1,
                "max_beam_width": 10,
                "tick_interval_frames": 6,
                "charge_max_frames": 45,
                "charge_bonus_length": 80,
                "charge_bonus_width": 6,
                "charge_bonus_duration": 22,
            },
            "flame": {
                "range": 70,
                "width": 16,
                "damage": 1,
                "tick_interval_frames": 3,
                "charge_max_frames": 45,
                "max_range": 140,
                "max_width": 28,
                "upgrade_base_bonus_range": 20,
                "upgrade_base_bonus_width": 6,
                "upgrade_base_bonus_damage": 0,
                "burn": {
                    "duration_frames": 120,
                    "damage": 1,
                    "tick_interval_frames": 10,
                    "spread_radius": 22,
                    "speed_multiplier": 0.55,
                },
            },
        },
        "items": {"drop_chance": 0.22, "heal_amount": 25, "power_amount": 1, "speed_amount": 0.2},
        "stage": {
            "scroll_speed": 1.2,
            "sections": [
                {"name": "moon", "distance": 900, "spawn_rate": 0.06},
                {"name": "space", "distance": 900, "spawn_rate": 0.08},
                {"name": "planet1", "distance": 900, "spawn_rate": 0.10},
                {"name": "planet2", "distance": 900, "spawn_rate": 0.12},
            ],
        },
    }


@dataclass(frozen=True)
class ConfigResult:
    data: dict[str, Any]
    loaded_from: Path | None
    warnings: list[str]


def _strip_toml_comment(line: str) -> str:
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i]
    return line


def _parse_toml_value(raw: str) -> Any:
    s = raw.strip()
    if not s:
        return ""
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    # very small subset: arrays of scalars
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        parts: list[str] = []
        buf = ""
        in_single = False
        in_double = False
        for ch in inner:
            if ch == "'" and not in_double:
                in_single = not in_single
                buf += ch
            elif ch == '"' and not in_single:
                in_double = not in_double
                buf += ch
            elif ch == "," and not in_single and not in_double:
                parts.append(buf.strip())
                buf = ""
            else:
                buf += ch
        if buf.strip():
            parts.append(buf.strip())
        return [_parse_toml_value(p) for p in parts]
    try:
        if "." in s or "e" in low:
            return float(s)
        return int(s, 10)
    except Exception:
        return s


def _ensure_table(root: dict[str, Any], path: list[str]) -> dict[str, Any]:
    cur: dict[str, Any] = root
    for key in path:
        nxt = cur.get(key)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[key] = nxt
        cur = nxt
    return cur


def _ensure_array_table(root: dict[str, Any], path: list[str]) -> dict[str, Any]:
    if not path:
        raise ValueError("empty array-of-table path")
    parent = _ensure_table(root, path[:-1])
    key = path[-1]
    arr = parent.get(key)
    if not isinstance(arr, list):
        arr = []
        parent[key] = arr
    entry: dict[str, Any] = {}
    arr.append(entry)
    return entry


def parse_toml_minimal(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current: dict[str, Any] = root
    for raw_line in text.splitlines():
        line = _strip_toml_comment(raw_line).strip()
        if not line:
            continue
        if line.startswith("[[") and line.endswith("]]"):
            header = line[2:-2].strip()
            path = [p.strip() for p in header.split(".") if p.strip()]
            current = _ensure_array_table(root, path)
            continue
        if line.startswith("[") and line.endswith("]"):
            header = line[1:-1].strip()
            path = [p.strip() for p in header.split(".") if p.strip()]
            current = _ensure_table(root, path)
            continue
        if "=" not in line:
            continue
        key_raw, value_raw = line.split("=", 1)
        key = key_raw.strip()
        value = _parse_toml_value(value_raw)
        if "." in key:
            _ensure_table(current, key.split(".")[:-1])[key.split(".")[-1]] = value
        else:
            current[key] = value
    return root


def load_config(path: str | Path = "config/game.toml") -> ConfigResult:
    cfg_path = Path(path)
    defaults = default_config()
    if not cfg_path.exists():
        return ConfigResult(data=defaults, loaded_from=None, warnings=[f"config not found: {cfg_path}"])

    try:
        loaded = parse_toml_minimal(cfg_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            return ConfigResult(data=defaults, loaded_from=None, warnings=["invalid config; using defaults"])
        merged = _deep_merge(defaults, loaded)
        return ConfigResult(data=merged, loaded_from=cfg_path, warnings=[])
    except Exception as exc:
        return ConfigResult(data=defaults, loaded_from=None, warnings=[f"failed to load config; using defaults: {exc}"])
