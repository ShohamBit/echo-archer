"""Regression cases from the player's premature-win and lag reports."""
import random
import unittest
import pygame
from pygame import Vector2
from loop_archer.model import Arrow, Enemy, Run
from loop_archer.presentation import Presentation
from loop_archer.progression import BY_KEY, Progress


class VictoryRegressionTests(unittest.TestCase):
    def test_default_mode_is_campaign(self):
        self.assertFalse(Run(Progress()).original)

    def test_fifteen_spawns_are_not_victory_while_enemies_are_alive(self):
        progress = Progress(levels={key: upgrade.max_level for key, upgrade in BY_KEY.items()})
        run = Run(progress, random.Random(5), original=True)
        run.original_spawn_count = 15
        run.enemies = [Enemy(1, Vector2(150, 150), hp=100)]
        run.update(.01)
        self.assertFalse(run.over, "A spawn counter is not a completed encounter")
        self.assertFalse(run.victory)

    def test_empty_final_wave_cannot_skip_the_boss(self):
        run = Run(Progress(), random.Random(6))
        run.wave = 8
        run.wave_delay = 0
        run.update(.01)
        self.assertFalse(run.over)
        self.assertTrue(any(enemy.kind == "tempest" for enemy in run.enemies))

    def test_boss_must_be_killed_before_final_clear_wins(self):
        run = Run(Progress(), random.Random(6))
        run.wave = 8
        run.wave_delay = 0
        run.invulnerable = 100
        boss = Enemy(1, Vector2(300, 100), "tempest", hp=1, speed=0, radius=40)
        run.enemies = [boss]
        run.update(.01)
        self.assertFalse(run.over)
        run.arrows = [Arrow(Vector2(200, 100), Vector2(5000, 0), damage=3)]
        boss.warden.phase = "exposed"
        boss.warden.timer = 2
        boss.warden.heading = Vector2(1, 0)
        boss.warden.target = Vector2(600, 100)
        run.update(.05)
        self.assertTrue(run.boss_defeated)
        self.assertTrue(run.over)
        self.assertTrue(run.victory)


class PresentationRegressionTests(unittest.TestCase):
    def test_presentation_keeps_native_resolution_and_exact_pixels(self):
        surface = pygame.Surface((31, 21))
        surface.fill((10, 20, 30))
        surface.set_at((7, 9), (234, 120, 5))
        before = pygame.image.tostring(surface, "RGB")
        self.assertIs(Presentation().apply(surface), surface)
        self.assertEqual(pygame.image.tostring(surface, "RGB"), before)


if __name__ == "__main__":
    unittest.main()
