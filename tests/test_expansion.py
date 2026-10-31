"""Encounter fairness, multi-kill scoring and reversible loadout coverage."""
import os
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
import wave

import pygame
from pygame import Vector2 as Vec
from loop_archer.boss import Tempest, Warden
from loop_archer.enemy_ai import update_enemy
from loop_archer.model import Arrow, Enemy, Run
from loop_archer.progression import Progress, load_progress, save_progress


class ExpansionModelTests(unittest.TestCase):
    def test_loadout_clamps_to_owned_and_does_not_mutate_purchases(self):
        progress = Progress(points=80, levels={"damage": 5, "shield": 2})
        progress.equip("damage", 99)
        progress.equip("shield", -1)
        run = Run(progress)
        self.assertEqual(run.level("damage"), 5)
        self.assertEqual(run.shields, 0)
        self.assertEqual(progress.level("shield"), 2)
        progress.equip("damage", 1)
        self.assertEqual(run.level("damage"), 5, "An active run keeps its starting loadout")
        self.assertEqual(Run(progress).level("damage"), 1)

    def test_loadout_roundtrip_and_old_profile_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            progress = Progress(points=99, levels={"damage": 5})
            progress.equip("damage", 2)
            save_progress(path, progress)
            loaded, notice = load_progress(path)
            self.assertFalse(notice)
            self.assertEqual(loaded.level("damage"), 5)
            self.assertEqual(loaded.equipped_levels()["damage"], 2)
            self.assertEqual(loaded.points, 99)
            path.write_text('{"version":1,"levels":{"damage":5}}')
            self.assertEqual(load_progress(path)[0].equipped_levels()["damage"], 5)
            path.write_text('{"version":1,"levels":{"damage":2},"active_levels":{"damage":3}}')
            self.assertTrue(load_progress(path)[1])

    def test_disabling_sale_removes_discount_without_losing_the_purchase(self):
        progress = Progress(levels={"sale": 2})
        self.assertEqual(progress.cost("damage"), 1)
        progress.equip("sale", 0)
        self.assertEqual(progress.cost("damage"), 2)
        self.assertEqual(progress.level("sale"), 2)

    def test_multi_kill_awards_actual_kills_across_frames_without_double_count(self):
        run = Run(Progress(), random.Random(4))
        run.wave_delay = 100
        run.enemies = [Enemy(i, Vec(300 + i * 80, 100), hp=1, speed=0, radius=20) for i in range(1, 4)]
        run.arrows = [Arrow(Vec(100, 100), Vec(6000, 0), 10)]
        run.update(.1)
        self.assertEqual(run.kills, 3)
        self.assertEqual(run.multikill_bonus, 5)  # second +2, third +3
        self.assertEqual(run.points, 8)
        self.assertEqual(run.best_multikill, 3)
        run.update(.1)
        self.assertEqual(run.multikill_bonus, 5)
        run.elapsed += .5
        run._reward_multikill()
        self.assertEqual(run.multikill_count, 1)
        self.assertEqual(run.multikill_bonus, 5)

    def test_warden_midpoint_and_tempest_finale_follow_playtested_difficulty(self):
        run = Run(Progress())
        run.wave = 3
        run.start_wave()
        self.assertEqual(run.spawn_queue, ["boss"])
        run.spawn("boss")
        self.assertFalse(run.boss_defeated)
        run.wave = 7
        run.start_wave()
        self.assertEqual(run.spawn_queue, ["tempest"])

    def test_tempest_locks_blink_then_opens_eye_with_bounded_damage(self):
        boss, pos, player = Tempest(), Vec(840, 400), Vec(1000, 1000)
        for _ in range(33):
            boss.update(.1, pos, player, (1680, 1680), 140)
        self.assertEqual(boss.phase, "blink")
        destination = Vec(boss.target)
        for _ in range(11):
            boss.update(.1, pos, Vec(200, 200), (1680, 1680), 140)
        self.assertEqual(pos, destination)
        self.assertTrue(boss.exposed)
        self.assertEqual(boss.core_damage(100), 8)
        self.assertFalse(boss.exposed)
        self.assertEqual(boss.core_damage(100), 0)

    def test_warden_enrage_adds_pressure_and_shorter_opening(self):
        calm, angry = Warden(), Warden(enraged=True)
        a, b = Vec(840, 400), Vec(840, 400)
        self.assertEqual(len(calm.update(1.11, a, Vec(840, 1100), (1680, 1680), 140)), 5)
        self.assertEqual(len(angry.update(.86, b, Vec(840, 1100), (1680, 1680), 140)), 9)
        self.assertLess(Warden.DURATIONS["exposed"], 2.6)
        self.assertGreater(Warden.MAX_HEALTH / Warden.CORE_BUDGET, 3)

    def test_hunter_commits_lunge_and_recovers(self):
        enemy = Enemy(1, Vec(400, 400), attack_clock=0)
        update_enemy(enemy, Vec(600, 400), .01)
        self.assertEqual(enemy.phase, "windup")
        locked = Vec(enemy.heading)
        update_enemy(enemy, Vec(400, 800), .66)
        self.assertEqual(enemy.phase, "lunge")
        self.assertEqual(enemy.heading, locked)
        start = Vec(enemy.pos)
        update_enemy(enemy, Vec(400, 800), .3)
        self.assertGreater(enemy.pos.x, start.x)
        self.assertEqual(enemy.phase, "recover")

    def test_caster_strafes_locks_aim_and_fires_three_shots(self):
        enemy = Enemy(1, Vec(400, 400), kind="shooter", attack_clock=0)
        update_enemy(enemy, Vec(1000, 400), .01)
        self.assertNotEqual(enemy.pos.y, 400)
        self.assertEqual(enemy.phase, "windup")
        locked = Vec(enemy.heading)
        shots = update_enemy(enemy, Vec(400, 1000), .71)
        self.assertEqual(len(shots), 3)
        self.assertEqual(shots[1].normalize(), locked)

    def test_boss_music_asset_is_valid_original_pcm_loop(self):
        with wave.open(str(Path(__file__).resolve().parents[1] / "assets/boss_assault.wav")) as track:
            self.assertEqual(track.getframerate(), 22050)
            self.assertEqual(track.getsampwidth(), 2)
            self.assertAlmostEqual(track.getnframes() / track.getframerate(), 25.6)


class ExpansionAppTests(unittest.TestCase):
    def test_player_arrival_freezes_clock_and_inputs_then_skips_cleanly(self):
        self.app.start()
        run = self.app.run
        clock, position = run.time_left, Vec(run.player)
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(700, 400)))
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.app.update(.5)
        self.assertEqual(run.time_left, clock)
        self.assertEqual(run.player, position)
        self.assertFalse(run.charging or run.enemies or self.app.recall_keys)
        self.app.render()
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.app.update(.1)
        self.assertFalse(self.app.entrance_active)
        self.assertLess(run.time_left, clock)

    def test_player_arrival_completes_naturally_and_freezes_while_paused(self):
        self.app.start()
        self.app.update(.2)
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        remaining = self.app.entry_remaining
        self.app.update(.5)
        self.assertEqual(self.app.entry_remaining, remaining)
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.app.update(remaining)
        self.assertFalse(self.app.entrance_active)
        self.assertEqual(self.app.run.elapsed, 0)
        self.app.update(.05)
        self.assertGreater(self.app.run.elapsed, 0)

    def test_entrance_click_cannot_activate_stale_menu_buttons(self):
        self.app.render()
        self.app.start(practice=True)
        run = self.app.run
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 450)))
        self.assertIs(self.app.run, run)
        self.assertTrue(self.app.practice)
        self.assertTrue(self.app.entrance_active)

    def test_campaign_boss_entrance_stops_combat_before_contact_or_projectiles(self):
        self.app.start()
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        run = self.app.run
        run.wave, run.wave_delay = 7, 0
        run.invulnerable = 0
        run.player = Vec(840, 504)
        self.app.update(.05)
        self.assertFalse(run.over)
        self.assertEqual(self.app.scene, "play")
        self.assertGreater(self.app.intro_remaining, 0)
        self.assertFalse(run.bullets)
        boss = run.enemies[0]
        self.assertGreater(boss.pos.distance_to(run.player), boss.radius + 60)
        self.assertEqual(boss.warden.timer, 3.2, "AI must not run before the entrance")

    def setUp(self):
        self.env = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        self.env.start()
        self.directory = tempfile.TemporaryDirectory()
        from loop_archer.app import App
        self.path = Path(self.directory.name) / "progress.json"
        self.app = App(self.path, headless=True)

    def tearDown(self):
        pygame.quit()
        self.directory.cleanup()
        self.env.stop()

    def test_intro_freezes_combat_and_clock_and_blocks_shooting(self):
        self.app.start(practice=True)
        initial_time = self.app.run.time_left
        boss_pos = Vec(self.app.run.enemies[0].pos)
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(700, 400)))
        self.app.update(.5)
        self.assertEqual(self.app.run.time_left, initial_time)
        self.assertEqual(self.app.run.enemies[0].pos, boss_pos)
        self.assertFalse(self.app.run.charging)
        self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.app.update(.1)
        self.assertLess(self.app.run.time_left, initial_time)
        self.assertEqual(self.app.intro_remaining, 0, "The intro plays only once per boss")

    def test_loadout_actions_keep_purchases_and_survive_reopen(self):
        self.app.progress.levels = {"damage": 5, "shield": 2}
        self.app.action("loadout")
        self.app.action("loadout_off")
        self.app.action("rank+:damage")
        self.assertEqual(self.app.progress.level("damage"), 5)
        loaded, notice = load_progress(self.path)
        self.assertFalse(notice)
        self.assertEqual(loaded.equipped_levels()["damage"], 1)
        self.assertEqual(loaded.equipped_levels()["shield"], 0)
        self.app.action("loadout_all")
        self.assertEqual(self.app.progress.equipped_levels()["shield"], 2)

    def test_second_boss_practice_and_loadout_render_without_writing(self):
        self.path.write_text('{"version":1,"points":17}')
        before = self.path.read_bytes()
        self.app.action("practice_boss")
        self.app.action("practice")
        self.assertEqual(self.app.run.enemies[0].kind, "tempest")
        self.app.update(.1)
        self.app.render()
        self.app.run.points = 100
        self.app.action("menu")
        self.app.action("loadout")
        self.app.render()
        self.app.action("quit")
        self.assertEqual(self.path.read_bytes(), before)

    def test_music_starts_pauses_resumes_and_stops_outside_battle(self):
        self.app.audio.enabled = True
        self.app.start(practice=True)
        with patch.object(self.app.audio, "music_channel") as channel:
            self.app.update(.1)
            self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            self.app.update(.1)
            self.app.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            self.app.update(.1)
            self.assertEqual(channel.play.call_count, 1)
            self.assertTrue(channel.pause.called)
            self.assertTrue(channel.unpause.called)
            self.app.action("menu")
            self.app.update(.1)
            self.assertTrue(channel.stop.called)


if __name__ == "__main__":
    unittest.main()
