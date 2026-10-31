"""Spatial skill tree using the original map's placed node coordinates.

The camera, hover, discovery and purchase animation are presentation state.
Progress and price rules stay in progression.py.
"""
import json
import math
from pathlib import Path
import pygame
from .progression import UPGRADES, BY_KEY

POSITIONS = json.loads((Path(__file__).resolve().parent.parent / "assets/tree_positions.json").read_text())
VIEW = pygame.Rect(240, 0, 800, 800)
WHITE, DIM, RED = (229, 240, 237), (132, 153, 164), (255, 104, 109)
ACCENT = (108, 226, 210)


def node_icon(key):
    """Render vector glyphs at 4x resolution; cached downsampling antialiases edges."""
    s = pygame.Surface((192, 192), pygame.SRCALPHA)
    c = WHITE
    def point(value):
        return pygame.Vector2(value) * 4
    def line(a, b, width=3):
        pygame.draw.line(s, c, point(a), point(b), width * 4)
    def polygon(points, width=0):
        pygame.draw.polygon(s, c, [point(v) for v in points], width * 4)
    def circle(center, radius, width=0):
        pygame.draw.circle(s, c, point(center), radius * 4, width * 4)
    def arc(rect, start, end, width):
        pygame.draw.arc(s, c, tuple(v * 4 for v in rect), start, end, width * 4)
    def arrow(x=24, y=24, angle=-45):
        direction = pygame.Vector2(1, 0).rotate(angle)
        side = direction.rotate(90)
        center = pygame.Vector2(x, y)
        tip, tail = center + direction * 17, center - direction * 16
        line(tail, tip, 4)
        polygon([tip + direction * 4, tip - direction * 7 + side * 7, tip - direction * 7 - side * 7])
        line(tail + side * 5, tail + direction * 7, 3)
    if key in ("damage", "speed", "full_charge"):
        arrow()
        if key == "speed":
            line((3, 31), (14, 20), 2)
            line((7, 40), (20, 27), 2)
        if key == "full_charge":
            line((34, 29), (34, 43))
            line((27, 36), (41, 36))
    elif key == "multishot":
        for x in (12, 24, 36):
            arrow(x, 25, -90)
    elif key in ("time", "time_kill", "passive"):
        circle((24, 26), 16, 3)
        line((24, 26), (24, 15))
        line((24, 26), (32, 29))
        line((19, 5), (29, 5), 4)
        if key != "time":
            line((36, 7), (36, 19))
            line((30, 13), (42, 13))
    elif key in ("shield", "safe"):
        polygon([(8, 9), (24, 5), (40, 9), (37, 30), (24, 44), (11, 30)], 3)
        if key == "safe":
            line((16, 25), (22, 31))
            line((22, 31), (33, 18))
    elif key in ("reward", "nugget", "recall_reward"):
        polygon([(24, 7), (41, 24), (24, 41), (7, 24)])
        if key == "recall_reward":
            pygame.draw.circle(s, (25, 25, 30), point((24, 24)), 32, 12)
    elif key in ("movement", "slow"):
        polygon([(12, 7), (24, 7), (24, 27), (38, 30), (40, 40), (11, 40), (8, 32)])
        if key == "slow":
            line((2, 13), (8, 13), 2)
            line((2, 20), (8, 20), 2)
    elif key in ("recall", "bounce"):
        arc((7, 7, 34, 34), .4, 5.7, 4)
        polygon([(6, 6), (22, 8), (8, 21)])
        if key == "bounce":
            line((5, 43), (43, 43))
    elif key == "charge":
        polygon([(27, 3), (10, 27), (24, 27), (19, 46), (39, 20), (26, 20)])
    elif key == "more_enemies":
        for x, y in ((15, 15), (32, 27)):
            polygon([(x, y - 10), (x + 10, y), (x, y + 10), (x - 10, y)])
    else:  # Sale tag
        polygon([(5, 21), (20, 6), (40, 6), (40, 28), (24, 43)], 3)
        circle((32, 14), 3)
        line((15, 30), (29, 16), 2)
    return s


class SkillTree:
    HOLD_SECONDS = .5

    def __init__(self):
        self.camera = pygame.Vector2()
        self.zoom = .8
        self.hovered = None
        self.holding = None
        self.hold_time = 0.0
        self.purchase_sent = False
        self.time = 0.0
        self.appeared = {}
        self.pulses = {}
        self.icons = {u.key: node_icon(u.key) for u in UPGRADES}
        self.scaled_icons = {}
        self.dragging = False

    def visible(self, progress):
        # Saved descendants remain visible even for unusual older profiles.
        return {u.key for u in UPGRADES if progress.unlocked(u.key) or progress.level(u.key)}

    def point(self, key):
        return pygame.Vector2(VIEW.center) + (pygame.Vector2(POSITIONS[key]) - self.camera) * self.zoom

    def rect(self, key):
        size = max(28, round(100 * self.zoom))
        return pygame.Rect(0, 0, size, size).move(self.point(key) - pygame.Vector2(size / 2, size / 2))

    def hit(self, mouse, progress):
        if not VIEW.collidepoint(mouse) or mouse[1] < 100 or mouse[1] > 706:
            return None
        return next((key for key in self.visible(progress) if self.rect(key).collidepoint(mouse)), None)

    def begin(self, mouse, progress):
        self.holding = self.hit(mouse, progress)
        self.hold_time = 0
        self.purchase_sent = False

    def release(self):
        self.holding = None
        self.hold_time = 0
        self.purchase_sent = False

    def reset_camera(self):
        self.camera.update(0, 0)
        self.zoom = .8

    def zoom_at(self, direction, mouse):
        anchor = (pygame.Vector2(mouse) - VIEW.center) / self.zoom + self.camera
        self.zoom = max(.32, min(1.35, self.zoom * (1.12 ** direction)))
        self.camera = anchor - (pygame.Vector2(mouse) - VIEW.center) / self.zoom

    def pan(self, motion):
        self.camera -= pygame.Vector2(motion) / self.zoom
        self.release()

    def update(self, dt, mouse, progress, movement=(0, 0)):
        self.time += dt
        move = pygame.Vector2(movement)
        if move:
            self.camera += move.normalize() * 650 * dt / self.zoom
            self.release()
        self.camera.x = max(-1200, min(1100, self.camera.x))
        self.camera.y = max(-1000, min(1250, self.camera.y))
        self.hovered = self.hit(mouse, progress)
        for key in self.visible(progress):
            self.appeared.setdefault(key, self.time)
        if self.holding != self.hovered:
            self.release()
        if self.holding and not self.purchase_sent:
            self.hold_time += dt
            if self.hold_time >= self.HOLD_SECONDS:
                self.purchase_sent = True
                return self.holding
        return None

    def bought(self, key):
        self.pulses[key] = self.time

    def draw(self, app):
        surface, progress = app.canvas, app.progress
        visible = self.visible(progress)
        surface.fill((12, 16, 22))
        # The board moves continuously with the camera, so the nodes sit in a
        # world rather than in screen-space UI cards.
        surface.set_clip(VIEW)
        tile = max(15, round(150 * self.zoom))
        origin = pygame.Vector2(VIEW.center) - self.camera * self.zoom
        start_x = VIEW.x - tile + int((origin.x - VIEW.x) % tile)
        start_y = -tile + int(origin.y % tile)
        for y in range(start_y, VIEW.bottom, tile):
            for x in range(start_x, VIEW.right, tile):
                index = round((x - origin.x) / tile) + round((y - origin.y) / tile)
                pygame.draw.rect(surface, (17, 25, 33), (x, y, tile, tile))
                pygame.draw.line(surface, (25, 37, 46), (x, y), (x + tile, y))
                pygame.draw.line(surface, (25, 37, 46), (x, y), (x, y + tile))
        for u in UPGRADES:
            if u.key not in visible or not u.parent or u.parent not in visible:
                continue
            a, b = self.point(u.parent), self.point(u.key)
            age = min(1, (self.time - self.appeared.get(u.key, self.time)) / .35)
            pygame.draw.line(surface, (32, 63, 71), a, b, max(3, round(5 * self.zoom)))
            pygame.draw.aaline(surface, ACCENT, a, a.lerp(b, age))
        for key in visible:
            rect = self.rect(key)
            age = min(1, (self.time - self.appeared.get(key, 0)) / .3)
            hovered = self.hovered == key
            pulse = max(0, 1 - (self.time - self.pulses.get(key, -10)) / .4)
            scale = (.8 + .2 * age) * (1.1 if hovered else 1) * (1 + .18 * pulse)
            if self.holding == key:
                scale *= 1 - .12 * min(1, self.hold_time / self.HOLD_SECONDS)
            rect.inflate_ip(rect.width * (scale - 1), rect.height * (scale - 1))
            rect.y += round(math.sin(self.time * 1.7 + len(key)) * 2)
            maxed = progress.level(key) == BY_KEY[key].max_level
            tint = ACCENT if maxed or hovered else (94, 123, 137)
            pygame.draw.rect(surface, (6, 12, 18), rect.move(0, 5), border_radius=14)
            pygame.draw.rect(surface, (29, 49, 58) if hovered else (23, 35, 45), rect, border_radius=14)
            pygame.draw.rect(surface, tint, rect, 2 if hovered else 1, border_radius=14)
            icon_size = max(12, round(rect.width * .62))
            cache_key = (key, icon_size)
            if cache_key not in self.scaled_icons:
                self.scaled_icons[cache_key] = pygame.transform.smoothscale(self.icons[key], (icon_size, icon_size))
                if len(self.scaled_icons) > 256:
                    self.scaled_icons.clear()
                    self.scaled_icons[cache_key] = pygame.transform.smoothscale(self.icons[key], (icon_size, icon_size))
            icon = self.scaled_icons[cache_key]
            surface.blit(icon, icon.get_rect(center=rect.center))
            if progress.level(key):
                pygame.draw.line(surface, tint, (rect.left, rect.bottom + 8),
                                 (rect.left + rect.width * progress.level(key) / BY_KEY[key].max_level, rect.bottom + 8), 2)
            if pulse:
                pygame.draw.rect(surface, WHITE, rect.inflate(24 * pulse, 24 * pulse), 1)
        surface.blit(app.vignette, VIEW)
        surface.set_clip(None)
        self.tooltip(app)
        app.text("SKILL TREE", 25, 65, 24, ACCENT)
        app.wrapped("Explore a branch. Make the next shot yours.", 25, 116, 180, 20, DIM)
        app.diamond((VIEW.left + 48, 52), 14, ACCENT)
        app.hud_text(progress.points, VIEW.left + 83, 15, 64, WHITE)
        app.text("WASD move     Wheel zoom     Home center", VIEW.centerx, 742, 18, DIM, True)
        app.text("HOLD TO BUY", VIEW.centerx, 708, 20, WHITE, True)
        app.button("SPACE / NEXT LOOP", (VIEW.centerx - 160, 764, 320, 32), "start", accent=True)

    def tooltip(self, app):
        key = self.hovered
        if not key:
            return
        u, p = BY_KEY[key], app.progress
        center = self.point(key)
        # A stable details card keeps the map and hovered node unobscured.
        x, y = 1060, 160
        pygame.draw.rect(app.canvas, (21, 31, 41), (x - 10, y - 16, 220, 385), border_radius=12)
        maxed = p.level(key) >= u.max_level
        end = app.wrapped(u.name, x, y, 195, 24, WHITE)
        app.text(f"RANK {p.level(key)} / {u.max_level}", x, end + 15, 18, ACCENT)
        app.wrapped(u.description, x, end + 60, 195, 18, DIM)
        price = "COMPLETE" if maxed else f"{p.cost(key)} points"
        rect = pygame.Rect(x, y + 280, 196, 42)
        affordable = not maxed and p.points >= p.cost(key)
        pygame.draw.rect(app.canvas, (28, 51, 58), rect, border_radius=7)
        app.text(price, *rect.center, 20, ACCENT if affordable or maxed else RED, True)
        if self.holding == key and affordable:
            pygame.draw.rect(app.canvas, WHITE, (rect.x, rect.bottom + 5, rect.width * min(1, self.hold_time / self.HOLD_SECONDS), 3))
