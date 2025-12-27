from __future__ import annotations

from typing import Any, Callable

import pyxel

from src.core.context import GameContext
from src.core.types import Vec2
from src.core.util import lerp
from src.entities.effects import Particle
from src.entities.enemy import Enemy
from src.entities.item import Item
from src.entities.player import Player
from src.entities.projectile import FlameStream, LaserBeam, Projectile
from src.systems.collision import aabb
from src.systems.drop_table import roll_drop
from src.systems.spawner import Spawner
from src.systems.stage import Stage
from src.ui.hud import HUD


class GameScene:
    def __init__(self, ctx: GameContext, selected_ship: str, on_game_over: Callable[[int], None]) -> None:
        self._ctx = ctx
        self._on_game_over = on_game_over
        window = ctx.config.get("window", {})
        self._w = int(window.get("width", 256))
        self._h = int(window.get("height", 144))

        self.stage = Stage(ctx.config, ctx.assets)
        self.player = Player.from_config(ctx.config, ship=selected_ship, start_x=24, start_y=self._h // 2 - 8)
        self.kills = 0

        self.enemies: list[Enemy] = []
        self.items: list[Item] = []
        self.spawner = Spawner(ctx.rng, self._w, self._h)
        self.hud = HUD(ctx.assets, self._w)

        self.projectiles: list[Projectile] = [
            Projectile(
                active=False,
                kind="cannon",
                owner="player",
                pos=Vec2(0.0, 0.0),
                vel=Vec2(0.0, 0.0),
                w=2,
                h=2,
                damage=1,
                lifetime=0,
            )
            for _ in range(128)
        ]
        self.enemy_shots: list[Projectile] = [
            Projectile(
                active=False,
                kind="enemy",
                owner="enemy",
                pos=Vec2(0.0, 0.0),
                vel=Vec2(0.0, 0.0),
                w=2,
                h=2,
                damage=10,
                lifetime=0,
            )
            for _ in range(64)
        ]
        self.laser = LaserBeam(
            active=False,
            x=0.0,
            y=0.0,
            length=int(ctx.config.get("weapons", {}).get("laser", {}).get("beam_length", 140)),
            width=int(ctx.config.get("weapons", {}).get("laser", {}).get("beam_width", 4)),
            damage=int(ctx.config.get("weapons", {}).get("laser", {}).get("damage", 1)),
            duration=0,
            tick_interval=int(ctx.config.get("weapons", {}).get("laser", {}).get("tick_interval_frames", 6)),
        )
        flame_cfg = ctx.config.get("weapons", {}).get("flame", {})
        self.flame = FlameStream(
            active=False,
            x=0.0,
            y=0.0,
            length=int(flame_cfg.get("range", 70)),
            width=int(flame_cfg.get("width", 16)),
            damage=int(flame_cfg.get("damage", 1)),
            tick_interval=int(flame_cfg.get("tick_interval_frames", 3)),
        )
        self.particles: list[Particle] = [
            Particle(active=False, pos=Vec2(0.0, 0.0), vel=Vec2(0.0, 0.0), lifetime=0) for _ in range(160)
        ]
        self._cleanup_tick = 0
        self._laser_charging = False
        self._laser_charge_frames = 0
        self._laser_fx: list[tuple[int, int, int]] = []  # (dy, variant, branch_dir)
        self._laser_fx_refresh = 0
        self._laser_charge_sfx_timer = 0
        self._flame_fx: list[tuple[int, int]] = []  # (dy, variant)
        self._flame_fx_refresh = 0
        self._flame_charge_frames = 0

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pyxel.stop(1)
        pyxel.stop(2)

    def update(self) -> None:
        inp = self._ctx.input.state
        self.player.step_cooldowns()
        self.stage.update()

        # Move player
        dx = (1 if inp.is_held("right") else 0) - (1 if inp.is_held("left") else 0)
        dy = (1 if inp.is_held("down") else 0) - (1 if inp.is_held("up") else 0)
        self.player.pos.x = float(self.player.pos.x + dx * self.player.speed)
        self.player.pos.y = float(self.player.pos.y + dy * self.player.speed)
        self.player.pos.x = float(max(0, min(self._w - self.player.w, self.player.pos.x)))
        self.player.pos.y = float(max(0, min(self._h - self.player.h, self.player.pos.y)))

        # Spawn enemies
        self.spawner.update(self.stage.current_section().spawn_rate, self.enemies, self.stage.current_section().name)

        # Shooting
        self._update_player_shooting(inp)

        # Update enemies
        self._update_enemies()

        # Update projectiles
        self._update_projectiles()

        # Laser
        self._update_laser()
        self._update_flame()
        self._update_burning()

        # Update items
        self._update_items()

        # Update particles
        self._update_particles()

        # Collisions
        self._handle_collisions()

        self._cleanup_tick += 1
        if self._cleanup_tick >= 45:
            self._cleanup_tick = 0
            self.enemies = [e for e in self.enemies if e.active]
            self.items = [it for it in self.items if it.active]

        if self.player.life <= 0:
            pyxel.play(0, 8)
            self._on_game_over(self.kills)

    def draw(self) -> None:
        self.stage.draw_background(self._w, self._h)
        self._draw_entities()
        self.hud.draw(self.player.life, self.player.max_life, self.kills, self.player.weapon_level, self.player.speed)
        if self._ctx.debug_enabled:
            # Debug only: simple outlines using Pyxel primitives are allowed
            pr = self.player.rect()
            pyxel.rectb(int(pr.x), int(pr.y), int(pr.w), int(pr.h), 8)

    def _update_player_shooting(self, inp: Any) -> None:
        weapons = self._ctx.config.get("weapons", {})
        level = self.player.weapon_level

        if inp.is_held("fire_cannon") and self.player.cooldown_cannon == 0:
            cannon = weapons.get("cannon", {})
            cooldown = int(cannon.get("cooldown_frames", 8))
            speed = float(cannon.get("speed", 4.0))
            damage = int(cannon.get("damage", 1))
            self.player.cooldown_cannon = max(1, cooldown - (level - 1))
            pyxel.play(0, 2)
            for i in range(min(1 + (level - 1) // 2, 3)):
                dy = (-1 + i) * 1.2 if i > 0 else 0.0
                self._spawn_projectile(
                    kind="cannon",
                    owner="player",
                    x=self.player.pos.x + 14,
                    y=self.player.pos.y + 7 + dy,
                    vx=speed,
                    vy=dy * 0.3,
                    w=2,
                    h=2,
                    damage=damage,
                    lifetime=60,
                )

        if inp.is_held("fire_missile") and self.player.cooldown_missile == 0:
            missile = weapons.get("missile", {})
            base_cd = int(missile.get("cooldown_frames", 18))
            reduction = int(missile.get("cooldown_reduction_per_level", 2))
            min_cd = int(missile.get("min_cooldown_frames", 8))
            self.player.cooldown_missile = max(min_cd, base_cd - (level - 1) * reduction)
            pyxel.play(0, 3)
            self._spawn_projectile(
                kind="missile",
                owner="player",
                x=self.player.pos.x + 10,
                y=self.player.pos.y + 12,
                vx=float(missile.get("speed", 3.0)),
                vy=0.0,
                w=4,
                h=3,
                damage=int(missile.get("damage", 2)) + (level - 1) // 2,
                lifetime=120,
            )

        if inp.is_held("fire_bomb") and self.player.cooldown_bomb == 0:
            bomb = weapons.get("bomb", {})
            self.player.cooldown_bomb = int(bomb.get("cooldown_frames", 28))
            pyxel.play(0, 4)
            base_radius = int(bomb.get("radius", 18))
            radius_inc = int(bomb.get("radius_increase_per_level", 3))
            max_radius = int(bomb.get("max_radius", 36))
            if self.player.bomb_radius_maxed:
                radius = max_radius
            else:
                radius = min(max_radius, base_radius + (level - 1) * radius_inc)
            size = 8 if self.player.bomb_big else 4
            self._spawn_projectile(
                kind="bomb",
                owner="player",
                x=self.player.pos.x + 10,
                y=self.player.pos.y + 12,
                vx=float(bomb.get("speed", 2.4)),
                vy=1.0,
                w=size,
                h=size,
                damage=int(bomb.get("damage", 3)) + (level - 1) // 2,
                lifetime=90,
                radius=radius,
            )

        laser_held = bool(inp.is_held("fire_laser"))
        if not self.laser.active and self.player.cooldown_laser == 0:
            if laser_held:
                if not self._laser_charging:
                    self._laser_charging = True
                    self._laser_charge_frames = 0
                    self._laser_charge_sfx_timer = 0
                laser_cfg = weapons.get("laser", {})
                max_frames = int(laser_cfg.get("charge_max_frames", 45))
                self._laser_charge_frames = min(max_frames, self._laser_charge_frames + 1)
                self._laser_charge_sfx_timer = max(0, self._laser_charge_sfx_timer - 1)
                if self._laser_charge_sfx_timer == 0:
                    ratio = self._laser_charge_frames / max(1, max_frames)
                    tier_count = 6
                    tier = min(tier_count - 1, int(ratio * (tier_count - 1)))
                    pyxel.play(1, 9 + tier)
                    self._laser_charge_sfx_timer = int(lerp(10, 3, ratio))
            elif self._laser_charging:
                pyxel.stop(1)
                self._fire_laser(level)
                self._laser_charging = False
                self._laser_charge_frames = 0
                self._laser_charge_sfx_timer = 0
        else:
            # Cancel charge if laser can't be fired right now.
            if self._laser_charging:
                pyxel.stop(1)
            self._laser_charging = False
            self._laser_charge_frames = 0
            self._laser_charge_sfx_timer = 0

        # Flame thrower (B)
        flame_held = bool(inp.is_held("fire_flame"))
        if flame_held and not self.laser.active:
            if not self.flame.active:
                self.flame.active = True
                pyxel.play(2, 15, loop=True)
            flame_cfg = weapons.get("flame", {})
            base_len = int(flame_cfg.get("range", 70))
            base_w = int(flame_cfg.get("width", 16))
            base_damage = int(flame_cfg.get("damage", 1))

            max_frames = max(1, int(flame_cfg.get("charge_max_frames", 45)))
            max_len = int(flame_cfg.get("max_range", 140))
            max_w = int(flame_cfg.get("max_width", 28))
            bonus_len = int(flame_cfg.get("upgrade_base_bonus_range", 20)) if self.player.flame_upgraded else 0
            bonus_w = int(flame_cfg.get("upgrade_base_bonus_width", 6)) if self.player.flame_upgraded else 0
            bonus_damage = int(flame_cfg.get("upgrade_base_bonus_damage", 1)) if self.player.flame_upgraded else 0

            if self.player.flame_upgraded:
                self._flame_charge_frames = min(max_frames, self._flame_charge_frames + 1)
            else:
                self._flame_charge_frames = 0

            ratio = (self._flame_charge_frames / max_frames) if self.player.flame_upgraded else 0.0
            min_len = min(max_len, base_len + bonus_len)
            min_w = min(max_w, base_w + bonus_w)
            if ratio >= 1.0:
                self.flame.length = max_len
                self.flame.width = max_w
            else:
                self.flame.length = int(lerp(min_len, max_len, ratio))
                self.flame.width = int(lerp(min_w, max_w, ratio))

            self.flame.damage = base_damage + bonus_damage
            self.flame.tick_interval = int(flame_cfg.get("tick_interval_frames", 3))
        else:
            if self.flame.active:
                self.flame.active = False
                pyxel.stop(2)
            self._flame_charge_frames = 0

    def _fire_laser(self, level: int) -> None:
        weapons = self._ctx.config.get("weapons", {})
        laser = weapons.get("laser", {})
        self.player.cooldown_laser = int(laser.get("cooldown_frames", 40))
        pyxel.play(0, 5)
        self.laser.active = True
        self.laser.x = self.player.pos.x + 14
        self.laser.y = self.player.pos.y + 8

        max_frames = max(1, int(laser.get("charge_max_frames", 45)))
        charge = min(max_frames, max(0, int(self._laser_charge_frames)))
        ratio = charge / max_frames

        base_len = int(laser.get("beam_length", 140))
        inc_len = int(laser.get("beam_length_increase_per_level", 10))
        max_len = int(laser.get("max_beam_length", 220))
        min_len = min(max_len, base_len + (level - 1) * inc_len)
        if ratio >= 1.0:
            self.laser.length = max_len
        else:
            self.laser.length = int(lerp(min_len, max_len, ratio))

        base_w = int(laser.get("beam_width", 4))
        inc_w = int(laser.get("beam_width_increase_per_level", 1))
        max_w = int(laser.get("max_beam_width", 10))
        min_w = min(max_w, base_w + (level - 1) * inc_w)
        if ratio >= 1.0:
            self.laser.width = max_w
        else:
            self.laser.width = int(lerp(min_w, max_w, ratio))

        if self.player.laser_maxed:
            self.laser.damage = int(laser.get("max_damage", laser.get("damage", 1)))
        else:
            self.laser.damage = int(laser.get("damage", 1))

        base_dur = 14 + (level - 1) * 2
        bonus_dur = int(laser.get("charge_bonus_duration", 22))
        if ratio >= 1.0:
            self.laser.duration = base_dur + bonus_dur
        else:
            self.laser.duration = int(lerp(base_dur, base_dur + bonus_dur, ratio))
        self.laser.tick_interval = int(laser.get("tick_interval_frames", 6))
        self.laser._tick = 0

    def _update_enemies(self) -> None:
        burn_cfg = self._ctx.config.get("weapons", {}).get("flame", {}).get("burn", {})
        burn_speed_mul = float(burn_cfg.get("speed_multiplier", 0.55))
        for e in self.enemies:
            if not e.active:
                continue
            e.timer += 1
            speed_mul = burn_speed_mul if e.burn_timer > 0 else 1.0
            if e.pattern == "straight":
                e.pos.x += e.vel.x * speed_mul
            elif e.pattern == "dash":
                e.pos.x += e.vel.x * 1.8 * speed_mul
            elif e.pattern in ("sine", "wave"):
                e.pos.x += e.vel.x * speed_mul
                e.pos.y += (pyxel.sin(e.timer * 4) * 0.5) * speed_mul
            elif e.pattern == "stop_shoot":
                if e.timer < 40:
                    e.pos.x += e.vel.x * speed_mul
                else:
                    e.pos.x += e.vel.x * 0.3 * speed_mul
                    e.shoot_cooldown = max(0, e.shoot_cooldown - 1)
                    if e.shoot_cooldown == 0:
                        e.shoot_cooldown = 60
                        self._spawn_enemy_shot(x=e.pos.x, y=e.pos.y + 3, vx=-2.4, vy=0.0, damage=10, lifetime=120)
            elif e.pattern == "formation":
                e.pos.x += e.vel.x * 1.2 * speed_mul

            if e.pos.x < -24 or e.pos.y < -24 or e.pos.y > self._h + 24:
                e.active = False

    def _update_projectiles(self) -> None:
        missile_turn = float(self._ctx.config.get("weapons", {}).get("missile", {}).get("turn_rate", 0.12))
        bomb_turn = float(self._ctx.config.get("weapons", {}).get("bomb", {}).get("homing_turn_rate", 0.10))
        for p in self.projectiles:
            if not p.active:
                continue
            p.lifetime -= 1
            if p.lifetime <= 0:
                if p.kind == "bomb":
                    self._explode_bomb(p)
                p.active = False
                continue

            if p.kind == "missile":
                target = self._nearest_enemy(p.pos.x, p.pos.y)
                if target is not None:
                    dx = (target.pos.x - p.pos.x)
                    dy = (target.pos.y - p.pos.y)
                    if abs(dx) + abs(dy) > 0.1:
                        desired = Vec2(dx, dy).normalized()
                        current = p.vel.normalized()
                        steer = Vec2(
                            current.x + (desired.x - current.x) * missile_turn,
                            current.y + (desired.y - current.y) * missile_turn,
                        ).normalized()
                        speed = p.vel.length()
                        p.vel = Vec2(steer.x * speed, steer.y * speed)
            elif p.kind == "bomb" and self.player.bomb_homing:
                target = self._nearest_enemy(p.pos.x, p.pos.y)
                if target is not None:
                    dx = (target.pos.x - p.pos.x)
                    dy = (target.pos.y - p.pos.y)
                    if abs(dx) + abs(dy) > 0.1:
                        desired = Vec2(dx, dy).normalized()
                        current = p.vel.normalized()
                        steer = Vec2(
                            current.x + (desired.x - current.x) * bomb_turn,
                            current.y + (desired.y - current.y) * bomb_turn,
                        ).normalized()
                        speed = p.vel.length()
                        p.vel = Vec2(steer.x * speed, steer.y * speed)

            p.pos.x += p.vel.x
            p.pos.y += p.vel.y
            if p.pos.x > self._w + 24 or p.pos.y < -24 or p.pos.y > self._h + 24:
                p.active = False

        for p in self.enemy_shots:
            if not p.active:
                continue
            p.lifetime -= 1
            if p.lifetime <= 0:
                p.active = False
                continue
            p.pos.x += p.vel.x
            p.pos.y += p.vel.y
            if p.pos.x < -24:
                p.active = False

    def _update_laser(self) -> None:
        if not self.laser.active:
            self._laser_fx = []
            return
        self.laser.x = self.player.pos.x + 14
        self.laser.y = self.player.pos.y + 8
        self._update_laser_fx()
        if self.laser.can_tick():
            self.laser.consume_tick()
            beam_rect = self.laser.rect()
            for e in self.enemies:
                if not e.active:
                    continue
                if aabb(beam_rect, e.rect()):
                    e.hp -= self.laser.damage
                    if e.hp <= 0:
                        self._kill_enemy(e)
        self.laser.step()

    def _update_flame(self) -> None:
        if not self.flame.active:
            self._flame_fx = []
            return
        self.flame.x = self.player.pos.x + 14
        self.flame.y = self.player.pos.y + 8

        if self.flame.can_tick():
            self.flame.consume_tick()
            flame_rect = self.flame.rect()
            for e in self.enemies:
                if not e.active:
                    continue
                if aabb(flame_rect, e.rect()):
                    e.hp -= self.flame.damage
                    self._ignite_enemy(e)
                    if e.hp <= 0:
                        self._kill_enemy(e)
        self.flame.step()

        seg_w = 8
        count = max(1, (int(self.flame.length) + seg_w - 1) // seg_w)
        if len(self._flame_fx) != count:
            self._flame_fx = [(0, 0) for _ in range(count)]
            self._flame_fx_refresh = 0
        self._flame_fx_refresh = max(0, self._flame_fx_refresh - 1)
        if self._flame_fx_refresh == 0:
            self._flame_fx_refresh = 2
            amp = max(1, int(self.flame.width) // 3)
            for i in range(count):
                dy = self._ctx.rng.randint(-amp, amp)
                variant = self._ctx.rng.randint(0, 1)
                self._flame_fx[i] = (dy, variant)

    def _ignite_enemy(self, e: Enemy) -> None:
        flame_cfg = self._ctx.config.get("weapons", {}).get("flame", {})
        burn = flame_cfg.get("burn", {})
        duration = int(burn.get("duration_frames", 120))
        if e.burn_timer <= 0:
            e.burn_timer = duration
            e.burn_tick = 0
        else:
            e.burn_timer = max(e.burn_timer, duration // 2)

    def _update_burning(self) -> None:
        flame_cfg = self._ctx.config.get("weapons", {}).get("flame", {})
        burn = flame_cfg.get("burn", {})
        tick_interval = max(1, int(burn.get("tick_interval_frames", 10)))
        burn_damage = int(burn.get("damage", 1))
        spread_r = float(burn.get("spread_radius", 22))
        spread_r2 = spread_r * spread_r
        duration = int(burn.get("duration_frames", 120))

        for e in self.enemies:
            if not e.active or e.burn_timer <= 0:
                continue
            e.burn_timer -= 1
            e.burn_tick -= 1
            if e.burn_tick > 0:
                continue
            e.burn_tick = tick_interval
            e.hp -= burn_damage
            if e.hp <= 0:
                self._kill_enemy(e)
                continue
            for other in self.enemies:
                if not other.active or other.burn_timer > 0:
                    continue
                dx = (other.pos.x - e.pos.x)
                dy = (other.pos.y - e.pos.y)
                if dx * dx + dy * dy <= spread_r2:
                    other.burn_timer = max(1, duration // 2)
                    other.burn_tick = tick_interval

    def _update_laser_fx(self) -> None:
        seg_w = 8
        count = max(1, (int(self.laser.length) + seg_w - 1) // seg_w)
        if len(self._laser_fx) != count:
            self._laser_fx = [(0, 0, 0) for _ in range(count)]
            self._laser_fx_refresh = 0

        self._laser_fx_refresh = max(0, self._laser_fx_refresh - 1)
        if self._laser_fx_refresh > 0:
            return
        self._laser_fx_refresh = 3

        amp = max(1, int(self.laser.width))
        for i in range(count):
            dy = self._ctx.rng.randint(-amp, amp)
            variant = self._ctx.rng.randint(0, 1)
            branch_dir = 0
            if self._ctx.rng.random() < 0.20:
                branch_dir = -1 if (i % 2 == 0) else 1
            self._laser_fx[i] = (dy, variant, branch_dir)

    def _update_items(self) -> None:
        for it in self.items:
            if not it.active:
                continue
            it.lifetime -= 1
            it.pos.x += it.vel.x
            it.pos.y += it.vel.y
            if it.lifetime <= 0 or it.pos.x < -16:
                it.active = False

    def _update_particles(self) -> None:
        for fx in self.particles:
            if not fx.active:
                continue
            fx.lifetime -= 1
            fx.pos.x += fx.vel.x
            fx.pos.y += fx.vel.y
            if fx.lifetime <= 0:
                fx.active = False

    def _handle_collisions(self) -> None:
        pr = self.player.rect()

        # player vs enemies
        inv_frames = int(self._ctx.config.get("player", {}).get("invincible_frames", 60))
        for e in self.enemies:
            if not e.active:
                continue
            if aabb(pr, e.rect()):
                if self.player.apply_damage(20, inv_frames):
                    self._spawn_explosion(self.player.pos.x + 8, self.player.pos.y + 8, 6)
                e.hp = 0
                self._kill_enemy(e)

        # player vs enemy bullets
        for p in self.enemy_shots:
            if not p.active:
                continue
            if aabb(pr, p.rect()):
                if self.player.apply_damage(p.damage, inv_frames):
                    self._spawn_explosion(self.player.pos.x + 8, self.player.pos.y + 8, 6)
                p.active = False

        # player bullets vs enemies
        for p in self.projectiles:
            if not p.active or p.owner != "player":
                continue
            if p.kind == "bomb":
                # bomb collision handled like a projectile, but explodes
                for e in self.enemies:
                    if not e.active:
                        continue
                    if aabb(p.rect(), e.rect()):
                        self._explode_bomb(p)
                        p.active = False
                        break
                continue

            for e in self.enemies:
                if not e.active:
                    continue
                if aabb(p.rect(), e.rect()):
                    e.hp -= p.damage
                    p.active = False
                    if e.hp <= 0:
                        self._kill_enemy(e)
                    break

        # items pickup
        for it in self.items:
            if not it.active:
                continue
            if aabb(pr, it.rect()):
                self._apply_item(it.kind)
                it.active = False

    def _apply_item(self, kind: str) -> None:
        items = self._ctx.config.get("items", {})
        if kind == "heal":
            self.player.heal(int(items.get("heal_amount", 25)))
            pyxel.play(0, 7)
        elif kind == "power":
            self.player.power_up(int(items.get("power_amount", 1)), int(self._ctx.config.get("weapons", {}).get("max_level", 5)))
            self.player.laser_maxed = True
            self.player.bomb_radius_maxed = True
            self.player.bomb_homing = True
            self.player.bomb_big = True
            self.player.flame_upgraded = True
            pyxel.play(0, 7)
        elif kind == "speed":
            self.player.speed_up(float(items.get("speed_amount", 0.2)))
            pyxel.play(0, 7)

    def _kill_enemy(self, e: Enemy) -> None:
        if not e.active:
            return
        e.active = False
        self.kills += e.score
        pyxel.play(0, 6)
        self._spawn_explosion(e.pos.x + e.w / 2, e.pos.y + e.h / 2, 5)
        drop_kind = roll_drop(self._ctx.rng, float(self._ctx.config.get("items", {}).get("drop_chance", 0.22)))
        if drop_kind is not None:
            self.items.append(
                Item(
                    active=True,
                    kind=drop_kind,
                    pos=Vec2(e.pos.x, e.pos.y),
                    vel=Vec2(-0.8, 0.2),
                    w=4,
                    h=4,
                    lifetime=360,
                )
            )

    def _explode_bomb(self, p: Projectile) -> None:
        radius = max(1, p.radius)
        cx = p.pos.x
        cy = p.pos.y
        pyxel.play(0, 6)
        self._spawn_explosion(cx, cy, 10)
        r2 = radius * radius
        for e in self.enemies:
            if not e.active:
                continue
            dx = (e.pos.x - cx)
            dy = (e.pos.y - cy)
            if dx * dx + dy * dy <= r2:
                e.hp -= p.damage
                if e.hp <= 0:
                    self._kill_enemy(e)

    def _spawn_explosion(self, x: float, y: float, count: int) -> None:
        for i in range(count):
            ang = (i * 37) % 360
            vx = pyxel.cos(ang) * 1.2
            vy = pyxel.sin(ang) * 1.2
            self._spawn_particle(x=x, y=y, vx=vx, vy=vy, lifetime=18)

    def _nearest_enemy(self, x: float, y: float) -> Enemy | None:
        best: Enemy | None = None
        best_d = 1e18
        for e in self.enemies:
            if not e.active:
                continue
            dx = e.pos.x - x
            dy = e.pos.y - y
            d = dx * dx + dy * dy
            if d < best_d:
                best_d = d
                best = e
        return best

    def _draw_entities(self) -> None:
        a = self._ctx.assets
        # Enemies
        for e in self.enemies:
            if not e.active:
                continue
            sp = a.sprites[f"enemy:{e.kind}"]
            pyxel.blt(int(e.pos.x), int(e.pos.y), sp.img, sp.u, sp.v, sp.w, sp.h, sp.colkey)

        # Items
        for it in self.items:
            if not it.active:
                continue
            sp = a.sprites[f"item:{it.kind}"]
            pyxel.blt(int(it.pos.x), int(it.pos.y), sp.img, sp.u, sp.v, sp.w, sp.h, sp.colkey)

        # Player
        sp = a.sprites[f"ship:{self.player.ship}"]
        if self.player.invincible > 0 and (self.player.invincible // 4) % 2 == 0:
            pass
        else:
            pyxel.blt(int(self.player.pos.x), int(self.player.pos.y), sp.img, sp.u, sp.v, sp.w, sp.h, sp.colkey)

        # Player projectiles
        for p in self.projectiles:
            if not p.active:
                continue
            sp = a.sprites.get(f"shot:{p.kind}")
            if sp is None:
                continue
            pyxel.blt(int(p.pos.x), int(p.pos.y), sp.img, sp.u, sp.v, sp.w, sp.h, sp.colkey)

        # Enemy shots
        sp_enemy = a.sprites["shot:cannon"]
        for p in self.enemy_shots:
            if not p.active:
                continue
            pyxel.blt(int(p.pos.x), int(p.pos.y), sp_enemy.img, sp_enemy.u, sp_enemy.v, sp_enemy.w, sp_enemy.h, sp_enemy.colkey)

        # Laser
        if self.laser.active:
            seg = a.sprites["shot:laser_seg"]
            base_y = int(self.laser.y)
            half = max(0, int(self.laser.width) // 2)
            for dy in range(-half, half + 1):
                y = base_y + dy
                x = int(self.laser.x)
                remaining = int(self.laser.length)
                while remaining > 0:
                    w = min(seg.w, remaining)
                    pyxel.blt(x, y, seg.img, seg.u, seg.v, w, seg.h, seg.colkey)
                    x += w
                    remaining -= w

            # lightning overlay (precomputed in update; no randomness here)
            fx_a = a.sprites["shot:laser_fx_a"]
            fx_b = a.sprites["shot:laser_fx_b"]
            branch = a.sprites["shot:laser_branch"]
            seg_w = 8
            count = max(1, (int(self.laser.length) + seg_w - 1) // seg_w)
            base_x = int(self.laser.x)
            for i in range(min(count, len(self._laser_fx))):
                dy, variant, branch_dir = self._laser_fx[i]
                fx = fx_a if variant == 0 else fx_b
                x = base_x + i * seg_w
                y = base_y + dy
                pyxel.blt(x, y, fx.img, fx.u, fx.v, fx.w, fx.h, fx.colkey)
                if branch_dir != 0:
                    pyxel.blt(
                        x + 2,
                        y + branch_dir * 3,
                        branch.img,
                        branch.u,
                        branch.v,
                        branch.w,
                        branch.h,
                        branch.colkey,
                    )

        # Flame
        if self.flame.active:
            blue = self.player.flame_upgraded and self._flame_charge_frames >= int(
                self._ctx.config.get("weapons", {}).get("flame", {}).get("charge_max_frames", 45)
            )
            flame_a = a.sprites["shot:flame_blue_a" if blue else "shot:flame_a"]
            flame_b = a.sprites["shot:flame_blue_b" if blue else "shot:flame_b"]
            base_y = int(self.flame.y)
            base_x = int(self.flame.x)
            seg_w = 8
            count = max(1, (int(self.flame.length) + seg_w - 1) // seg_w)
            for i in range(min(count, len(self._flame_fx))):
                dy, variant = self._flame_fx[i]
                sp = flame_a if variant == 0 else flame_b
                x = base_x + i * seg_w
                y = base_y + dy
                pyxel.blt(x, y, sp.img, sp.u, sp.v, sp.w, sp.h, sp.colkey)

        # Burning overlay on enemies
        burn_a = a.sprites["shot:flame_a"]
        burn_b = a.sprites["shot:flame_b"]
        for e in self.enemies:
            if not e.active or e.burn_timer <= 0:
                continue
            sp = burn_a if (e.timer // 4) % 2 == 0 else burn_b
            pyxel.blt(int(e.pos.x + 2), int(e.pos.y - 4), sp.img, sp.u, sp.v, sp.w, sp.h, sp.colkey)

        # Particles
        fx_sp = a.sprites["fx:explosion"]
        for fx in self.particles:
            if not fx.active:
                continue
            pyxel.blt(int(fx.pos.x), int(fx.pos.y), fx_sp.img, fx_sp.u, fx_sp.v, fx_sp.w, fx_sp.h, fx_sp.colkey)

    def _spawn_projectile(
        self,
        *,
        kind: str,
        owner: str,
        x: float,
        y: float,
        vx: float,
        vy: float,
        w: int,
        h: int,
        damage: int,
        lifetime: int,
        radius: int = 0,
    ) -> None:
        for p in self.projectiles:
            if p.active:
                continue
            p.active = True
            p.kind = kind
            p.owner = owner
            p.pos.x = x
            p.pos.y = y
            p.vel.x = vx
            p.vel.y = vy
            p.w = w
            p.h = h
            p.damage = damage
            p.lifetime = lifetime
            p.radius = radius
            return

    def _spawn_enemy_shot(self, *, x: float, y: float, vx: float, vy: float, damage: int, lifetime: int) -> None:
        for p in self.enemy_shots:
            if p.active:
                continue
            p.active = True
            p.kind = "enemy"
            p.owner = "enemy"
            p.pos.x = x
            p.pos.y = y
            p.vel.x = vx
            p.vel.y = vy
            p.w = 2
            p.h = 2
            p.damage = damage
            p.lifetime = lifetime
            p.radius = 0
            return

    def _spawn_particle(self, *, x: float, y: float, vx: float, vy: float, lifetime: int) -> None:
        for fx in self.particles:
            if fx.active:
                continue
            fx.active = True
            fx.pos.x = x
            fx.pos.y = y
            fx.vel.x = vx
            fx.vel.y = vy
            fx.lifetime = lifetime
            return
