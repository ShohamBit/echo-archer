"""Behavior tests for combat rules, independent of display/audio initialization."""
import random
import unittest

from pygame import Vector2 as Vec

from loop_archer.model import Arrow, Enemy, Run, WIDTH, HEIGHT, bank_run, segment_hits
from loop_archer.progression import Progress


def quiet_run(levels=None):
    run = Run(Progress(levels=levels or {}), random.Random(123), original=False)
    run.wave_delay = 1000
    run.time_left = 1000
    run.invulnerable = 0
    return run


class CollisionTests(unittest.TestCase):
    def test_sweep_detects_crossed_target_and_rejects_target_beyond_endpoint(self):
        self.assertTrue(segment_hits(Vec(0, 0), Vec(1000, 0), Vec(500, 1), 2))
        self.assertFalse(segment_hits(Vec(0, 0), Vec(1000, 0), Vec(1050, 0), 2))
        self.assertFalse(segment_hits(Vec(0, 0), Vec(1000, 0), Vec(500, 10), 2))

    def test_stationary_segment_is_supported(self):
        self.assertTrue(segment_hits(Vec(2, 2), Vec(2, 2), Vec(3, 2), 1))
        self.assertFalse(segment_hits(Vec(2, 2), Vec(2, 2), Vec(4, 2), 1))

    def test_fast_charged_arrow_pierces_multiple_enemies(self):
        run = quiet_run()
        run.enemies = [Enemy(1, Vec(250, 100), hp=2, speed=0),
                       Enemy(2, Vec(350, 100), hp=2, speed=0)]
        run.arrows = [Arrow(Vec(100, 100), Vec(12000, 0), damage=3, full=True)]
        run.update(0.03)
        self.assertEqual(run.kills, 2)
        self.assertFalse(run.enemies)
        self.assertGreater(run.points, 0)

    def test_partial_charge_arrow_also_pierces_multiple_enemies(self):
        run = quiet_run()
        run.enemies = [Enemy(1, Vec(250, 100), hp=2, speed=0),
                       Enemy(2, Vec(350, 100), hp=2, speed=0)]
        run.arrows = [Arrow(Vec(100, 100), Vec(12000, 0), damage=3, full=False)]
        run.update(0.03)
        self.assertEqual(run.kills, 2)
        self.assertFalse(run.enemies)
        self.assertEqual(run.arrows[0].state, "flying")

    def test_partial_charge_pierces_both_targets_when_spawn_order_is_reversed(self):
        run = quiet_run()
        farther = Enemy(1, Vec(350, 100), hp=2, speed=0)
        nearer = Enemy(2, Vec(250, 100), hp=2, speed=0)
        run.enemies = [farther, nearer]
        run.arrows = [Arrow(Vec(100, 100), Vec(60000, 0), damage=3, full=False)]
        run.update(1 / 120)
        self.assertFalse(run.enemies)
        self.assertEqual(run.kills, 2)

    def test_piercing_arrow_does_not_repeat_damage_while_inside_enemy(self):
        run = quiet_run()
        enemy = Enemy(1, Vec(200, 100), hp=20, speed=0, radius=30)
        run.enemies = [enemy]
        run.arrows = [Arrow(Vec(180, 100), Vec(800, 0), damage=3, full=True)]
        run.update(0.05)
        self.assertEqual(enemy.hp, 17)


class RunTests(unittest.TestCase):
    def test_full_charge_multishot_and_bonus_damage(self):
        run = quiet_run({"multishot": 2, "damage": 2, "full_charge": 1})
        run.begin_charge()
        for _ in range(20):
            run.update(run.charge_duration / 10)
        run.release()
        self.assertEqual(len(run.arrows), 3)
        self.assertTrue(all(arrow.full for arrow in run.arrows))
        self.assertTrue(all(arrow.damage == 4 for arrow in run.arrows))
        self.assertFalse(run.charging)
        self.assertEqual(run.charge, 0)
        run.release()
        self.assertEqual(len(run.arrows), 3)

    def test_recall_can_hit_enemies_already_hit_on_outward_leg(self):
        run = quiet_run({"recall": 2, "recall_reward": 1})
        run.player = Vec(200, 800)
        run.enemies = [Enemy(1, Vec(600, 800), hp=2, speed=0),
                       Enemy(2, Vec(750, 800), hp=2, speed=0)]
        arrow = Arrow(Vec(1000, 800), Vec(0, 0), 1, state="stuck", hit={1, 2})
        run.arrows = [arrow]
        run.recall()
        self.assertEqual(arrow.state, "returning")
        for _ in range(4):
            run.update(0.25)
        self.assertEqual(run.kills, 2)
        self.assertEqual(arrow.return_hit, {1, 2})
        self.assertGreaterEqual(run.points, 4)

    def test_returning_arrow_is_safe_without_immunity_upgrade(self):
        run = quiet_run()
        run.player = Vec(200, 300)
        run.arrows = [Arrow(Vec(600, 300), Vec(0, 0), 1, state="stuck")]
        run.recall()
        for _ in range(4):
            run.update(0.25)
        self.assertFalse(run.over)
        self.assertFalse(run.arrows)
        self.assertTrue(run.can_shoot)

    def test_returning_arrow_homes_toward_the_live_player(self):
        run = quiet_run()
        run.player = Vec(200, 300)
        arrow = Arrow(Vec(600, 300), Vec(0, 0), 1, state="stuck")
        run.arrows = [arrow]
        run.recall()
        run.update(0.25, movement=(0, -1))
        self.assertFalse(run.over)
        self.assertLess(arrow.velocity.x, 0)
        self.assertLess(arrow.velocity.y, 0)
        self.assertLess(arrow.pos.y, 300)

    def test_friendly_fire_upgrade_protects_against_flying_arrows(self):
        run = quiet_run({"safe": 1})
        run.player = Vec(200, 300)
        run.arrows = [Arrow(Vec(600, 300), Vec(-2000, 0), 1)]
        run.update(0.25)
        self.assertFalse(run.over)

    def test_flying_arrow_can_hurt_player_without_immunity(self):
        run = quiet_run()
        run.player = Vec(200, 300)
        run.arrows = [Arrow(Vec(600, 300), Vec(-2000, 0), 1)]
        run.update(0.25)
        self.assertTrue(run.over)
        self.assertIn("flying arrow", run.reason)

    def test_releasing_recall_stops_homing_until_pressed_again(self):
        run = quiet_run()
        run.player = Vec(200, 800)
        arrow = Arrow(Vec(1200, 800), Vec(), 1, state="stuck")
        run.arrows = [arrow]
        run.recall()
        run.update(0.25)
        stopped_at = Vec(arrow.pos)
        run.stop_recall()
        run.update(0.25, movement=(0, 1))
        self.assertEqual(arrow.state, "stuck")
        self.assertEqual(arrow.pos, stopped_at)
        run.recall()
        run.update(0.25)
        self.assertNotEqual(arrow.pos, stopped_at)

    def test_charge_tiers_and_duration_use_recovered_blueprint_values(self):
        run = quiet_run()
        self.assertEqual(run.charge_duration, 1.25)
        self.assertEqual(run.charge_level, 1)
        run.charge = run.charge_duration * .25
        self.assertEqual(run.charge_level, 2)
        run.charge = run.charge_duration * .5
        self.assertEqual(run.charge_level, 3)
        run.charge = run.charge_duration * .75
        self.assertEqual(run.charge_level, 4)
        upgraded = quiet_run({"charge": 3})
        self.assertAlmostEqual(upgraded.charge_duration, .8)

    def test_charging_and_recalling_reduce_movement_speed(self):
        normal, charging, recalling = quiet_run(), quiet_run(), quiet_run()
        origin = Vec(normal.player)
        charging.begin_charge()
        charging.charge = charging.charge_duration
        recalling.arrows = [Arrow(recalling.player + Vec(600, 0), Vec(), 1, state="stuck")]
        recalling.recall()
        for run in (normal, charging, recalling):
            run.update(.1, movement=(0, 1))
        self.assertAlmostEqual(normal.player.y - origin.y, 50)
        self.assertAlmostEqual(charging.player.y - origin.y, 25)
        self.assertAlmostEqual(recalling.player.y - origin.y, 10)

    def test_arrow_slows_in_steps_then_becomes_recallable(self):
        run = quiet_run()
        arrow = Arrow(Vec(400, 300), Vec(1000, 0), 1)
        run.arrows = [arrow]
        run.update(.1)
        self.assertEqual(arrow.velocity.length(), 1000)
        run.update(.1)
        self.assertEqual(arrow.velocity.length(), 750)
        run.update(.2)
        self.assertEqual(arrow.state, "stuck")
        run.recall()
        self.assertEqual(arrow.state, "returning")

    def test_timer_expires_once_and_stops_simulation(self):
        run = quiet_run()
        run.time_left = 0.01
        run.update(0.02)
        self.assertTrue(run.over)
        self.assertFalse(run.victory)
        self.assertEqual(run.time_left, 0)
        self.assertEqual(run.events.count("death"), 1)
        position = Vec(run.player)
        run.update(0.2, movement=(1, 0))
        self.assertEqual(run.player, position)
        self.assertEqual(run.events.count("death"), 1)

    def test_shield_absorbs_one_hit_and_provides_grace_period(self):
        run = quiet_run({"shield": 1})
        run.hurt("test hit")
        self.assertFalse(run.over)
        self.assertEqual(run.shields, 0)
        run.hurt("same frame hit")
        self.assertFalse(run.over)
        run.invulnerable = 0
        run.hurt("second hit")
        self.assertTrue(run.over)

    def test_diagonal_movement_is_normalized_and_player_stays_in_bounds(self):
        straight, diagonal = quiet_run(), quiet_run()
        origin = Vec(straight.player)
        straight.update(0.1, movement=(1, 0))
        diagonal.update(0.1, movement=(1, 1))
        self.assertAlmostEqual(straight.player.distance_to(origin),
                               diagonal.player.distance_to(origin), places=5)
        diagonal.player = Vec(WIDTH - 1, HEIGHT - 1)
        diagonal.update(0.1, movement=(1, 1))
        self.assertLess(diagonal.player.x, WIDTH)
        self.assertLess(diagonal.player.y, HEIGHT)

    def test_clear_wave_advances_but_final_clear_wins_campaign(self):
        run = quiet_run()
        run.wave_delay = 0
        run.update(0.01)
        self.assertEqual(run.wave, 1)
        self.assertTrue(run.enemies or run.spawn_queue)
        final = quiet_run()
        final.wave = 8
        final.boss_defeated = True
        final.wave_delay = 0
        final.update(0.01)
        self.assertTrue(final.over)
        self.assertTrue(final.victory)

    def test_endless_mode_continues_past_campaign_final_wave(self):
        run = Run(Progress(), random.Random(123), endless=True, original=False)
        run.wave = 8
        run.wave_delay = 0
        run.update(0.01)
        self.assertFalse(run.over)
        self.assertEqual(run.wave, 9)

    def test_bank_run_preserves_currency_and_personal_bests(self):
        progress = Progress(points=7, loops=2, best_wave=5, best_kills=10)
        run = quiet_run()
        run.points, run.wave, run.kills = 13, 3, 12
        run.finish("test end")
        bank_run(progress, run)
        self.assertEqual((progress.points, progress.loops), (20, 3))
        self.assertEqual((progress.best_wave, progress.best_kills), (5, 12))


if __name__ == "__main__":
    unittest.main()
