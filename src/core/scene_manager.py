from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Scene(Protocol):
    def on_enter(self) -> None: ...
    def on_exit(self) -> None: ...
    def update(self) -> None: ...
    def draw(self) -> None: ...


@dataclass
class SceneManager:
    scene: Scene

    def change(self, next_scene: Scene) -> None:
        self.scene.on_exit()
        self.scene = next_scene
        self.scene.on_enter()

    def update(self) -> None:
        self.scene.update()

    def draw(self) -> None:
        self.scene.draw()
