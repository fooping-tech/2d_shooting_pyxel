from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyxel


@dataclass
class StageSection:
    name: str
    distance: float
    spawn_rate: float


class Stage:
    def __init__(self, config: dict[str, Any], assets: Any) -> None:
        self._assets = assets
        stage = config.get("stage", {})
        self.scroll_speed = float(stage.get("scroll_speed", 1.2))
        self.sections: list[StageSection] = []
        for sec in stage.get("sections", []):
            self.sections.append(
                StageSection(
                    name=str(sec.get("name", "moon")),
                    distance=float(sec.get("distance", 900)),
                    spawn_rate=float(sec.get("spawn_rate", 0.06)),
                )
            )
        if not self.sections:
            self.sections = [StageSection(name="moon", distance=900, spawn_rate=0.06)]

        self.section_index = 0
        self.section_progress = 0.0
        self.scroll_x = 0.0
        self._assets.apply_theme(self.current_section().name)

    def current_section(self) -> StageSection:
        return self.sections[self.section_index]

    def update(self) -> None:
        self.scroll_x += self.scroll_speed
        self.section_progress += self.scroll_speed
        if self.section_progress >= self.current_section().distance:
            self.section_progress = 0.0
            self.section_index = (self.section_index + 1) % len(self.sections)
            self._assets.apply_theme(self.current_section().name)

    def draw_background(self, screen_w: int, screen_h: int) -> None:
        pyxel.cls(0)
        theme = self._assets.themes[self.current_section().name]
        self._draw_wrapped_tilemap(self._assets.TM_FAR, theme, screen_w, screen_h, int(self.scroll_x * 0.3))
        self._draw_wrapped_tilemap(self._assets.TM_NEAR, theme, screen_w, screen_h, int(self.scroll_x))

    def _draw_wrapped_tilemap(self, tm_id: int, theme: Any, screen_w: int, screen_h: int, offset_px: int) -> None:
        tile_size = 8
        map_w = int(theme.map_w)
        start_tile_x = (offset_px // tile_size) % map_w
        start_px = offset_px % tile_size
        tiles_w = (screen_w // tile_size) + 2
        tiles_h = (screen_h // tile_size) + 2

        sx = -start_px
        sy = 0
        pyxel.bltm(sx, sy, tm_id, start_tile_x, 0, tiles_w, tiles_h, 0)
        if start_tile_x + tiles_w > map_w:
            overflow_tiles = (start_tile_x + tiles_w) - map_w
            pyxel.bltm(sx + (map_w - start_tile_x) * tile_size, sy, tm_id, 0, 0, overflow_tiles, tiles_h, 0)
