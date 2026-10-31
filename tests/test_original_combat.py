"""Regressions for the original-game differences reported by the player.

Unlike implementation-only tests, these describe the single-volley and repeated
wall-bounce behavior the user confirmed in the supplied Unreal game.
"""
import random
import unittest

from pygame import Vector2 as Vec

from loop_archer.model import Arrow, Run, WIDTH, HEIGHT
from loop_archer.progression import Progress


def isolated_run(levels=None):
    run = Run(Progress(levels=levels or {}), random.Random(8), original=False)
    run.wave_delay = 1000
    run.time_left = 1000
    run.invulnerable = 1000
    return run


class OriginalCombatTests(unittest.TestCase):
    def test_only_one_arrow_can_be_out_before_recall(self):
        run = isolated_run()
        run.begin_charge()
        run.release()
        self.assertEqual(len(run.arrows), 1)
        run.begin_charge()
        run.release()
        self.assertEqual(len(run.arrows), 1, "Shooting must wait for the deployed arrow to return")

    def test_multishot_is_one_deployed_volley_not_unlimited_ammunition(self):
        run = isolated_run({"multishot": 2})
        run.begin_charge()
        run.release()
        run.begin_charge()
        run.release()
        self.assertEqual(len(run.arrows), 3)

    def test_arrow_keeps_bouncing_off_top_and_bottom_walls(self):
        run = isolated_run()
        arrow = Arrow(Vec(WIDTH / 3, HEIGHT - 5), Vec(0, 2000), 1)
        run.arrows = [arrow]
        run.update(.05)
        self.assertLess(arrow.velocity.y, 0)
        arrow.pos.y = 5
        run.update(.05)
        self.assertGreater(arrow.velocity.y, 0, "The second wall must reflect the arrow too")
        self.assertEqual(arrow.state, "flying")
        self.assertEqual(arrow.bounces, 2)

    def test_deployed_arrow_does_not_stop_on_an_invented_lifetime(self):
        run = isolated_run()
        arrow = Arrow(Vec(WIDTH / 2, HEIGHT / 3), Vec(12000, 0), 1)
        run.arrows = [arrow]
        for _ in range(12):
            run.update(.2)
        self.assertEqual(arrow.state, "flying")
        self.assertGreater(arrow.velocity.length(), 0)

    def test_screen_side_portal_wraps_arrow_without_reversing_direction(self):
        run = isolated_run()
        arrow = Arrow(Vec(WIDTH - 60, HEIGHT / 3), Vec(1500, 0), 1)
        run.arrows = [arrow]
        run.update(.05)
        self.assertLess(arrow.pos.x, WIDTH / 3)
        self.assertGreater(arrow.velocity.x, 0)

    def test_in_flight_arrow_cannot_be_recalled(self):
        run = isolated_run()
        arrow = Arrow(Vec(500, 100), Vec(1000, 0), 1)
        run.arrows = [arrow]
        run.recall()
        self.assertEqual(arrow.state, "flying")

    def test_recall_homes_safely_to_moving_player_and_refills_bow(self):
        run = isolated_run()
        run.invulnerable = 0
        run.player = Vec(WIDTH / 2, HEIGHT / 2)
        run.arrows = [Arrow(run.player + Vec(500, 0), Vec(), 1, state="stuck")]
        run.recall()
        for _ in range(100):
            run.update(.02, movement=(0, -.2))
        self.assertFalse(run.over)
        self.assertFalse(run.arrows)
        run.begin_charge()
        run.release()
        self.assertEqual(len(run.arrows), 1)

    def test_square_world_preserves_original_camera_speed_scale(self):
        self.assertEqual(WIDTH, HEIGHT)
        self.assertGreater(WIDTH, 1600)
        run = isolated_run()
        start = Vec(run.player)
        run.update(.1, movement=(1, 0))
        self.assertAlmostEqual(run.player.x - start.x, 50)

    def test_original_spawn_timer_does_not_wait_for_enemy_clear(self):
        run = Run(Progress(), random.Random(12), original=True)
        run.time_left = 1000
        run.invulnerable = 1000
        for _ in range(3):
            run.update(.2)
        self.assertFalse(run.enemies)
        run.update(.2)
        self.assertEqual(len(run.enemies), 1)
        for _ in range(8):
            run.update(.2)
        self.assertGreaterEqual(len(run.enemies), 2)

    def test_survival_does_not_end_after_fifteen_normal_spawns(self):
        run = Run(Progress(), random.Random(12), original=True)
        run.original_spawn_count = 15
        run.update(.01)
        self.assertFalse(run.over)
        self.assertFalse(run.victory)


if __name__ == "__main__":
    unittest.main()
