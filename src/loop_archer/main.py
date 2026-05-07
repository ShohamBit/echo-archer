from __future__ import annotations

from math import atan2, cos, sin

import pygame

from loop_archer import config
from loop_archer.input import InputState
from loop_archer.models import GameMode, GameState, Vec2
from loop_archer.persistence import load_game, save_game
from loop_archer.systems import begin_next_loop, update_world
from loop_archer.upgrades import UPGRADE_DEFINITIONS, apply_upgrade


SCREEN_CENTER = Vec2(config.WINDOW_WIDTH / 2, config.WINDOW_HEIGHT / 2)
BG = (12, 14, 20)
ARENA_FILL = (22, 26, 36)
ARENA_LINE = (74, 93, 121)
PLAYER = (245, 180, 82)
PLAYER_HIT = (255, 245, 220)
ENEMY = (208, 72, 78)
ENEMY_HIT = (255, 170, 160)
ARROW = (246, 218, 128)
SHARD = (103, 210, 255)
TEXT = (229, 235, 244)
MUTED = (142, 154, 174)
PANEL = (22, 25, 34)
BUTTON = (63, 93, 142)
BUTTON_HOVER = (82, 121, 184)
LOCKED = (59, 65, 78)


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
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small_font = pygame.font.SysFont("consolas", 16)
        self.big_font = pygame.font.SysFont("consolas", 48, bold=True)
        self.state = load_game()
        self.open_upgrades_button = Button(
            pygame.Rect(config.WINDOW_WIDTH // 2 - 130, 462, 260, 48),
            "Open Skill Tree",
        )
        self.restart_button = Button(
            pygame.Rect(config.WINDOW_WIDTH // 2 - 100, 560, 200, 48),
            "Start Loop",
        )
        self.buy_button = Button(
            pygame.Rect(config.WINDOW_WIDTH // 2 - 105, 390, 210, 48),
            "Buy Upgrade",
        )

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(config.FPS) / 1000.0
            input_state = self._read_input()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game(self.state)
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
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
        return InputState(move=move, aim_world=mouse_world, shoot=shoot)

    def _handle_event(self, event: pygame.event.Event) -> None:
        if self.state.mode is GameMode.DEAD_SUMMARY:
            if self.open_upgrades_button.was_clicked(event):
                self.state.mode = GameMode.UPGRADE
        elif self.state.mode is GameMode.UPGRADE:
            if self.buy_button.was_clicked(event):
                apply_upgrade(self.state, "sharper_arrows_1")
                save_game(self.state)
            elif self.restart_button.was_clicked(event):
                begin_next_loop(self.state)
                save_game(self.state)

    def _world_to_screen(self, position: Vec2) -> tuple[int, int]:
        screen = SCREEN_CENTER + position
        return int(screen.x), int(screen.y)

    def _screen_to_world(self, position: Vec2) -> Vec2:
        return position - SCREEN_CENTER

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
        pygame.draw.circle(self.screen, ARENA_FILL, center, int(config.ARENA_RADIUS))
        pygame.draw.circle(self.screen, ARENA_LINE, center, int(config.ARENA_RADIUS), 3)
        pygame.draw.circle(self.screen, (36, 45, 61), center, 120, 1)
        pygame.draw.circle(self.screen, (36, 45, 61), center, 220, 1)

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
            color = ENEMY_HIT if enemy.hit_flash_timer > 0 else ENEMY
            pygame.draw.circle(
                self.screen,
                color,
                self._world_to_screen(enemy.position),
                int(enemy.radius),
            )

        color = PLAYER_HIT if self.state.player.hit_flash_timer > 0 else PLAYER
        player_pos = self._world_to_screen(self.state.player.position)
        pygame.draw.circle(self.screen, color, player_pos, int(self.state.player.radius))
        aim = self.state.player.aim_direction
        bow_tip = self.state.player.position + aim * 30
        pygame.draw.line(self.screen, ARROW, player_pos, self._world_to_screen(bow_tip), 4)
        self._draw_loop_glyph(center)

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
        hp_width = max(0, int(220 * self.state.player.hp / self.state.player_stats.max_hp))
        pygame.draw.rect(self.screen, (42, 46, 58), pygame.Rect(28, 26, 220, 18))
        pygame.draw.rect(self.screen, (214, 72, 88), pygame.Rect(28, 26, hp_width, 18))
        self._text(f"Loop {self.state.current_loop:02d}", 28, 56, self.font)
        self._text(f"{_format_time(self.state.run_timer)}", 590, 28, self.font)
        self._text(f"Run shards {self.state.run_shards}", 28, 86, self.small_font, SHARD)
        self._text(f"Total shards {self.state.total_shards}", 28, 108, self.small_font, TEXT)
        self._text(f"Damage {self.state.player_stats.damage}", 28, 130, self.small_font, ARROW)
        self._text(f"Best {_format_time(self.state.best_time)}", 1090, 28, self.small_font, MUTED)

    def _draw_death_summary(self) -> None:
        self._draw_overlay_panel(380, 170, 520, 380)
        summary = self.state.last_run_summary
        self._center_text("LOOP FAILED", 230, self.big_font)
        self._center_text(
            f"Time survived: {_format_time(summary.time_survived)}", 312, self.font
        )
        self._center_text(f"Enemies defeated: {summary.enemies_defeated}", 344, self.font)
        self._center_text(f"Shards gained: {summary.shards_gained}", 376, self.font, SHARD)
        self.open_upgrades_button.draw(self.screen, self.font)

    def _draw_upgrade_screen(self) -> None:
        self._draw_overlay_panel(330, 120, 620, 520)
        self._center_text("SKILL TREE", 174, self.big_font)
        self._center_text(f"Available shards: {self.state.total_shards}", 236, self.font, SHARD)

        upgrade = UPGRADE_DEFINITIONS["sharper_arrows_1"]
        owned = upgrade.id in self.state.owned_upgrades
        card = pygame.Rect(config.WINDOW_WIDTH // 2 - 170, 286, 340, 86)
        pygame.draw.rect(self.screen, (31, 36, 48), card, border_radius=6)
        pygame.draw.rect(self.screen, (101, 128, 172), card, 2, border_radius=6)
        self._center_text(upgrade.name, 308, self.font)
        self._center_text("+20% arrow damage", 338, self.small_font, ARROW)
        status = "Owned" if owned else f"Cost: {upgrade.cost} shards"
        self._center_text(status, 360, self.small_font, MUTED)

        if owned or self.state.total_shards < upgrade.cost:
            pygame.draw.rect(self.screen, LOCKED, self.buy_button.rect, border_radius=6)
            label = "Owned" if owned else "Need Shards"
            text = self.font.render(label, True, MUTED)
            self.screen.blit(text, text.get_rect(center=self.buy_button.rect.center))
        else:
            self.buy_button.draw(self.screen, self.font)

        self.restart_button.draw(self.screen, self.font)

    def _draw_overlay_panel(self, x: int, y: int, w: int, h: int) -> None:
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
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

    def _center_text(
        self,
        label: str,
        y: int,
        font: pygame.font.Font,
        color: tuple[int, int, int] = TEXT,
    ) -> None:
        text = font.render(label, True, color)
        self.screen.blit(text, text.get_rect(center=(config.WINDOW_WIDTH // 2, y)))


def _format_time(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def main() -> None:
    GameApp().run()


if __name__ == "__main__":
    main()
