"""Headless lifecycle tests: event handling, pause, banking and save protection."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame


class AppLifecycleTests(unittest.TestCase):
    def test_boss_practice_does_not_bank_after_returning_to_menu(self):
        saved = '{"version":1,"points":77}'
        self.save_path.write_text(saved)
        original = self.app.progress.points
        loops = self.app.progress.loops
        self.app.start(practice=True)
        self.assertEqual(self.app.run.wave, 8)
        self.app.run.points = 100
        self.app.action("menu")
        self.app.action("quit")
        self.assertEqual(self.app.progress.points, original)
        self.assertEqual(self.app.progress.loops, loops)
        self.assertEqual(self.save_path.read_text(), saved)

    def test_headless_cli_never_banks_into_the_player_profile(self):
        from loop_archer.app import App, main
        original = '{"version":1,"points":77}'
        self.save_path.write_text(original)
        def fake_loop(app, frames=0, screenshot=None):
            app.start()
            app.run.points = 99
            app.bank()
        with patch("sys.argv", ["main.py", "--headless", "--save", str(self.save_path)]), patch.object(App, "loop", fake_loop):
            main()
        self.assertEqual(self.save_path.read_text(), original)

    def test_hold_purchase_buys_one_rank_and_scene_change_cancels_hold(self):
        self.app.scene = "tree"
        self.app.progress.points = 100
        self.app.mouse = self.app.shop.point("damage")
        self.app.shop.begin(self.app.mouse, self.app.progress)
        self.app.update(.6)
        self.assertEqual(self.app.progress.level("damage"), 1)
        self.app.update(1)
        self.assertEqual(self.app.progress.level("damage"), 1)
        self.app.start()
        self.assertIsNone(self.app.shop.holding)

    def setUp(self):
        self.environment = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy",
                                                 "SDL_AUDIODRIVER": "dummy"})
        self.environment.start()
        self.directory = tempfile.TemporaryDirectory()
        self.save_path = Path(self.directory.name) / "progress.json"
        from loop_archer.app import App
        self.app = App(self.save_path, headless=True, seed=123)

    def tearDown(self):
        pygame.quit()
        self.directory.cleanup()
        self.environment.stop()

    def test_pause_freezes_timer_and_cancels_incomplete_draw(self):
        self.app.start()
        self.app.run.begin_charge()
        self.app.run.charge = 0.2
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(self.app.scene, "pause")
        self.assertFalse(self.app.run.charging)
        self.assertEqual(self.app.run.charge, 0)
        time_before = self.app.run.time_left
        self.app.update(0.2)
        self.assertEqual(self.app.run.time_left, time_before)
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.app.update(0.1)
        self.assertLess(self.app.run.time_left, time_before)

    def test_losing_focus_pauses_and_release_does_not_fire(self):
        self.app.start()
        self.app.run.begin_charge()
        self.app.handle(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(100, 100)))
        self.assertEqual(self.app.scene, "pause")
        self.assertFalse(self.app.run.charging)
        self.assertFalse(self.app.run.arrows)

    def test_recall_stops_only_after_both_keyboard_and_mouse_are_released(self):
        from pygame import Vector2 as Vec
        from loop_archer.model import Arrow
        self.app.start()
        arrow = Arrow(self.app.run.player + Vec(600, 0), Vec(), 1, state="stuck")
        self.app.run.arrows = [arrow]
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(500, 350)))
        self.assertEqual(arrow.state, "returning")
        self.app.handle(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
        self.assertEqual(arrow.state, "returning")
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=3, pos=(500, 350)))
        self.assertEqual(arrow.state, "stuck")
        self.assertFalse(self.app.recall_keys)

    def test_losing_focus_cancels_held_recall(self):
        from pygame import Vector2 as Vec
        from loop_archer.model import Arrow
        self.app.start()
        arrow = Arrow(self.app.run.player + Vec(600, 0), Vec(), 1, state="stuck")
        self.app.run.arrows = [arrow]
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.app.handle(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(self.app.scene, "pause")
        self.assertEqual(arrow.state, "stuck")
        self.assertFalse(self.app.recall_keys)

    def test_finishing_then_closing_banks_only_once_and_saves(self):
        self.app.start()
        self.app.run.points = 7
        self.app.run.finish("Test end")
        self.app.update(0.1)
        self.assertEqual(self.app.scene, "result")
        self.assertEqual(self.app.progress.points, 7)
        self.assertEqual(self.app.progress.loops, 1)
        self.app.handle(pygame.event.Event(pygame.QUIT))
        self.assertFalse(self.app.running)
        self.assertEqual(self.app.progress.points, 7)
        self.assertEqual(self.app.progress.loops, 1)
        from loop_archer.progression import load_progress
        loaded, warning = load_progress(self.save_path)
        self.assertFalse(warning)
        self.assertEqual(loaded.points, 7)
        self.assertEqual(loaded.loops, 1)

    def test_closing_live_run_banks_points(self):
        self.app.start()
        self.app.run.points = 5
        self.app.handle(pygame.event.Event(pygame.QUIT))
        self.assertEqual(self.app.progress.points, 5)
        self.assertEqual(self.app.progress.loops, 1)
        self.assertTrue(self.save_path.exists())

    def test_mouse_mapping_accounts_for_letterboxing(self):
        self.app.window = pygame.display.set_mode((1000, 1000))
        logical_center = self.app.mouse_position((500, 500))
        self.assertEqual(logical_center, (640, 400))
        self.assertLess(self.app.mouse_position((0, 0))[1], 0)

    def test_corrupt_save_is_not_overwritten_by_banking(self):
        content = "broken save data"
        self.save_path.write_text(content, encoding="utf-8")
        from loop_archer.app import App
        self.app = App(self.save_path, headless=True, seed=123)
        self.assertFalse(self.app.save_allowed)
        self.app.start()
        self.app.run.points = 10
        self.app.action("quit")
        self.assertEqual(self.save_path.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
