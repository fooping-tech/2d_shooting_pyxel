# 2d_shooting_pyxel

A side-scrolling shooter built with Pyxel (Gradius-like).

## Requirements

- Python 3.x
- Pyxel

## Run

```sh
pyxel run main.py
```

## GitHub Pages (Web)

This repo deploys a browser build via GitHub Actions using `<pyxel-run>` (gamepad enabled).

1. Open `Settings -> Pages`
2. Set `Build and deployment -> Source` to `GitHub Actions`
3. Push to `main` to deploy

Build locally:

```sh
./scripts/build_pages.sh
```

Output: `site/index.html`

If the browser build doesn't start, make sure `site/` is served over HTTP (not `file://`) and that the deployed `site/` contains `src/index.html` and other directory `index.html` files (GitHub Pages needs them for Pyxel's WASM loader to fetch package directories).

## Controls

- `W/A/S/D`: Move
- `J`: Confirm / Cannon
- `K`: Missile
- `L`: Bomb
- `U`: Laser (hold to charge, release to fire; full charge = max output + lightning FX)
- `I`: Flame thrower
- `O`: Back (to Title)
- `TAB`: Toggle debug view

Gamepad (works with the on-screen virtual gamepad on iPhone):

- D-Pad: Move
- `A`: Confirm / Cannon
- `B`: Missile
- `X`: Bomb
- `Y`: Laser
- `Start`: Flame
- `Back`: Back (to Title)

## Game Rules

- Destroy enemies to increase `KILLS`
- Getting hit reduces `LIFE`; `0` = Game Over (brief invincibility after hit)
- Enemies can drop items:
  - `heal`: Heal life
  - `power`: Increase weapon level and unlock/upgrade special behaviors
  - `speed`: Increase move speed (capped)
- Stage background changes over time: `moon -> space -> planet1 -> planet2 -> ...`

## Config

Tune values in `config/game.toml`:

- Window: `window.*`
- Player: `player.*`
- Weapons: `weapons.*`
- Items: `items.*`
- Stage/Spawns: `stage.*`

## Project Layout

- `main.py`: entry point
- `src/core/`: app/input/config/assets/scene manager
- `src/scenes/`: Title / Game / GameOver
- `src/entities/`: Player / Enemy / Projectile / Item / Effects
- `src/systems/`: Stage / Spawner / Collision / DropTable
- `src/ui/`: HUD
