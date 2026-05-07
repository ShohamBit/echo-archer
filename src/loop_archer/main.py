from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, sin

import pygame

from loop_archer import config
from loop_archer.input import InputState
from loop_archer.layout import (
    arena_radius_for_screen,
    dash_indicator_rect_for_screen,
    health_bar_rect_for_screen,
)
from loop_archer.models import EnemyKind, GameMode, Vec2
from loop_archer.persistence import load_game, save_game
from loop_archer.systems import begin_next_loop, current_echo_decay_rate, update_world
from loop_archer.upgrades import UPGRADE_DEFINITIONS, apply_upgrade


BG = (12, 14, 20)
ARENA_FILL = (22, 26, 36)
ARENA_LINE = (74, 93, 121)
PLAYER = (245, 180, 82)
PLAYER_HIT = (255, 245, 220)
ENEMY = (208, 72, 78)
ENEMY_HIT = (255, 170, 160)
ENEMY_CORE = (102, 27, 37)
FAST_ENEMY = (225, 96, 210)
FAST_ENEMY_HIT = (255, 180, 244)
FAST_ENEMY_CORE = (92, 31, 103)
ARROW = (246, 218, 128)
SHARD = (103, 210, 255)
TEXT = (229, 235, 244)
MUTED = (142, 154, 174)
PANEL = (22, 25, 34)
BUTTON = (63, 93, 142)
BUTTON_HOVER = (82, 121, 184)
LOCKED = (59, 65, 78)
UPGRADE_BRANCHES = ("Archer", "Survivor", "Echo")
BRANCH_ACCENTS = {
    "Archer": (246, 218, 128),
    "Survivor": (118, 214, 168),
    "Echo": (103, 210, 255),
}


@dataclass(frozen=True)
class UpgradeScreenLayout:
    panel_rect: pygame.Rect
    restart_button_rect: pygame.Rect
    branch_header_positions: dict[str, tuple[int, int]]
    card_rects: dict[str, pygame.Rect]
    compact_cards: bool


def upgrade_screen_layout(
    width: int,
    height: int,
    upgrades,
) -> UpgradeScreenLayout:
    margin_x = 24 if width < 1000 else 48
    margin_y = 20 if height < 680 else 28
    panel_width = min(width - margin_x * 2, 1140)
    panel_height = min(height - margin_y * 2, 680)
    panel_rect = pygame.Rect(
        (width - panel_width) // 2,
        (height - panel_height) // 2,
        panel_width,
        panel_height,
    )
    restart_button_rect = pygame.Rect(0, 0, 200, 48)
    restart_button_rect.center = (width // 2, panel_rect.bottom - 36)

    side_padding = 28 if width < 1000 else 40
    column_gap = 14 if width < 1000 else 18
    column_width = int(
        (panel_rect.width - side_padding * 2 - column_gap * 2) / len(UPGRADE_BRANCHES)
    )
    branch_header_y = panel_rect.y + 112
    card_start_y = panel_rect.y + 138
    card_gap = 6 if height < 680 else 8

    by_branch = {branch: [] for branch in UPGRADE_BRANCHES}
    for upgrade in upgrades:
        by_branch.setdefault(upgrade.branch, []).append(upgrade)
    max_cards = max((len(items) for items in by_branch.values()), default=1)
    available_height = restart_button_rect.top - 12 - card_start_y
    card_height = int(
        min(64, (available_height - card_gap * max(0, max_cards - 1)) / max_cards)
    )
    card_height = max(34, card_height)
    compact_cards = card_height < 50

    branch_header_positions: dict[str, tuple[int, int]] = {}
    card_rects: dict[str, pygame.Rect] = {}
    for column, branch in enumerate(UPGRADE_BRANCHES):
        x = panel_rect.x + side_padding + column * (column_width + column_gap)
        branch_header_positions[branch] = (x, branch_header_y)
        for row, upgrade in enumerate(by_branch.get(branch, [])):
            card_rects[upgrade.id] = pygame.Rect(
                x,
                card_start_y + row * (card_height + card_gap),
                column_width,
                card_height,
            )

    return UpgradeScreenLayout(
        panel_rect=panel_rect,
        restart_button_rect=restart_button_rect,
        branch_header_positions=branch_header_positions,
        card_rects=card_rects,
        compact_cards=compact_cards,
    )


class Button:
    def __init__(self, rect: pygame.Rect, label: str) -> None:
        self.rect = rect
        self.label = label

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        mouse = pygame.mouse.get_pos()
        color = BUTTON_HOVER if self.rect.collidepoint(mouse) else BUTTON
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (120, 150, 198), self.rect, 2, border_radius=6)
        text = font.render(self.label, True, TEXT)
        surface.blit(text, text.get_rect(center=self.rect.center))

    def was_clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Echo Archer")
        self.fullscreen = True
        self.windowed_size = (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small_font = pygame.font.SysFont("consolas", 16)
        self.tiny_font = pygame.font.SysFont("consolas", 13)
        self.big_font = pygame.font.SysFont("consolas", 48, bold=True)
        self.state = load_game()
        self.open_upgrades_button = Button(pygame.Rect(0, 0, 260, 48), "Open Skill Tree")
        self.restart_button = Button(pygame.Rect(0, 0, 200, 48), "Start Loop")
        self.upgrade_card_rects: dict[str, pygame.Rect] = {}
        self._layout_buttons()
        self._sync_arena_radius()

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(config.FPS) / 1000.0
            input_state = self._read_input()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game(self.state)
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F11:
                        self._toggle_fullscreen()
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.windowed_size = event.size
                    self.screen = pygame.display.set_mode(
                        self.windowed_size, pygame.RESIZABLE
                    )
                    self._layout_buttons()
                    self._sync_arena_radius()
                else:
                    self._handle_event(event)

            update_world(self.state, input_state, dt)
            if self.state.mode is GameMode.DEAD_SUMMARY:
                save_game(self.state)
            self._draw()

        pygame.quit()

    def _read_input(self) -> InputState:
        keys = pygame.key.get_pressed()
        move = Vec2(
            float(keys[pygame.K_d] or keys[pygame.K_RIGHT])
            - float(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            float(keys[pygame.K_s] or keys[pygame.K_DOWN])
            - float(keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        mouse_world = self._screen_to_world(Vec2(*pygame.mouse.get_pos()))
        shoot = pygame.mouse.get_pressed(num_buttons=3)[0]
        dash = keys[pygame.K_SPACE]
        return InputState(move=move, aim_world=mouse_world, shoot=shoot, dash=dash)

    def _handle_event(self, event: pygame.event.Event) -> None:
        if self.state.mode is GameMode.DEAD_SUMMARY:
            if self.open_upgrades_button.was_clicked(event):
                self.state.mode = GameMode.UPGRADE
        elif self.state.mode is GameMode.UPGRADE:
            if self.restart_button.was_clicked(event):
                begin_next_loop(self.state)
                save_game(self.state)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for upgrade_id, rect in self.upgrade_card_rects.items():
                    if rect.collidepoint(event.pos):
                        apply_upgrade(self.state, upgrade_id)
                        save_game(self.state)
                        break

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self._layout_buttons()
        self._sync_arena_radius()

    def _layout_buttons(self) -> None:
        width, height = self.screen.get_size()
        cx = width // 2
        cy = height // 2
        self.open_upgrades_button.rect.center = (cx, cy + 112)
        self.restart_button.rect.center = (cx, cy + 200)

    def _sync_arena_radius(self) -> None:
        width, height = self.screen.get_size()
        self.state.arena_radius = arena_radius_for_screen(width, height)

    @property
    def screen_center(self) -> Vec2:
        width, height = self.screen.get_size()
        return Vec2(width / 2, height / 2)

    def _world_to_screen(self, position: Vec2) -> tuple[int, int]:
        screen = self.screen_center + position
        return int(screen.x), int(screen.y)

    def _screen_to_world(self, position: Vec2) -> Vec2:
        return position - self.screen_center

    def _draw(self) -> None:
        self.screen.fill(BG)
        self._draw_playfield()
        self._draw_hud()

        if self.state.mode is GameMode.DEAD_SUMMARY:
            self._draw_death_summary()
        elif self.state.mode is GameMode.UPGRADE:
            self._draw_upgrade_screen()

        pygame.display.flip()

    def _draw_playfield(self) -> None:
        center = self._world_to_screen(Vec2())
        arena_radius = int(self.state.arena_radius)
        pygame.draw.circle(self.screen, ARENA_FILL, center, arena_radius)
        pygame.draw.circle(self.screen, ARENA_LINE, center, arena_radius, 3)
        pygame.draw.circle(self.screen, (36, 45, 61), center, int(arena_radius * 0.34), 1)
        pygame.draw.circle(self.screen, (36, 45, 61), center, int(arena_radius * 0.62), 1)

        for pickup in self.state.pickups:
            pygame.draw.circle(
                self.screen,
                SHARD,
                self._world_to_screen(pickup.position),
                int(pickup.radius),
            )

        for arrow in self.state.arrows:
            start = arrow.position - arrow.direction * 16
            end = arrow.position + arrow.direction * 12
            pygame.draw.line(
                self.screen,
                ARROW,
                self._world_to_screen(start),
                self._world_to_screen(end),
                4,
            )

        for enemy in self.state.enemies:
            if enemy.kind is EnemyKind.FAST:
                self._draw_fast_enemy(enemy)
            else:
                self._draw_chaser(enemy)

        color = PLAYER_HIT if (
            self.state.player.hit_flash_timer > 0
            or self.state.player.dash_flash_timer > 0
        ) else PLAYER
        player_pos = self._world_to_screen(self.state.player.position)
        pygame.draw.circle(self.screen, color, player_pos, int(self.state.player.radius))
        aim = self.state.player.aim_direction
        bow_tip = self.state.player.position + aim * 30
        pygame.draw.line(self.screen, ARROW, player_pos, self._world_to_screen(bow_tip), 4)
        self._draw_loop_glyph(center)

    def _draw_chaser(self, enemy) -> None:
        color = ENEMY_HIT if enemy.hit_flash_timer > 0 else ENEMY
        to_player = (self.state.player.position - enemy.position).normalized()
        if to_player.length() <= 0:
            to_player = Vec2(1, 0)
        angle = atan2(to_player.y, to_player.x)
        radius = enemy.radius
        tip = enemy.position + Vec2(cos(angle), sin(angle)) * (radius * 1.35)
        left = enemy.position + Vec2(
            cos(angle + 2.45), sin(angle + 2.45)
        ) * radius
        right = enemy.position + Vec2(
            cos(angle - 2.45), sin(angle - 2.45)
        ) * radius
        points = [
            self._world_to_screen(tip),
            self._world_to_screen(left),
            self._world_to_screen(right),
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, (110, 33, 45), points, 3)
        core_center = self._world_to_screen(enemy.position)
        pygame.draw.circle(self.screen, ENEMY_CORE, core_center, max(5, int(radius * 0.32)))
        eye = enemy.position + to_player * (radius * 0.44)
        pygame.draw.circle(
            self.screen,
            (255, 195, 158),
            self._world_to_screen(eye),
            max(3, int(radius * 0.14)),
        )

    def _draw_fast_enemy(self, enemy) -> None:
        color = FAST_ENEMY_HIT if enemy.hit_flash_timer > 0 else FAST_ENEMY
        to_player = (self.state.player.position - enemy.position).normalized()
        if to_player.length() <= 0:
            to_player = Vec2(1, 0)
        angle = atan2(to_player.y, to_player.x)
        side_angle = angle + 1.5708
        radius = enemy.radius
        points = [
            enemy.position + Vec2(cos(angle), sin(angle)) * (radius * 1.55),
            enemy.position + Vec2(cos(side_angle), sin(side_angle)) * (radius * 0.95),
            enemy.position - Vec2(cos(angle), sin(angle)) * (radius * 1.15),
            enemy.position - Vec2(cos(side_angle), sin(side_angle)) * (radius * 0.95),
        ]
        screen_points = [self._world_to_screen(point) for point in points]
        pygame.draw.polygon(self.screen, color, screen_points)
        pygame.draw.polygon(self.screen, (125, 41, 139), screen_points, 3)
        pygame.draw.circle(
            self.screen,
            FAST_ENEMY_CORE,
            self._world_to_screen(enemy.position),
            max(4, int(radius * 0.3)),
        )

    def _draw_loop_glyph(self, center: tuple[int, int]) -> None:
        radius = 54
        for offset in (0, 3.14):
            points = []
            for i in range(28):
                t = offset + i / 27 * 4.7
                points.append(
                    (
                        int(center[0] + cos(t) * radius),
                        int(center[1] + sin(t) * radius * 0.55),
                    )
                )
            pygame.draw.lines(self.screen, (45, 63, 92), False, points, 2)

    def _draw_hud(self) -> None:
        width, height = self.screen.get_size()
        self._draw_health_bar(width, height)
        self._draw_dash_indicator(width, height)
        self._text(f"Loop {self.state.current_loop:02d}", 28, 26, self.font)
        self._center_text(f"{_format_time(self.state.run_timer)}", 34, self.font)
        self._text(f"Run shards {self.state.run_shards}", 28, 58, self.small_font, SHARD)
        self._text(f"Total shards {self.state.total_shards}", 28, 80, self.small_font, TEXT)
        self._text(f"Damage {self.state.player_stats.damage}", 28, 102, self.small_font, ARROW)
        decay_rate = current_echo_decay_rate(
            self.state.run_timer,
            self.state.player_stats,
        )
        decay_label = (
            "Echo Decay: Grace"
            if decay_rate <= 0
            else f"Echo Decay: -{decay_rate:.2f} HP/s"
        )
        self._text(decay_label, 28, 124, self.small_font, MUTED)
        best = self.small_font.render(
            f"Best {_format_time(self.state.best_time)}", True, MUTED
        )
        self.screen.blit(best, (width - best.get_width() - 28, 28))

    def _draw_health_bar(self, width: int, height: int) -> None:
        x, y, bar_width, bar_height = health_bar_rect_for_screen(width, height)
        health_ratio = max(
            0.0,
            min(1.0, self.state.player.hp / self.state.player_stats.max_hp),
        )
        shell = pygame.Rect(x - 4, y - 4, bar_width + 8, bar_height + 8)
        track = pygame.Rect(x, y, bar_width, bar_height)
        fill = pygame.Rect(x, y, int(bar_width * health_ratio), bar_height)

        pygame.draw.rect(self.screen, (14, 16, 22), shell, border_radius=8)
        pygame.draw.rect(self.screen, (45, 48, 60), track, border_radius=6)
        pygame.draw.rect(self.screen, (214, 72, 88), fill, border_radius=6)
        pygame.draw.rect(self.screen, (238, 188, 164), shell, 2, border_radius=8)

    def _draw_dash_indicator(self, width: int, height: int) -> None:
        x, y, bar_width, bar_height = dash_indicator_rect_for_screen(width, height)
        cooldown = self.state.player_stats.dash_cooldown
        ready_ratio = 1.0
        if cooldown > 0:
            ready_ratio = 1.0 - (
                self.state.player.dash_cooldown_timer / cooldown
            )
        ready_ratio = max(0.0, min(1.0, ready_ratio))

        shell = pygame.Rect(x - 3, y - 3, bar_width + 6, bar_height + 6)
        track = pygame.Rect(x, y, bar_width, bar_height)
        fill = pygame.Rect(x, y, int(bar_width * ready_ratio), bar_height)
        color = (111, 205, 255) if ready_ratio >= 1.0 else (74, 114, 153)

        pygame.draw.rect(self.screen, (14, 16, 22), shell, border_radius=6)
        pygame.draw.rect(self.screen, (45, 48, 60), track, border_radius=5)
        pygame.draw.rect(self.screen, color, fill, border_radius=5)
        pygame.draw.rect(self.screen, (146, 179, 212), shell, 1, border_radius=6)
        label = self.small_font.render("Dash", True, MUTED)
        self.screen.blit(label, (x, y - 22))

    def _draw_death_summary(self) -> None:
        width, height = self.screen.get_size()
        self._draw_overlay_panel(width // 2 - 260, height // 2 - 190, 520, 380)
        summary = self.state.last_run_summary
        self._center_text("LOOP FAILED", height // 2 - 130, self.big_font)
        reason = summary.death_reason.value if summary.death_reason else "Unknown"
        self._center_text(reason, height // 2 - 74, self.font, MUTED)
        self._center_text(
            f"Time survived: {_format_time(summary.time_survived)}",
            height // 2 - 28,
            self.font,
        )
        self._center_text(f"Enemies defeated: {summary.enemies_defeated}", height // 2 + 4, self.font)
        self._center_text(f"Shards gained: {summary.shards_gained}", height // 2 + 36, self.font, SHARD)
        self.open_upgrades_button.draw(self.screen, self.font)

    def _draw_upgrade_screen(self) -> None:
        width, height = self.screen.get_size()
        layout = upgrade_screen_layout(width, height, UPGRADE_DEFINITIONS.values())
        panel = layout.panel_rect
        self._draw_overlay_panel(panel.x, panel.y, panel.width, panel.height)
        self._center_text("SKILL TREE", panel.y + 38, self.big_font)
        self._center_text(
            f"Available shards: {self.state.total_shards}",
            panel.y + 84,
            self.font,
            SHARD,
        )

        self.upgrade_card_rects = {}
        for branch, position in layout.branch_header_positions.items():
            accent = BRANCH_ACCENTS.get(branch, MUTED)
            self._text(branch.upper(), position[0], position[1], self.small_font, accent)
            underline = pygame.Rect(position[0], position[1] + 21, 56, 2)
            pygame.draw.rect(self.screen, accent, underline, border_radius=1)

        for upgrade in UPGRADE_DEFINITIONS.values():
            rect = layout.card_rects[upgrade.id]
            self.upgrade_card_rects[upgrade.id] = rect
            self._draw_upgrade_card(rect, upgrade, layout.compact_cards)

        self.restart_button.rect = layout.restart_button_rect
        self.restart_button.draw(self.screen, self.font)

    def _draw_upgrade_card(
        self,
        rect: pygame.Rect,
        upgrade,
        compact: bool = False,
    ) -> None:
        owned = upgrade.id in self.state.owned_upgrades
        missing_prereq = any(
            item not in self.state.owned_upgrades for item in upgrade.prerequisites
        )
        affordable = self.state.total_shards >= upgrade.cost
        can_buy = not owned and not missing_prereq and affordable

        mouse = pygame.mouse.get_pos()
        if owned:
            fill = (28, 48, 42)
            border = (94, 174, 131)
        elif can_buy and rect.collidepoint(mouse):
            fill = (44, 57, 80)
            border = (136, 164, 218)
        elif can_buy:
            fill = (31, 36, 48)
            border = (101, 128, 172)
        else:
            fill = (27, 30, 38)
            border = (66, 72, 88)

        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        pygame.draw.rect(
            self.screen,
            BRANCH_ACCENTS.get(upgrade.branch, border),
            pygame.Rect(rect.x, rect.y, 4, rect.height),
            border_top_left_radius=6,
            border_bottom_left_radius=6,
        )
        pygame.draw.rect(self.screen, border, rect, 1, border_radius=6)

        if owned:
            status = "Owned"
        elif missing_prereq:
            status = "Locked"
        elif affordable:
            status = f"Buy: {upgrade.cost}"
        else:
            status = f"Need: {upgrade.cost}"
        status_color = SHARD if can_buy else MUTED

        name_font = self.small_font if not compact else self.tiny_font
        body_font = self.small_font if not compact else self.tiny_font
        self._text_fit(
            upgrade.name,
            rect.x + 12,
            rect.y + (7 if not compact else 5),
            rect.width - 24,
            name_font,
            TEXT,
        )

        if compact:
            self._text_fit(
                status,
                rect.x + 12,
                rect.y + 22,
                rect.width - 24,
                body_font,
                status_color,
            )
            return

        self._text_fit(
            upgrade.description,
            rect.x + 12,
            rect.y + 30,
            rect.width - 24,
            body_font,
            ARROW,
        )
        self._text_fit(
            status,
            rect.x + 12,
            rect.y + rect.height - 21,
            rect.width - 24,
            body_font,
            status_color,
        )

    def _draw_overlay_panel(self, x: int, y: int, w: int, h: int) -> None:
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=8)
        pygame.draw.rect(self.screen, (88, 105, 137), rect, 2, border_radius=8)

    def _text(
        self,
        label: str,
        x: int,
        y: int,
        font: pygame.font.Font,
        color: tuple[int, int, int] = TEXT,
    ) -> None:
        self.screen.blit(font.render(label, True, color), (x, y))

    def _text_fit(
        self,
        label: str,
        x: int,
        y: int,
        max_width: int,
        font: pygame.font.Font,
        color: tuple[int, int, int] = TEXT,
    ) -> None:
        fitted = label
        if font.size(fitted)[0] > max_width:
            while fitted and font.size(f"{fitted}...")[0] > max_width:
                fitted = fitted[:-1]
            fitted = f"{fitted}..." if fitted else "..."
        self._text(fitted, x, y, font, color)

    def _center_text(
        self,
        label: str,
        y: int,
        font: pygame.font.Font,
        color: tuple[int, int, int] = TEXT,
    ) -> None:
        text = font.render(label, True, color)
        width, _ = self.screen.get_size()
        self.screen.blit(text, text.get_rect(center=(width // 2, y)))


def _format_time(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def main() -> None:
    GameApp().run()


if __name__ == "__main__":
    main()
