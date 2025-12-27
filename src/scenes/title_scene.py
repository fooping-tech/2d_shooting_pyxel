from __future__ import annotations

from typing import Callable

import pyxel

from src.core.context import GameContext


class TitleScene:
    def __init__(self, ctx: GameContext, on_start: Callable[[str], None]) -> None:
        self._ctx = ctx
        self._on_start = on_start
        self._ships = ["propeller", "jet", "fighter", "ufo"]
        self._idx = 0

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def update(self) -> None:
        inp = self._ctx.input.state
        if inp.is_pressed("left"):
            self._idx = (self._idx - 1) % len(self._ships)
            pyxel.play(0, 0)
        if inp.is_pressed("right"):
            self._idx = (self._idx + 1) % len(self._ships)
            pyxel.play(0, 0)
        if inp.is_pressed("confirm"):
            pyxel.play(0, 1)
            self._on_start(self._ships[self._idx])

    def draw(self) -> None:
        pyxel.cls(0)
        font = self._ctx.assets.font
        if font is None:
            return
        font.draw(52, 16, "SIDE-SCROLL SHOOTER")
        font.draw(84, 36, "SELECT SHIP")

        font.draw(60, 90, "J:START  K:MISSILE")
        font.draw(36, 102, "L:BOMB  U:LASER  I:FLAME")

        font.draw(44, 122, "WASD:MOVE  A/D:SELECT")
        font.draw(24, 134, "GAMEPAD:DPAD MOVE  A START")
        ship = self._ships[self._idx]
        font.draw(88, 60, ship.upper())
        sp = self._ctx.assets.sprites[f"ship:{ship}"]
        pyxel.blt(120, 58, sp.img, sp.u, sp.v, sp.w, sp.h, sp.colkey)
