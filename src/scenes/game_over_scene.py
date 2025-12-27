from __future__ import annotations

from typing import Callable

import pyxel

from src.core.context import GameContext


class GameOverScene:
    def __init__(self, ctx: GameContext, kills: int, on_retry: Callable[[], None], on_title: Callable[[], None]) -> None:
        self._ctx = ctx
        self._kills = kills
        self._on_retry = on_retry
        self._on_title = on_title

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def update(self) -> None:
        inp = self._ctx.input.state
        if inp.is_pressed("confirm"):
            pyxel.play(0, 1)
            self._on_retry()
        if inp.is_pressed("back"):
            pyxel.play(0, 0)
            self._on_title()

    def draw(self) -> None:
        pyxel.cls(0)
        font = self._ctx.assets.font
        if font is None:
            return
        font.draw(72, 44, "ゲームオーバー")
        font.draw(84, 68, f"ゲキハ:{self._kills}")
        font.draw(52, 104, "J:リトライ  O:タイトル")
