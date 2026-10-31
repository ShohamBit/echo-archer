"""Pygame scenes, input, rendering and application lifecycle.

Fixed logical canvas + letterboxing keeps mouse coordinates correct on resize.
The combat model knows nothing about the window or UI.
"""
import argparse
import math
import os
from pathlib import Path
import random
import pygame
import pygame.gfxdraw
from .audio import Audio
from .model import HEIGHT, WIDTH, PLAYER_RADIUS, Run, bank_run
from .progression import Progress, UPGRADES, load_progress, save_progress
from .creatures import draw_creature
from .shop import SkillTree
from .presentation import Presentation

CANVAS = (1280, 800)
ARENA = pygame.Rect(240, 0, 800, 800)
BG = (12, 16, 22)
PANEL = (21, 28, 36)
LINE = (48, 61, 70)
WHITE = (229, 240, 237)
MUTED = (133, 153, 160)
CYAN = (108, 226, 210)
RED = (255, 99, 113)
GOLD = (239, 196, 119)


class App:
    def __init__(self, save_path: Path, *, headless=False, seed=None, windowed=False):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.window = pygame.display.set_mode((1152, 720), pygame.RESIZABLE) if headless or windowed else pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Loop Archer / Python")
        self.canvas = pygame.Surface(CANVAS)
        self.clock = pygame.time.Clock()
        regular_font = Path("C:/Windows/Fonts/segoeui.ttf")
        font_path = str(regular_font) if regular_font.exists() else None
        self.fonts = {size: pygame.font.Font(font_path, size) for size in (18, 20, 22, 24, 28, 32, 40, 48, 64, 88)}
        self.hud_fonts = {size: pygame.font.Font(None, size + 12) for size in (48, 64)}
        self.text_cache = {}
        self.scaled_frame = None
        self.shop = SkillTree()
        self.presentation = Presentation()
        self.shot_pulse = 0.0
        self.audio = Audio()
        if headless:
            self.audio.enabled = False
        self.save_path = save_path
        self.progress, self.notice = load_progress(save_path)
        self.save_allowed = not self.notice
        self.rng = random.Random(seed)
        self.visual_rng = random.Random(seed)
        self.scene = "menu"
        self.run = None
        self.running = True
        self.endless = False
        self.original_mode = False
        self.recall_keys = set()
        self.arrow_directions = {}
        self.fullscreen = not (headless or windowed)
        self.comparison = False
        self.practice = False
        self.run_practice = False
        self.windowed_size = (1152, 720)
        self.practice_boss = "boss"
        self.intro_remaining = 0.0
        self.intro_boss = None
        self.seen_bosses = set()
        self.mouse = (-100, -100)
        self.buttons = []
        self.animation = 0.0
        self.result_banked = False
        self.last_save = 0.0
        self.checker = pygame.Surface(ARENA.size).convert()
        for y in range(ARENA.height):
            tone = 20 + round(9 * y / ARENA.height)
            pygame.draw.line(self.checker, (tone - 6, tone, tone + 8), (0, y), (ARENA.width, y))
        for x in range(0, ARENA.width, 80):
            pygame.draw.line(self.checker, (27, 39, 48), (x, 0), (x, ARENA.height))
        for y in range(0, ARENA.height, 80):
            pygame.draw.line(self.checker, (27, 39, 48), (0, y), (ARENA.width, y))
        pygame.draw.rect(self.checker, (49, 73, 82), (14, 14, 772, 772), 1, border_radius=28)
        # A soft vignette preserves the original's dark square playfield without
        # changing the simulation or consuming its seeded random sequence.
        self.vignette = pygame.Surface(ARENA.size, pygame.SRCALPHA)
        for margin in range(0, 170, 2):
            pygame.draw.rect(self.vignette, (0, 0, 0, max(0, 9 - margin // 22)),
                             self.vignette.get_rect().inflate(-margin * 2, -margin * 2), 2)

    def persist(self):
        if not self.save_allowed or self.practice:
            return
        try:
            save_progress(self.save_path, self.progress)
        except OSError as exc:
            self.notice = f"Unable to save: {exc.strerror or 'file access error'}"

    def start(self, practice=False):
        self.shop.release()
        self.shop.dragging = False
        self.run = Run(self.progress, self.rng, self.endless, original=self.original_mode)
        self.practice = practice
        self.run_practice = practice
        self.intro_remaining = 0
        self.intro_boss = None
        self.seen_bosses.clear()
        if practice:
            self.run.original = False
            self.run.endless = False
            self.run.wave = 8 if self.practice_boss == "boss" else 4
            self.run.wave_delay = 0
            self.run.spawn(self.practice_boss)
            self.begin_boss_intro(self.run.enemies[-1])
        self.scene = "play"
        self.result_banked = False
        self.recall_keys.clear()
        self.arrow_directions.clear()

    def begin_boss_intro(self, enemy):
        self.seen_bosses.add(enemy.id)
        self.intro_boss = enemy
        self.intro_remaining = 3.2
        self.cancel_input()

    def draw_loadout(self):
        self.header("UPGRADE LOADOUT")
        self.text("Set equipped ranks without losing purchases. Combat changes apply next run.", 60, 92, 22, MUTED)
        self.text("Equipped / owned", 350, 124, 18, MUTED)
        self.text("Equipped / owned", 960, 124, 18, MUTED)
        for i, upgrade in enumerate(UPGRADES):
            x, y = 60 + (i // 10) * 610, 147 + (i % 10) * 49
            pygame.draw.rect(self.canvas, PANEL, (x, y, 550, 43), border_radius=7)
            owned = self.progress.level(upgrade.key)
            active = self.progress.equipped_levels()[upgrade.key]
            self.text(upgrade.name, x + 12, y + 8, 20, WHITE if active else MUTED)
            self.text(f"{active} / {owned}", x + 290, y + 8, 20, CYAN)
            self.button("−", (x + 386, y + 3, 60, 37), "rank-:" + upgrade.key, active > 0)
            self.button("+", (x + 470, y + 3, 60, 37), "rank+:" + upgrade.key, active < owned)
            if pygame.Rect(x, y, 550, 43).collidepoint(self.mouse):
                self.wrapped(upgrade.description, 65, 655, 1140, 20, GOLD)
        self.button("DISABLE ALL", (60, 716, 245, 52), "loadout_off")
        self.button("EQUIP ALL OWNED", (320, 716, 280, 52), "loadout_all")
        self.button("PLAY", (660, 716, 240, 52), "start", accent=True)
        self.button("BACK", (950, 716, 270, 52), "menu")

    def text(self, text, x, y, size=24, color=WHITE, center=False):
        key = (str(text), size, tuple(color))
        surface = self.text_cache.get(key)
        if surface is None:
            surface = self.fonts[size].render(str(text), True, color)
            if len(self.text_cache) >= 512:
                self.text_cache.clear()
            self.text_cache[key] = surface
        rect = surface.get_rect(center=(x, y)) if center else surface.get_rect(topleft=(x, y))
        self.canvas.blit(surface, rect)
        return rect

    def wrapped(self, text, x, y, width, size=24, color=MUTED):
        words, line = text.split(), ""
        for word in words:
            trial = (line + " " + word).strip()
            if line and self.fonts[size].size(trial)[0] > width:
                self.text(line, x, y, size, color)
                y += size + 4
                line = word
            else:
                line = trial
        if line:
            self.text(line, x, y, size, color)
        return y + size + 4

    def hud_text(self, text, x, y, size=64, color=WHITE, center=False):
        surface = self.hud_fonts[size].render(str(text), True, color)
        rect = surface.get_rect(center=(x, y)) if center else surface.get_rect(topleft=(x, y))
        self.canvas.blit(surface, rect)

    def button(self, label, rect, action, enabled=True, accent=False):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(self.mouse) and enabled
        color = CYAN if accent and enabled else WHITE if enabled else MUTED
        fill = (37, 64, 65) if hover else (26, 42, 46) if accent else PANEL
        pygame.draw.rect(self.canvas, fill, rect, border_radius=7)
        pygame.draw.rect(self.canvas, color if hover or accent else LINE, rect, 1, border_radius=7)
        self.text(label, *rect.center, 24, color, True)
        self.buttons.append((rect, action, enabled))

    def header(self, title):
        self.text("LOOP / ARCHER", 30, 24, 32)
        self.text(title, 270, 29, 22, CYAN)
        pygame.draw.line(self.canvas, LINE, (30, 76), (1250, 76))

    def diamond(self, pos, radius, color, width=0):
        x, y = pos
        points = [(round(x), round(y - radius)), (round(x + radius), round(y)),
                  (round(x), round(y + radius)), (round(x - radius), round(y))]
        if width:
            pygame.draw.polygon(self.canvas, color, points, width)
        else:
            pygame.gfxdraw.filled_polygon(self.canvas, points, color)
        pygame.gfxdraw.aapolygon(self.canvas, points, color)

    def bow(self, pos, direction, charge=0, scale=1):
        direction = pygame.Vector2(direction)
        side = direction.rotate(90)
        pos = pygame.Vector2(pos)
        tip1, tip2 = pos + direction * 18 * scale + side * 22 * scale, pos + direction * 18 * scale - side * 22 * scale
        front = pos + direction * 30 * scale
        pygame.draw.lines(self.canvas, CYAN if charge >= .98 else WHITE, False, [tip1, front, tip2], max(2, int(3 * scale)))
        pull = pos + direction * (18 - charge * 20) * scale
        pygame.draw.lines(self.canvas, MUTED, False, [tip1, pull, tip2], 1)
        pygame.draw.line(self.canvas, WHITE, pull, pos + direction * 42 * scale, 2)

    def draw_menu(self):
        self.header("DRAW / RECALL / EVOLVE")
        for radius in (120, 180, 250):
            pygame.draw.circle(self.canvas, LINE, (950, 380), radius, 1)
        self.diamond((950, 380), 35, WHITE)
        self.bow((950, 380), (math.cos(self.animation * .3), math.sin(self.animation * .3)), .7, 2.3)
        for i in range(7):
            angle = i * math.tau / 7 + self.animation * .06
            self.diamond((950 + math.cos(angle) * 250, 380 + math.sin(angle) * 250), 12, RED)
        self.text("ONE MORE", 65, 173, 88)
        self.text("LOOP.", 65, 247, 88, CYAN)
        self.wrapped("One bow. A changing battlefield. Make every shot count, then pull it back for another.", 70, 355, 505, 24)
        self.button("ENTER THE LOOP   /   SPACE", (70, 465, 440, 62), "start", accent=True)
        self.button("PERMANENT UPGRADES", (70, 542, 440, 54), "tree")
        mode = "SURVIVAL" if self.original_mode else "ENDLESS" if self.endless else "CAMPAIGN / 8 WAVES"
        self.button("MODE: " + mode, (70, 612, 440, 48), "mode")
        self.button("BOSS PRACTICE", (535, 612, 235, 48), "practice")
        self.button("BOSS: WARDEN" if self.practice_boss == "boss" else "BOSS: TEMPEST", (790, 612, 220, 48), "practice_boss")
        self.button("UPGRADE LOADOUT", (535, 542, 290, 54), "loadout")
        self.text(f"{self.progress.points} points    /    {self.progress.loops} attempts    /    Best wave {self.progress.best_wave}", 70, 702, 20, GOLD)
        self.text("Based on LOOP ARCHER by PolyCube & tEMMiE", 70, 752, 20, MUTED)
        self.text("M  SOUND ON/OFF     ESC  QUIT", 930, 752, 20, MUTED)

    def draw_arena(self):
        run = self.run
        offset = pygame.Vector2(ARENA.topleft)
        scale = ARENA.width / WIDTH
        if run.shake > 0 and self.presentation.shake:
            offset += (self.visual_rng.uniform(-run.shake, run.shake), self.visual_rng.uniform(-run.shake, run.shake))
        def point(position):
            return pygame.Vector2(position) * scale + offset

        self.canvas.blit(self.checker, ARENA)
        self.canvas.set_clip(ARENA)
        for x in (ARENA.left + 5, ARENA.right - 5):
            pygame.draw.line(self.canvas, (37, 80, 83), (x, 150), (x, 650), 8)
            pygame.draw.line(self.canvas, CYAN, (x, 180), (x, 620), 2)
        for p in run.particles:
            pygame.draw.circle(self.canvas, p.color, point(p.pos), max(1, round(p.life * 8)))
        for arrow in run.arrows:
            arrow_id = id(arrow)
            if arrow.velocity:
                self.arrow_directions[arrow_id] = arrow.velocity.normalize()
            direction = self.arrow_directions.get(arrow_id, pygame.Vector2(1, 0))
            p = point(arrow.pos)
            # The shipped arrow is a substantial silhouette, rather than a tiny
            # projectile. It dims when no longer moving and safe to pick up.
            color = (246, 246, 246) if arrow.state != "stuck" else (113, 113, 119)
            if arrow.state == "returning":
                color = CYAN
            length = 170 * scale
            side = direction.rotate(90)
            tail, head = p - direction * length / 2, p + direction * length / 2
            if self.presentation.trails and arrow.state != "stuck":
                pygame.draw.aaline(self.canvas, (48, 88, 95), tail - direction * 50, tail)
            pygame.draw.line(self.canvas, (5, 5, 8), tail + (0, 5), head + (0, 5), 9)
            pygame.draw.line(self.canvas, color, tail, head - direction * 12, 5)
            pygame.draw.polygon(self.canvas, color, [head + direction * 9,
                                head - direction * 14 + side * 9, head - direction * 14 - side * 9])
            pygame.draw.aalines(self.canvas, color, True, [head + direction * 9,
                                head - direction * 14 + side * 9, head - direction * 14 - side * 9])
            pygame.draw.polygon(self.canvas, color, [tail - direction * 3,
                                tail + direction * 14 + side * 7, tail + direction * 14 - side * 7])
        active_arrows = {id(arrow) for arrow in run.arrows}
        self.arrow_directions = {key: value for key, value in self.arrow_directions.items() if key in active_arrows}
        for enemy in run.enemies:
            p = point(enemy.pos)
            radius = enemy.radius * scale
            if enemy.warden:
                self.draw_warden(enemy, point, scale)
                continue
            draw_creature(self.canvas, enemy, point, scale, self.animation, self.presentation.flashes)
        for bullet in run.bullets:
            pygame.draw.circle(self.canvas, RED, point(bullet.pos), max(6, 14 * scale))
        p = point(run.player)
        if not self.presentation.flashes or run.invulnerable <= 0 or int(run.elapsed * 12) % 2 == 0:
            self.diamond(p + (0, 8), 80 * scale, (9, 9, 12))
            self.diamond(p, 80 * scale, WHITE)
            self.diamond(p, 48 * scale, (30, 68, 74))
            ratio = min(1, run.charge / run.charge_duration)
            # Bow sits beyond the body, with the same large visual footprint as
            # the original rather than occupying the archer's center.
            bow_pos = p + run.aim * ((74 - self.shot_pulse * 18) * scale)
            bow_scale = 4 * scale
            direction = run.aim
            side = direction.rotate(90)
            tip1 = bow_pos + direction * 18 * bow_scale + side * 22 * bow_scale
            tip2 = bow_pos + direction * 18 * bow_scale - side * 22 * bow_scale
            front = bow_pos + direction * (30 - ratio * 9 + self.shot_pulse * 6) * bow_scale
            pygame.draw.lines(self.canvas, (145, 145, 150), False, [tip1, front, tip2], 6)
            pygame.draw.aalines(self.canvas, CYAN, False, [tip1, front, tip2])
            pull = bow_pos + direction * (18 - ratio * 20) * bow_scale
            pygame.draw.lines(self.canvas, (213, 213, 218), False, [tip1, pull, tip2], 2)
            if run.can_shoot:
                pygame.draw.line(self.canvas, WHITE, pull, bow_pos + direction * 42 * bow_scale, 5)
            if run.shields:
                pygame.draw.circle(self.canvas, (200, 218, 236), p, 108 * scale, 2)
        state = run.bow_state
        label = {"ready": "READY", "charging": f"DRAW {run.charge_level}/4", "flying": "IN FLIGHT",
                 "recallable": "RECALL READY", "returning": "RETURNING"}[state]
        color = GOLD if state in ("charging", "recallable") else CYAN if state in ("ready", "returning") else MUTED
        badge = pygame.Rect(0, 0, 162, 30)
        badge.center = (max(ARENA.left + 85, min(ARENA.right - 85, p.x)), max(155, min(690, p.y + 72)))
        pygame.draw.rect(self.canvas, (15, 27, 35), badge, border_radius=10)
        pygame.draw.rect(self.canvas, color, badge, 1, border_radius=10)
        self.text(label, *badge.center, 18, color, True)
        if state == "charging":
            for i in range(4):
                pygame.draw.circle(self.canvas, GOLD if i < run.charge_level else LINE,
                                   (badge.centerx - 24 + i * 16, badge.bottom + 9), 4)
        self.canvas.blit(self.vignette, ARENA)
        if ARENA.collidepoint(self.mouse):
            mx, my = self.mouse
            for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                pygame.draw.line(self.canvas, WHITE, (mx + dx * 8, my + dy * 8), (mx + dx * 17, my + dy * 17), 3)
        self.canvas.set_clip(None)

    def draw_warden(self, enemy, point, scale):
        warden = enemy.warden
        p, radius = point(enemy.pos), enemy.radius * scale
        if self.intro_remaining > 0 and self.intro_boss is enemy:
            arrival = max(0, min(1, (3.2 - self.intro_remaining) / 1.8))
            p.y -= (1 - arrival) ** 2 * 440
            radius *= .45 + .55 * arrival
            for ring in range(3):
                pygame.draw.ellipse(self.canvas, (135, 101, 189),
                                    (p.x-radius*(1.3+ring*.3), p.y-radius*.4-ring*9,
                                     radius*(2.6+ring*.6), radius*.8+ring*18), 2)
        if enemy.kind == "tempest":
            violet = (189, 144, 252)
            if warden.phase == "blink" and warden.target is not None:
                destination = point(warden.target)
                pygame.draw.circle(self.canvas, violet, destination, radius + 18, 2)
                pygame.draw.line(self.canvas, violet, destination - (18, 0), destination + (18, 0), 2)
                pygame.draw.line(self.canvas, violet, destination - (0, 18), destination + (0, 18), 2)
            # Six revolving blades surround an eye, rather than Warden armor.
            for i in range(6):
                direction = pygame.Vector2(1, 0).rotate(warden.angle + i * 60)
                side = direction.rotate(90)
                points = [p + direction * radius * .55, p + direction * radius * 1.12 + side * radius * .25,
                          p + direction * radius * 1.25, p + direction * radius * .7 - side * radius * .18]
                pygame.draw.polygon(self.canvas, (50, 37, 72), points)
                pygame.draw.aalines(self.canvas, violet, True, points)
            eye = [p + (-radius*.6, 0), p + (0, -radius*.32), p + (radius*.6, 0), p + (0, radius*.32)]
            pygame.draw.polygon(self.canvas, CYAN if warden.exposed else violet, eye)
            pygame.draw.circle(self.canvas, BG, p, radius*.18)
            return
        direction = warden.heading
        side = direction.rotate(90)
        if warden.phase == "dash_windup":
            end = point(enemy.pos + direction * 800)
            polygon = [p + side * radius, end + side * radius, end - side * radius, p - side * radius]
            pygame.draw.polygon(self.canvas, (53, 34, 45), polygon)
            pygame.draw.aalines(self.canvas, RED, True, polygon)
            pygame.draw.aaline(self.canvas, GOLD, p, end)
        elif warden.phase == "fan_windup":
            for angle in (-24, -12, 0, 12, 24):
                ray = direction.rotate(angle)
                pygame.draw.aaline(self.canvas, (155, 91, 82), p + ray * radius,
                                   point(enemy.pos + ray * 750))
        pygame.draw.circle(self.canvas, (29, 38, 51), p, radius)
        pygame.draw.circle(self.canvas, (85, 115, 134), p, radius, 2)
        facing = -math.atan2(direction.y, direction.x)
        pygame.draw.arc(self.canvas, RED, (p.x - radius, p.y - radius, radius * 2, radius * 2),
                        facing - 2.25, facing + 2.25, 7)
        self.diamond(p, radius * .35, GOLD if warden.phase.endswith("windup") else MUTED)
        core = p - direction * radius * .72
        color = CYAN if warden.exposed else (71, 95, 109)
        pygame.draw.circle(self.canvas, (12, 27, 34), core, 55 * scale)
        pygame.draw.circle(self.canvas, color, core, 48 * scale, 3)
        pygame.draw.circle(self.canvas, color, core, 19 * scale)
        if warden.exposed:
            pygame.draw.circle(self.canvas, CYAN, core, (58 + math.sin(self.animation * 8) * 5) * scale, 1)

    def draw_play(self):
        run = self.run
        self.canvas.fill(BG)
        self.draw_arena()
        timer = pygame.Rect(ARENA.centerx - 260, 30, 520, 18)
        pygame.draw.rect(self.canvas, (5, 5, 7), timer)
        fill = timer.inflate(-10, -10)
        fill.width = max(0, round(fill.width * run.time_left / run.max_time))
        pygame.draw.rect(self.canvas, CYAN if run.time_left > 4 else RED, fill, border_radius=5)
        self.text(f"{run.time_left:.1f}s", ARENA.centerx, 68, 24, WHITE, True)
        self.text("LOOP", 28, 65, 28, MUTED)
        self.text("ARCHER", 28, 102, 28, CYAN)
        self.text("WAVE", 28, 200, 20, MUTED)
        wave = f"{run.wave:02} / 08" if self.practice or not self.endless and not self.original_mode else f"{run.wave:02}"
        self.text(wave, 28, 235, 32, WHITE)
        self.text("POINTS", 28, 310, 20, MUTED)
        self.hud_text(run.points, 28, 350, 48, GOLD)
        self.text(f"{run.kills} kills", 28, 426, 22, MUTED)
        self.text(f"{run.shields} shields", 28, 463, 22, CYAN)
        self.text(f"{len(run.enemies) + len(run.spawn_queue)} enemies {'active' if run.original else 'left'}", 28, 501, 18, MUTED)
        self.wrapped("Defeat the final boss to clear the campaign." if self.practice or not self.endless and not self.original_mode else "Survive. There is no automatic finish.", 28, 525, 190, 18, MUTED)
        boss = next((e for e in run.enemies if e.warden), None)
        if boss and self.intro_remaining <= 0:
            self.text(boss.warden.NAME + (" / ENRAGED" if boss.warden.enraged else ""), ARENA.centerx, 108, 24, RED, True)
            pygame.draw.rect(self.canvas, (54, 31, 43), (ARENA.centerx - 180, 132, 360, 8), border_radius=4)
            pygame.draw.rect(self.canvas, RED, (ARENA.centerx - 180, 132, 360 * max(0, min(1, boss.hp / boss.warden.MAX_HEALTH)), 8), border_radius=4)
            self.text(boss.warden.hint, ARENA.centerx, 165, 18, CYAN if boss.warden.exposed else GOLD, True)
        status = run.bow_hint
        self.text(status, ARENA.centerx, 754, 22, (180, 180, 186), True)
        if run.feedback_time > 0:
            self.text(run.feedback, ARENA.centerx, 708, 18, GOLD, True)
        if run.combo > 1:
            self.text(f"SKILLSHOT CHAIN {run.combo}", 1060, 210, 18, CYAN)
            pygame.draw.rect(self.canvas, CYAN, (1060, 245, 190 * run.combo_timer / 3, 4), border_radius=2)
        if run.skillshot_bonus:
            self.text(f"+{run.skillshot_bonus} skill points", 1060, 290, 18, GOLD)
        if run.multikill_bonus:
            self.text(f"+{run.multikill_bonus} multi-kill points", 1060, 330, 18, GOLD)
            self.text(f"Best burst: {run.best_multikill}", 1060, 357, 18, MUTED)
        if run.multikill_feedback_time > 0:
            self.text(run.multikill_feedback, ARENA.centerx, 675, 24, CYAN, True)
        self.text("ESC PAUSE   M SOUND   F11 FULLSCREEN", ARENA.centerx, 782, 18, (106, 106, 112), True)

    def draw_boss_intro(self):
        boss = self.intro_boss
        # A local gate and title card; the arena stays visible throughout arrival.
        pygame.draw.rect(self.canvas, BG, (ARENA.left, 570, ARENA.width, 175))
        self.text("AN INTRUDER ENTERS THE LOOP", 640, 599, 20, GOLD, True)
        self.text(boss.warden.NAME, 640, 641, 40, RED if boss.kind == "boss" else (189, 144, 252), True)
        self.text("Break the armor. Survive the charge." if boss.kind == "boss" else "Escape the spiral. Punish the blink.", 640, 686, 22, WHITE, True)
        self.text("ENTER TO SKIP", 640, 725, 18, MUTED, True)

    def draw_tree(self):
        self.shop.draw(self)

    def overlay(self, title, subtitle):
        shade = pygame.Surface(CANVAS, pygame.SRCALPHA)
        shade.fill((6, 10, 16, 215))
        self.canvas.blit(shade, (0, 0))
        pygame.draw.rect(self.canvas, PANEL, (360, 200, 560, 400), border_radius=12)
        pygame.draw.rect(self.canvas, LINE, (360, 200, 560, 400), 1, border_radius=12)
        self.text(title, 640, 263, 48, CYAN, True)
        self.text(subtitle, 640, 320, 24, WHITE, True)

    def render(self):
        self.buttons = []
        self.canvas.fill(BG)
        if self.scene == "menu":
            self.draw_menu()
        elif self.scene == "tree":
            self.draw_tree()
        elif self.scene == "loadout":
            self.draw_loadout()
        else:
            self.draw_play()
            if self.intro_remaining > 0 and self.scene == "play":
                self.draw_boss_intro()
            if self.scene == "pause":
                self.overlay("PAUSED", "Take a breath. Your timer is frozen.")
                self.button("RESUME   /   ESC", (420, 379, 440, 52), "resume", accent=True)
                self.button("END RUN & BANK POINTS", (420, 447, 440, 52), "retire")
                self.button("SAVE & QUIT", (420, 515, 440, 52), "quit")
            elif self.scene == "result":
                self.overlay("LOOP BREACHED" if self.run.victory else "THE LOOP CONTINUES", self.run.reason)
                self.text(f"+{self.run.points} POINTS   /   {self.run.kills} KILLS   /   WAVE {self.run.wave}", 640, 369, 24, GOLD, True)
                self.text(f"Skillshots +{self.run.skillshot_bonus}   /   Multi-kills +{self.run.multikill_bonus}   /   Best burst {self.run.best_multikill}", 640, 399, 18, MUTED, True)
                self.button("PRACTICE AGAIN" if self.practice else "SPEND POINTS   /   SPACE", (420, 432, 440, 56), "practice" if self.practice else "tree", accent=True)
                self.button("BACK TO MENU" if self.practice else "TRY AGAIN", (420, 506, 440, 52), "menu" if self.practice else "start")
                counts = self.run.skillshot_counts
                self.text(f"Portal {counts['Portal']}   /   Ricochet {counts['Ricochet']}   /   Recall {counts['Recall']}", 640, 579, 18, MUTED, True)
        if self.notice:
            pygame.draw.rect(self.canvas, (75, 42, 40), (0, 0, 1280, 22))
            self.text(self.notice, 8, 2, 18, WHITE)
        if self.comparison:
            self.text("SANDBOX", 1060, 24, 20, WHITE)
            self.text("Save unchanged", 1060, 54, 18, MUTED)
        elif self.practice:
            self.text("PRACTICE", 1060, 24, 20, CYAN)
            self.text("Save unchanged", 1060, 54, 18, MUTED)
        # The side margins provide discoverable effect controls without covering combat.
        if self.scene not in ("menu", "loadout"):
            self.text("F5 SHAKE " + ("ON" if self.presentation.shake else "OFF"), 24, 683, 18, MUTED)
            self.text("F6 FLASH " + ("ON" if self.presentation.flashes else "OFF"), 24, 709, 18, MUTED)
            self.text("F7 TRAILS " + ("ON" if self.presentation.trails else "OFF"), 24, 735, 18, MUTED)
        self.presentation.apply(self.canvas)
        size = self.window.get_size()
        scale = min(size[0] / CANVAS[0], size[1] / CANVAS[1])
        dimensions = (max(1, round(CANVAS[0] * scale)), max(1, round(CANVAS[1] * scale)))
        self.window.fill(BG)
        if self.scaled_frame is None or self.scaled_frame.get_size() != dimensions:
            self.scaled_frame = pygame.Surface(dimensions).convert()
        pygame.transform.smoothscale(self.canvas, dimensions, self.scaled_frame)
        self.window.blit(self.scaled_frame, ((size[0] - dimensions[0]) // 2, (size[1] - dimensions[1]) // 2))
        pygame.display.flip()

    def mouse_position(self, pos):
        w, h = self.window.get_size()
        scale = min(w / CANVAS[0], h / CANVAS[1])
        return ((pos[0] - (w - CANVAS[0] * scale) / 2) / scale,
                (pos[1] - (h - CANVAS[1] * scale) / 2) / scale)

    def arena_position(self, pos):
        """Convert logical UI coordinates into original Unreal world units."""
        return ((pos[0] - ARENA.x) * WIDTH / ARENA.width,
                (pos[1] - ARENA.y) * HEIGHT / ARENA.height)

    def cancel_input(self):
        self.recall_keys.clear()
        self.run.stop_recall()
        self.run.charging = False
        self.run.charge = 0

    def bank(self):
        if self.run is not None and not self.result_banked:
            if not self.run_practice:
                bank_run(self.progress, self.run)
            self.result_banked = True
            if not self.run_practice:
                self.persist()

    def action(self, action):
        if action == "start":
            self.start()
        elif action == "practice":
            self.start(practice=True)
        elif action == "practice_boss":
            self.practice_boss = "tempest" if self.practice_boss == "boss" else "boss"
        elif action.startswith(("rank+:", "rank-:")):
            key = action.split(":", 1)[1]
            rank = self.progress.equipped_levels()[key]
            self.progress.equip(key, rank + (1 if action.startswith("rank+") else -1))
            self.persist()
        elif action == "loadout_off":
            for upgrade in UPGRADES:
                self.progress.equip(upgrade.key, 0)
            self.persist()
        elif action == "loadout_all":
            self.progress.active_levels.clear()
            self.persist()
        elif action == "mode":
            if self.original_mode:
                self.original_mode, self.endless = False, False
            elif not self.endless:
                self.endless = True
            else:
                self.original_mode, self.endless = True, False
        elif action in ("menu", "tree", "loadout"):
            self.shop.release()
            self.shop.dragging = False
            self.scene = action
            self.practice = False
        elif action == "resume":
            self.scene = "play"
        elif action == "retire":
            self.run.finish("You ended this attempt")
            self.bank()
            self.scene = "result"
        elif action == "quit":
            self.bank()
            self.running = False

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.action("quit")
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.shop.release()
            self.shop.dragging = False
            if self.scene == "play":
                self.cancel_input()
                self.scene = "pause"
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                if not self.fullscreen:
                    self.windowed_size = self.window.get_size()
                self.fullscreen = not self.fullscreen
                self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if self.fullscreen else pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            elif event.key in (pygame.K_F5, pygame.K_F6, pygame.K_F7):
                setting = {pygame.K_F5: "shake", pygame.K_F6: "flashes", pygame.K_F7: "trails"}[event.key]
                setattr(self.presentation, setting, not getattr(self.presentation, setting))
            elif event.key == pygame.K_HOME and self.scene == "tree":
                self.shop.reset_camera()
            elif event.key == pygame.K_m:
                self.audio.enabled = not self.audio.enabled
            elif event.key == pygame.K_RETURN and self.scene == "play" and self.intro_remaining > 0:
                self.intro_remaining = 0
            elif event.key == pygame.K_ESCAPE:
                if self.scene == "play":
                    self.cancel_input()
                    self.scene = "pause"
                elif self.scene == "pause":
                    self.scene = "play"
                elif self.scene == "menu":
                    self.action("quit")
                else:
                    self.shop.release()
                    self.scene = "menu"
            elif event.key == pygame.K_SPACE:
                if self.scene == "play":
                    if self.intro_remaining <= 0:
                        self.recall_keys.add("space")
                        self.run.recall()
                elif self.scene in ("menu", "tree"):
                    self.start()
                elif self.scene == "result":
                    if self.practice:
                        self.start(practice=True)
                    else:
                        self.scene = "tree"
        elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            self.recall_keys.discard("space")
            if self.run is not None and not self.recall_keys:
                self.run.stop_recall()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse = self.mouse_position(event.pos)
            if self.scene == "tree" and event.button in (2, 3):
                self.shop.dragging = True
                self.shop.release()
            elif self.scene == "tree" and event.button == 1 and self.shop.hit(self.mouse, self.progress):
                self.shop.begin(self.mouse, self.progress)
            elif self.scene == "play" and self.intro_remaining <= 0:
                if event.button == 1 and ARENA.collidepoint(self.mouse):
                    self.run.begin_charge()
                elif event.button == 3:
                    self.recall_keys.add("mouse")
                    self.run.recall()
            elif event.button == 1:
                for rect, action, enabled in self.buttons:
                    if enabled and rect.collidepoint(self.mouse):
                        self.action(action)
                        break
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.scene == "tree":
                if event.button == 1:
                    self.shop.release()
                elif event.button in (2, 3):
                    self.shop.dragging = False
            if event.button == 1 and self.scene == "play":
                self.run.release()
            elif event.button == 3:
                self.recall_keys.discard("mouse")
                if self.run is not None and not self.recall_keys:
                    self.run.stop_recall()
        elif event.type == pygame.MOUSEWHEEL and self.scene == "tree":
            self.shop.zoom_at(event.y, self.mouse)
        elif event.type == pygame.MOUSEMOTION and self.scene == "tree" and self.shop.dragging:
            w, h = self.window.get_size()
            scale = min(w / CANVAS[0], h / CANVAS[1])
            self.shop.pan((event.rel[0] / scale, event.rel[1] / scale))

    def update(self, dt):
        self.animation += dt
        self.shot_pulse = max(0, self.shot_pulse - dt * 9)
        battle = self.run is not None and any(e.warden for e in self.run.enemies) and self.scene in ("play", "pause")
        self.audio.sync_music(battle, paused=self.scene == "pause")
        if self.scene == "tree":
            keys = pygame.key.get_pressed()
            movement = (int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
                        int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
            purchase = self.shop.update(dt, self.mouse, self.progress, movement)
            if purchase and self.progress.buy(purchase):
                self.shop.bought(purchase)
                self.audio.play("buy")
                self.persist()
        if self.scene == "play":
            if self.intro_remaining > 0:
                self.intro_remaining = max(0, self.intro_remaining - dt)
                return
            keys = pygame.key.get_pressed()
            movement = (int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
                        int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
            if self.recall_keys:
                self.run.recall()
            self.run.update(dt, movement, self.arena_position(self.mouse))
            boss = next((e for e in self.run.enemies if e.warden and e.id not in self.seen_bosses), None)
            if boss is not None:
                self.begin_boss_intro(boss)
            for name in set(self.run.events):
                if name == "shoot":
                    self.shot_pulse = 1.0
                self.audio.play(name)
            self.run.events.clear()
            if self.run.over:
                self.bank()
                self.scene = "result"

    def loop(self, frames=0, screenshot=None):
        count = 0
        while self.running:
            dt = min(self.clock.tick(60) / 1000, .1)
            self.mouse = self.mouse_position(pygame.mouse.get_pos())
            for event in pygame.event.get():
                self.handle(event)
            if not self.running:
                break
            self.update(dt)
            self.render()
            count += 1
            if frames and count >= frames:
                break
        if screenshot:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.canvas, str(screenshot))
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Loop Archer / Python reconstruction")
    parser.add_argument("--save", type=Path, default=Path(__file__).resolve().parent.parent / "saves" / "progress.json")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--headless", action="store_true", help="Use SDL dummy drivers for automated rendering")
    parser.add_argument("--frames", type=int, default=0, help="Exit after a fixed number of frames")
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--scene", choices=("menu", "play", "tree", "loadout"), default="menu")
    parser.add_argument("--windowed", action="store_true", help="Start in a resizable window instead of fullscreen")
    parser.add_argument("--comparison", action="store_true", help="Read-only shop/combat comparison with temporary progress")
    parser.add_argument("--boss-practice", action="store_true", help="Practice the selected boss with equipped upgrades; never writes progress")
    parser.add_argument("--boss", choices=("warden", "tempest"), default="warden")
    args = parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    app = App(args.save, headless=args.headless, seed=args.seed, windowed=args.windowed)
    app.practice_boss = "boss" if args.boss == "warden" else "tempest"
    if args.headless:
        # Rendering checks must never bank points into the player's real profile.
        app.save_allowed = False
    if args.comparison:
        app.comparison = True
        app.save_allowed = False
        app.progress = Progress(points=100, levels={"damage": 1, "charge": 1, "time": 1, "recall": 1, "movement": 1})
    if args.boss_practice:
        app.start(practice=True)
    elif args.scene == "play":
        app.start()
    else:
        app.scene = "tree" if args.comparison and args.scene == "menu" else args.scene
    app.loop(args.frames, args.screenshot)
