"""Campaign progression, readable crowds and isolated boss-practice endings."""
import random
import unittest
from pygame import Vector2 as Vec
from loop_archer.campaign import CAMPAIGN, boss_wave
from loop_archer.enemy_ai import separate_enemies
from loop_archer.model import Arrow, Bullet, Enemy, Run
from loop_archer.progression import Progress


def quiet():
    run = Run(Progress(), random.Random(7))
    run.wave_delay = 1000
    run.time_left = 1000
    run.invulnerable = 1000
    return run


def kill_last_enemy(run):
    run.enemies = [Enemy(1, Vec(400, 100), hp=1, radius=20, speed=0)]
    run.arrows = [Arrow(Vec(300, 100), Vec(5000, 0), 10)]
    run.update(.03)


class CampaignTests(unittest.TestCase):
    def test_enemy_roles_are_introduced_before_mixed_pressure_and_bosses(self):
        self.assertEqual(len(CAMPAIGN), 8)
        self.assertEqual(set(CAMPAIGN[0].enemies), {"chaser"})
        self.assertIn("tank", CAMPAIGN[1].enemies)
        self.assertNotIn("shooter", CAMPAIGN[1].enemies)
        self.assertIn("shooter", CAMPAIGN[2].enemies)
        self.assertEqual(boss_wave("boss"), 4)
        self.assertEqual(boss_wave("tempest"), 8)
        self.assertLess(len(CAMPAIGN[4].enemies), len(CAMPAIGN[6].enemies))

    def test_more_company_keeps_rank_effect_without_adding_boss_guards(self):
        for wave in range(1, 9):
            with self.subTest(wave=wave):
                base = Run(Progress(), random.Random(9))
                upgraded = Run(Progress(levels={"more_enemies": 5}), random.Random(9))
                base.wave = upgraded.wave = wave - 1
                base.start_wave()
                upgraded.start_wave()
                self.assertEqual(len(upgraded.spawn_queue) - len(base.spawn_queue),
                                 0 if CAMPAIGN[wave - 1].boss else 5)

    def test_first_wave_spawns_small_groups_with_a_gap_between_them(self):
        run = quiet()
        run.start_wave()
        run.update(.01)
        run.update(.25)
        run.update(.15)
        self.assertEqual(len(run.enemies), 2)
        run.update(.25)
        run.update(.25)
        self.assertEqual(len(run.enemies), 2)
        run.update(.25)
        run.update(.25)
        self.assertEqual(len(run.enemies), 3)

    def test_regroup_freezes_clock_but_allows_movement_and_arrow_retrieval(self):
        run = quiet()
        run.wave = 1
        run.bullets = [Bullet(Vec(100, 100), Vec(0, 300))]
        kill_last_enemy(run)
        self.assertGreater(run.intermission, 0)
        self.assertFalse(run.bullets)
        clock, start = run.time_left, Vec(run.player)
        run.levels["passive"] = 3
        run.passive_clock = 2.9
        points = run.points
        run.arrows = [Arrow(run.player + Vec(500, 0), Vec(), 1, state="stuck")]
        run.recall()
        run.update(.2, movement=(1, 0))
        self.assertEqual(run.time_left, clock)
        self.assertEqual(run.points, points, "Regroup must not generate free passive income")
        self.assertGreater(run.player.x, start.x)
        self.assertEqual(run.bow_state, "returning")
        for _ in range(10):
            run.update(.2)
        self.assertEqual(run.wave, 2)
        self.assertEqual(run.intermission, 0)

    def test_pending_reinforcements_prevent_a_false_wave_clear(self):
        run = quiet()
        run.wave = 1
        run.spawn_queue = ["chaser"]
        run.spawn_timer = 10
        kill_last_enemy(run)
        self.assertEqual(run.intermission, 0)
        self.assertFalse(run.over)

    def test_midboss_kill_does_not_complete_the_campaign(self):
        run = quiet()
        run.wave = 4
        run.spawn("boss")
        enemy = run.enemies[0]
        enemy.pos, enemy.hp = Vec(700, 200), 1
        enemy.warden.phase, enemy.warden.timer = "exposed", 2
        enemy.warden.heading, enemy.warden.target = Vec(1, 0), Vec(1000, 200)
        run.arrows = [Arrow(Vec(450, 200), Vec(5000, 0), 4)]
        run.update(.05)
        self.assertFalse(run.boss_defeated)
        self.assertFalse(run.over)
        self.assertGreater(run.intermission, 0)

    def test_tempest_open_eye_allows_arrow_through_blades_before_core_hit(self):
        run = quiet()
        enemy = Enemy(1, Vec(700, 200), kind="tempest", hp=32, radius=140)
        enemy.warden.phase, enemy.warden.timer = "exposed", 2
        run.enemies = [enemy]
        arrow = Arrow(Vec(510, 200), Vec(2000, 0), 2)
        run.arrows = [arrow]
        run.update(.04)
        self.assertEqual(enemy.hp, 32)
        self.assertNotIn(enemy.id, arrow.hit)
        self.assertGreater(arrow.velocity.x, 0)
        run.update(.04)
        self.assertEqual(enemy.hp, 26)
        self.assertIn(enemy.id, arrow.hit)

    def test_tempest_closed_eye_still_deflects_arrows(self):
        run = quiet()
        enemy = Enemy(1, Vec(700, 200), kind="tempest", hp=32, radius=140)
        run.enemies = [enemy]
        arrow = Arrow(Vec(510, 200), Vec(2000, 0), 2)
        run.arrows = [arrow]
        run.update(.04)
        self.assertEqual(enemy.hp, 32)
        self.assertLess(arrow.velocity.x, 0)


class EnemySpacingTests(unittest.TestCase):
    def test_overlapping_hunters_separate_even_at_identical_positions(self):
        enemies = [Enemy(i, Vec(600, 600)) for i in (1, 2)]
        separate_enemies(enemies, .1)
        self.assertGreater(enemies[0].pos.distance_to(enemies[1].pos), 0)

    def test_spacing_checks_neighbors_across_cell_boundaries(self):
        enemies = [Enemy(1, Vec(299, 600)), Enemy(2, Vec(301, 600))]
        separate_enemies(enemies, .1)
        self.assertGreater(enemies[0].pos.distance_to(enemies[1].pos), 2)

    def test_spacing_never_moves_committed_attacks_or_bosses(self):
        for phase in ("windup", "lunge"):
            with self.subTest(phase=phase):
                fixed = Enemy(1, Vec(600, 600), phase=phase)
                hunter = Enemy(2, Vec(610, 600))
                boss = Enemy(3, Vec(600, 600), kind="boss")
                separate_enemies([fixed, hunter, boss], .1)
                self.assertEqual(fixed.pos, Vec(600, 600))
                self.assertEqual(boss.pos, Vec(600, 600))
                self.assertGreater(hunter.pos.x, 610)

    def test_spacing_is_bounded_and_does_not_pull_distant_enemies(self):
        enemies = [Enemy(1, Vec(75, 75)), Enemy(2, Vec(75, 75)), Enemy(3, Vec(1000, 1000))]
        separate_enemies(enemies, .1)
        self.assertEqual(enemies[2].pos, Vec(1000, 1000))
        for enemy in enemies:
            self.assertGreaterEqual(enemy.pos.x, enemy.radius)
            self.assertGreaterEqual(enemy.pos.y, enemy.radius)


if __name__ == "__main__":
    unittest.main()
