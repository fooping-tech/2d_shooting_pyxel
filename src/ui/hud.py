from __future__ import annotations

from typing import Any

import pyxel

from src.core.util import clamp


class HUD:
    def __init__(self, assets: Any, screen_w: int) -> None:
        self._assets = assets
        self._w = screen_w

    def draw(self, life: int, max_life: int, kills: int, weapon_level: int, speed: float) -> None:
        font = self._assets.font
        if font is None:
            return

        # LIFE bar
        font.draw(4, 2, "LIFE")
        heart = self._assets.sprites["hud:heart"]
        pyxel.blt(38, 4, heart.img, heart.u, heart.v, heart.w, heart.h, heart.colkey)

        bar_x = 46
        bar_y = 4
        bar_w = 80
        filled = int(bar_w * (life / max(1, max_life)))
        # bar segments via blt (no rect); reuse font glyph blocks as segments
        seg = self._assets.sprites.get("font:-")
        if seg is not None:
            # background
            for i in range(0, bar_w, 8):
                pyxel.blt(bar_x + i, bar_y, seg.img, seg.u, seg.v, seg.w, seg.h, seg.colkey)
            # filled
            for i in range(0, filled, 8):
                pyxel.blt(bar_x + i, bar_y + 8, seg.img, seg.u, seg.v, seg.w, seg.h, seg.colkey)

        # KILLS
        text = f"KILLS:{kills}"
        font.draw(self._w - 8 * len(text) - 4, 2, text)

        # Power / Speed (icons + numbers)
        power_icon = self._assets.sprites["hud:power"]
        speed_icon = self._assets.sprites["hud:speed"]
        px = 4
        py = 16
        pyxel.blt(px, py, power_icon.img, power_icon.u, power_icon.v, power_icon.w, power_icon.h, power_icon.colkey)
        font.draw(px + 8, py - 2, f"P:{weapon_level}")
        pyxel.blt(px + 40, py, speed_icon.img, speed_icon.u, speed_icon.v, speed_icon.w, speed_icon.h, speed_icon.colkey)
        speed_pct = int(clamp(speed / 3.2, 0.0, 9.9) * 10)
        font.draw(px + 48, py - 2, f"S:{speed_pct}")
