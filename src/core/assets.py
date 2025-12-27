from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyxel


@dataclass(frozen=True)
class Sprite:
    img: int
    u: int
    v: int
    w: int
    h: int
    colkey: int = 0


@dataclass(frozen=True)
class ThemeTiles:
    far: list[list[int]]
    near: list[list[int]]
    map_w: int
    map_h: int


class SpriteFont:
    def __init__(self, sprite_map: dict[str, Sprite], glyph_w: int = 8) -> None:
        self._sprite_map = sprite_map
        self._glyph_w = glyph_w

    def draw(self, x: int, y: int, text: str) -> None:
        cx = x
        for ch in text:
            sprite = self._sprite_map.get(ch.upper(), self._sprite_map.get("?", None))
            if sprite is not None:
                pyxel.blt(cx, y, sprite.img, sprite.u, sprite.v, sprite.w, sprite.h, sprite.colkey)
            cx += self._glyph_w


class Assets:
    IMG_SPRITES = 0
    IMG_FONT = 1
    IMG_TILES = 2

    TM_FAR = 0
    TM_NEAR = 1

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.sprites: dict[str, Sprite] = {}
        self.font: SpriteFont | None = None
        self.themes: dict[str, ThemeTiles] = {}

    def load(self) -> None:
        pyxel.images[self.IMG_SPRITES].cls(0)
        pyxel.images[self.IMG_FONT].cls(0)
        pyxel.images[self.IMG_TILES].cls(0)

        self._build_sprites()
        self._build_font()
        self._build_tiles_and_themes()
        self._build_sounds()

    def apply_theme(self, name: str) -> None:
        theme = self.themes.get(name)
        if theme is None:
            theme = next(iter(self.themes.values()))
        far_tm = pyxel.tilemaps[self.TM_FAR]
        near_tm = pyxel.tilemaps[self.TM_NEAR]
        far_tm.imgsrc = self.IMG_TILES
        near_tm.imgsrc = self.IMG_TILES

        # Tilemap.set() signature differs by Pyxel version; use pset for portability.
        for y, row in enumerate(theme.far):
            for x, tile in enumerate(row):
                far_tm.pset(x, y, tile)
        for y, row in enumerate(theme.near):
            for x, tile in enumerate(row):
                near_tm.pset(x, y, tile)

    def _build_sprites(self) -> None:
        img = pyxel.images[self.IMG_SPRITES]

        def put(u: int, v: int, pattern: list[str], color: int) -> None:
            for y, row in enumerate(pattern):
                for x, ch in enumerate(row):
                    if ch != " ":
                        img.pset(u + x, v + y, color)

        ships = {
            "propeller": (0, 0, 11),
            "jet": (16, 0, 12),
            "fighter": (32, 0, 8),
            "ufo": (48, 0, 10),
        }
        for name, (u0, v0, col) in ships.items():
            pattern = [
                "     **        ",
                "    ****       ",
                "   ******      ",
                "***********    ",
                "************** ",
                "***********    ",
                "   ******      ",
                "    ****       ",
                "     **        ",
                "               ",
                "   *      *    ",
                "    *    *     ",
                "     *  *      ",
                "      **       ",
                "               ",
                "               ",
            ]
            put(u0, v0, pattern, col)
            self.sprites[f"ship:{name}"] = Sprite(self.IMG_SPRITES, u0, v0, 16, 16, 0)

        # Enemies
        enemy_defs = {
            "drone": (0, 24, 2),
            "fighter": (16, 24, 3),
            "turret": (32, 24, 5),
        }
        for name, (u0, v0, col) in enemy_defs.items():
            pattern = [
                "    ****    ",
                "   ******   ",
                "************",
                "************",
                "************",
                "  ********  ",
                "   ******   ",
                "    ****    ",
            ]
            put(u0, v0, pattern, col)
            self.sprites[f"enemy:{name}"] = Sprite(self.IMG_SPRITES, u0, v0, 12, 8, 0)

        # Projectiles
        put(0, 40, ["**", "**"], 7)
        self.sprites["shot:cannon"] = Sprite(self.IMG_SPRITES, 0, 40, 2, 2, 0)

        put(8, 40, [" ** ", "****", " ** "], 14)
        self.sprites["shot:missile"] = Sprite(self.IMG_SPRITES, 8, 40, 4, 3, 0)

        put(
            16,
            40,
            [
                "  ****  ",
                " ****** ",
                "********",
                "********",
                "********",
                "********",
                " ****** ",
                "  ****  ",
            ],
            9,
        )
        self.sprites["shot:bomb"] = Sprite(self.IMG_SPRITES, 16, 40, 8, 8, 0)

        put(24, 40, ["********"], 11)
        self.sprites["shot:laser_seg"] = Sprite(self.IMG_SPRITES, 24, 40, 8, 1, 0)

        # Lightning variants (overlay)
        put(24, 41, ["** ** **"], 7)
        self.sprites["shot:laser_fx_a"] = Sprite(self.IMG_SPRITES, 24, 41, 8, 1, 0)
        put(24, 42, ["* ***** "], 10)
        self.sprites["shot:laser_fx_b"] = Sprite(self.IMG_SPRITES, 24, 42, 8, 1, 0)
        put(32, 40, [" *  ", "*** ", " *  "], 7)
        self.sprites["shot:laser_branch"] = Sprite(self.IMG_SPRITES, 32, 40, 4, 3, 0)

        # Flame segments (8x8)
        put(
            40,
            40,
            [
                "   **   ",
                "  ****  ",
                " ****** ",
                "********",
                " ****** ",
                "  ****  ",
                "   **   ",
                "        ",
            ],
            10,
        )
        self.sprites["shot:flame_a"] = Sprite(self.IMG_SPRITES, 40, 40, 8, 8, 0)
        put(
            48,
            40,
            [
                "        ",
                "   **   ",
                "  ****  ",
                " ****** ",
                "********",
                " ****** ",
                "  ****  ",
                "   **   ",
            ],
            9,
        )
        self.sprites["shot:flame_b"] = Sprite(self.IMG_SPRITES, 48, 40, 8, 8, 0)

        # Blue flame (max charge)
        put(
            56,
            40,
            [
                "   **   ",
                "  ****  ",
                " ****** ",
                "********",
                " ****** ",
                "  ****  ",
                "   **   ",
                "        ",
            ],
            12,
        )
        self.sprites["shot:flame_blue_a"] = Sprite(self.IMG_SPRITES, 56, 40, 8, 8, 0)
        put(
            64,
            40,
            [
                "        ",
                "   **   ",
                "  ****  ",
                " ****** ",
                "********",
                " ****** ",
                "  ****  ",
                "   **   ",
            ],
            6,
        )
        self.sprites["shot:flame_blue_b"] = Sprite(self.IMG_SPRITES, 64, 40, 8, 8, 0)

        # Items
        put(0, 48, [" ** ", "****", "****", " ** "], 8)
        self.sprites["item:heal"] = Sprite(self.IMG_SPRITES, 0, 48, 4, 4, 0)
        put(8, 48, ["****", "*  *", "*  *", "****"], 10)
        self.sprites["item:power"] = Sprite(self.IMG_SPRITES, 8, 48, 4, 4, 0)
        put(16, 48, [" ** ", "*** ", " ** ", " ***"], 12)
        self.sprites["item:speed"] = Sprite(self.IMG_SPRITES, 16, 48, 4, 4, 0)

        # HUD icons
        put(0, 56, [" ** ", "****", "****", " ** "], 8)
        self.sprites["hud:heart"] = Sprite(self.IMG_SPRITES, 0, 56, 4, 4, 0)
        put(8, 56, ["****", "* **", "** *", "****"], 10)
        self.sprites["hud:power"] = Sprite(self.IMG_SPRITES, 8, 56, 4, 4, 0)
        put(16, 56, [" ** ", "*** ", " ** ", " ***"], 12)
        self.sprites["hud:speed"] = Sprite(self.IMG_SPRITES, 16, 56, 4, 4, 0)

        # Effects
        put(0, 64, [" ** ", "****", "****", " ** "], 7)
        self.sprites["fx:explosion"] = Sprite(self.IMG_SPRITES, 0, 64, 4, 4, 0)

        # UI arrows (8x8)
        put(64, 0, ["   *   ", "  ***  ", " ***** ", "   *   ", "   *   ", "   *   ", "       ", "       "], 7)
        self.sprites["ui:up"] = Sprite(self.IMG_SPRITES, 64, 0, 8, 8, 0)
        put(72, 0, ["   *   ", "   *   ", "   *   ", " ***** ", "  ***  ", "   *   ", "       ", "       "], 7)
        self.sprites["ui:down"] = Sprite(self.IMG_SPRITES, 72, 0, 8, 8, 0)
        put(64, 8, ["   *   ", "  **   ", " ***** ", "*******", " ***** ", "  **   ", "   *   ", "       "], 7)
        self.sprites["ui:left"] = Sprite(self.IMG_SPRITES, 64, 8, 8, 8, 0)
        put(72, 8, ["   *   ", "   **  ", " ***** ", "*******", " ***** ", "   **  ", "   *   ", "       "], 7)
        self.sprites["ui:right"] = Sprite(self.IMG_SPRITES, 72, 8, 8, 8, 0)

    def _build_font(self) -> None:
        img = pyxel.images[self.IMG_FONT]

        glyphs: dict[str, list[str]] = {
            " ": ["     ", "     ", "     ", "     ", "     ", "     ", "     "],
            "?": ["*****", "   **", "  ** ", " **  ", "     ", " **  ", "     "],
            "-": ["     ", "     ", "     ", "*****", "     ", "     ", "     "],
            ":": ["     ", "  ** ", "  ** ", "     ", "  ** ", "  ** ", "     "],
            ".": ["     ", "     ", "     ", "     ", "     ", " **  ", " **  "],
            "!": [" **  ", " **  ", " **  ", " **  ", " **  ", "     ", " **  "],
            "/": ["    *", "   * ", "  *  ", " *   ", "*    ", "     ", "     "],
            "0": ["*****", "**  *", "**  *", "**  *", "*  **", "*  **", "*****"],
            "1": ["  ** ", " *** ", "  ** ", "  ** ", "  ** ", "  ** ", "*****"],
            "2": ["*****", "    *", "    *", "*****", "*    ", "*    ", "*****"],
            "3": ["*****", "    *", "    *", "*****", "    *", "    *", "*****"],
            "4": ["*   *", "*   *", "*   *", "*****", "    *", "    *", "    *"],
            "5": ["*****", "*    ", "*    ", "*****", "    *", "    *", "*****"],
            "6": ["*****", "*    ", "*    ", "*****", "*   *", "*   *", "*****"],
            "7": ["*****", "    *", "   * ", "  *  ", " *   ", " *   ", " *   "],
            "8": ["*****", "*   *", "*   *", "*****", "*   *", "*   *", "*****"],
            "9": ["*****", "*   *", "*   *", "*****", "    *", "    *", "*****"],
            "A": [" *** ", "*   *", "*   *", "*****", "*   *", "*   *", "*   *"],
            "B": ["**** ", "*   *", "*   *", "**** ", "*   *", "*   *", "**** "],
            "C": [" ****", "*    ", "*    ", "*    ", "*    ", "*    ", " ****"],
            "D": ["**** ", "*   *", "*   *", "*   *", "*   *", "*   *", "**** "],
            "E": ["*****", "*    ", "*    ", "**** ", "*    ", "*    ", "*****"],
            "F": ["*****", "*    ", "*    ", "**** ", "*    ", "*    ", "*    "],
            "G": [" ****", "*    ", "*    ", "* ***", "*   *", "*   *", " ****"],
            "H": ["*   *", "*   *", "*   *", "*****", "*   *", "*   *", "*   *"],
            "I": ["*****", "  ** ", "  ** ", "  ** ", "  ** ", "  ** ", "*****"],
            "J": ["*****", "    *", "    *", "    *", "*   *", "*   *", " *** "],
            "K": ["*   *", "*  * ", "* *  ", "**   ", "* *  ", "*  * ", "*   *"],
            "L": ["*    ", "*    ", "*    ", "*    ", "*    ", "*    ", "*****"],
            "M": ["*   *", "** **", "* * *", "*   *", "*   *", "*   *", "*   *"],
            "N": ["*   *", "**  *", "* * *", "*  **", "*   *", "*   *", "*   *"],
            "O": [" *** ", "*   *", "*   *", "*   *", "*   *", "*   *", " *** "],
            "P": ["**** ", "*   *", "*   *", "**** ", "*    ", "*    ", "*    "],
            "Q": [" *** ", "*   *", "*   *", "*   *", "* * *", "*  * ", " ** *"],
            "R": ["**** ", "*   *", "*   *", "**** ", "* *  ", "*  * ", "*   *"],
            "S": [" ****", "*    ", "*    ", " *** ", "    *", "    *", "**** "],
            "T": ["*****", "  ** ", "  ** ", "  ** ", "  ** ", "  ** ", "  ** "],
            "U": ["*   *", "*   *", "*   *", "*   *", "*   *", "*   *", " *** "],
            "V": ["*   *", "*   *", "*   *", "*   *", " * * ", " * * ", "  *  "],
            "W": ["*   *", "*   *", "*   *", "* * *", "* * *", "** **", "*   *"],
            "X": ["*   *", " * * ", "  *  ", "  *  ", "  *  ", " * * ", "*   *"],
            "Y": ["*   *", " * * ", "  *  ", "  *  ", "  *  ", "  *  ", "  *  "],
            "Z": ["*****", "    *", "   * ", "  *  ", " *   ", "*    ", "*****"],
        }

        sprite_map: dict[str, Sprite] = {}
        cell_w = 8
        cell_h = 8

        def draw_glyph(u0: int, v0: int, rows: list[str]) -> None:
            for y, row in enumerate(rows):
                for x, ch in enumerate(row):
                    if ch == "*":
                        img.pset(u0 + x + 1, v0 + y + 1, 7)

        chars = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            " -:./!?"
        )
        cols = 16
        for idx, ch in enumerate(chars):
            u0 = (idx % cols) * cell_w
            v0 = (idx // cols) * cell_h
            draw_glyph(u0, v0, glyphs.get(ch, glyphs["?"]))
            sprite_map[ch] = Sprite(self.IMG_FONT, u0, v0, cell_w, cell_h, 0)
        sprite_map["?"] = sprite_map["?"]

        self.font = SpriteFont(sprite_map, glyph_w=cell_w)
        self.sprites.update({f"font:{k}": v for k, v in sprite_map.items()})

    def _build_sounds(self) -> None:
        # Simple 1-channel SFX; keep it lightweight.
        # 0: cursor, 1: start, 2: cannon, 3: missile, 4: bomb, 5: laser, 6: explosion, 7: item, 8: gameover
        # 9-14: laser_charge (low -> high pitch)
        pyxel.sounds[0].set("c3", "p", "6", "n", 10)
        pyxel.sounds[1].set("c3 e3 g3 c4", "t", "6644", "n", 12)
        pyxel.sounds[2].set("g4", "p", "7", "n", 8)
        pyxel.sounds[3].set("c4 d4 e4", "t", "665", "n", 16)
        pyxel.sounds[4].set("a3", "n", "6", "n", 14)
        pyxel.sounds[5].set("c4 c4 c4 c4", "s", "4444", "n", 6)
        pyxel.sounds[6].set("c2 c1", "n", "76", "f", 8)
        pyxel.sounds[7].set("e4 g4", "t", "66", "n", 12)
        pyxel.sounds[8].set("c3 b2 a2", "t", "654", "n", 22)
        pyxel.sounds[9].set("c2", "s", "2", "n", 4)
        pyxel.sounds[10].set("d2", "s", "2", "n", 4)
        pyxel.sounds[11].set("e2", "s", "2", "n", 4)
        pyxel.sounds[12].set("g2", "s", "2", "n", 4)
        pyxel.sounds[13].set("a2", "s", "2", "n", 4)
        pyxel.sounds[14].set("c3", "s", "2", "n", 4)
        # flame loop
        pyxel.sounds[15].set("a2 g2 a2 g2", "n", "2222", "n", 6)

    def _build_tiles_and_themes(self) -> None:
        img = pyxel.images[self.IMG_TILES]
        img.cls(0)

        def tile(u: int, v: int, pattern: list[str], color: int) -> None:
            for y, row in enumerate(pattern):
                for x, ch in enumerate(row):
                    if ch != " ":
                        img.pset(u + x, v + y, color)

        # Tiles are 8x8, index = (u//8, v//8)
        # 0,0 is empty (transparent background tile)
        tile(8, 0, ["  **  ", " **** ", "******", "******", "******", "******", " **** ", "  **  "], 7)  # star
        tile(16, 0, ["********", "********", "********", "********", "********", "********", "********", "********"], 6)  # moon ground
        tile(24, 0, ["********", "********", "********", "********", "********", "********", "********", "********"], 1)  # space dark
        tile(32, 0, ["********", "********", "********", "********", "********", "********", "********", "********"], 4)  # planet soil
        tile(40, 0, ["   **   ", "  ****  ", " ****** ", "********", "********", " ****** ", "  ****  ", "   **   "], 13)  # planet dot

        def tile_uv(u: int, v: int) -> tuple[int, int]:
            return (u // 8, v // 8)

        star = tile_uv(8, 0)
        moon = tile_uv(16, 0)
        space = tile_uv(24, 0)
        soil = tile_uv(32, 0)
        planet = tile_uv(40, 0)
        empty = (0, 0)

        map_w = 64
        map_h = 32

        def empty_map(fill: tuple[int, int]) -> list[list[tuple[int, int]]]:
            return [[fill for _ in range(map_w)] for _ in range(map_h)]

        def sprinkle_stars(m: list[list[tuple[int, int]]], density: int) -> None:
            # deterministic pattern; no RNG here (assets step)
            for y in range(map_h):
                for x in range(map_w):
                    if (x * 13 + y * 7) % density == 0:
                        m[y][x] = star

        themes: dict[str, ThemeTiles] = {}

        # Moon: stars + ground band
        far = empty_map(space)
        sprinkle_stars(far, density=23)
        near = empty_map(empty)
        for y in range(map_h - 4, map_h):
            for x in range(map_w):
                near[y][x] = moon
        themes["moon"] = ThemeTiles(far=far, near=near, map_w=map_w, map_h=map_h)

        # Space: dense stars, no ground
        far = empty_map(space)
        sprinkle_stars(far, density=17)
        near = empty_map(empty)
        for y in range(3, map_h, 9):
            for x in range(5, map_w, 11):
                near[y][x] = planet
        themes["space"] = ThemeTiles(far=far, near=near, map_w=map_w, map_h=map_h)

        # Planet1: stars + soil band + planet dots
        far = empty_map(space)
        sprinkle_stars(far, density=29)
        near = empty_map(empty)
        for y in range(map_h - 5, map_h):
            for x in range(map_w):
                near[y][x] = soil
        for y in range(map_h - 12, map_h - 6):
            for x in range(4, map_w, 13):
                near[y][x] = planet
        themes["planet1"] = ThemeTiles(far=far, near=near, map_w=map_w, map_h=map_h)

        # Planet2: different density
        far = empty_map(space)
        sprinkle_stars(far, density=19)
        near = empty_map(empty)
        for y in range(map_h - 6, map_h):
            for x in range(map_w):
                near[y][x] = soil
        for y in range(map_h - 14, map_h - 7):
            for x in range(7, map_w, 9):
                near[y][x] = planet
        themes["planet2"] = ThemeTiles(far=far, near=near, map_w=map_w, map_h=map_h)

        self.themes = themes
        self.apply_theme(next(iter(themes.keys())))
