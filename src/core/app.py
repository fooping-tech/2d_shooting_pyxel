from __future__ import annotations

from random import Random

import pyxel

from src.core.config import load_config
from src.core.context import GameContext
from src.core.env import load_dotenv
from src.core.input import Input
from src.core.scene_manager import SceneManager


def run_app() -> None:
    _ = load_dotenv(".env")  # keep optional; app must start without it

    cfg_result = load_config("config/game.toml")
    cfg = cfg_result.data

    window = cfg.get("window", {})
    width = int(window.get("width", 256))
    height = int(window.get("height", 144))
    fps = int(window.get("fps", 60))
    title = str(window.get("title", "Side-Scrolling Shooter"))

    pyxel.init(width, height, title=title, fps=fps)

    input_system = Input(cfg)
    rng = Random()

    from src.core.assets import Assets  # local import: pyxel must be initialized

    assets = Assets(cfg)
    assets.load()

    debug_enabled = bool(cfg.get("debug", {}).get("enabled", False))
    ctx = GameContext(config=cfg, input=input_system, rng=rng, debug_enabled=debug_enabled, assets=assets)

    from src.scenes.game_over_scene import GameOverScene
    from src.scenes.game_scene import GameScene
    from src.scenes.title_scene import TitleScene

    manager = SceneManager(scene=TitleScene(ctx, on_start=lambda _ship: None))

    def go_title() -> None:
        manager.change(TitleScene(ctx, on_start=start_game))

    def start_game(selected_ship: str) -> None:
        def on_game_over(kills: int) -> None:
            manager.change(
                GameOverScene(
                    ctx,
                    kills=kills,
                    on_retry=lambda: start_game(selected_ship),
                    on_title=go_title,
                )
            )

        manager.change(GameScene(ctx, selected_ship=selected_ship, on_game_over=on_game_over))

    go_title()

    def update() -> None:
        ctx.input.update()
        if ctx.input.state.is_pressed("toggle_debug"):
            ctx.debug_enabled = not ctx.debug_enabled
        manager.update()

    def draw() -> None:
        manager.draw()

    pyxel.run(update, draw)
