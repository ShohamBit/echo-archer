"""Player-facing bow states, tactical boss, skillshot scoring and practice safety."""
import random
import unittest
from pygame import Vector2 as Vec
from loop_archer.boss import Warden
from loop_archer.model import Arrow, Enemy, Run
from loop_archer.progression import BY_KEY, Progress


def sandbox(levels=None):
    run = Run(Progress(levels=levels or {}), random.Random(15))
    run.wave_delay = 1000
    run.invulnerable = 1000
    run.time_left = 1000
    return run


class BowStateTests(unittest.TestCase):
    def test_ready_charge_flying_recallable_returning_and_ready_cycle(self):
        run = sandbox()
        self.assertEqual(run.bow_state, "ready")
        run.begin_charge()
        self.assertEqual(run.bow_state, "charging")
        run.release()
        self.assertEqual(run.bow_state, "flying")
        for _ in range(4):
            run.update(.2)
        self.assertEqual(run.bow_state, "recallable")
        self.assertIn("recallable", run.events)
        run.recall()
        self.assertEqual(run.bow_state, "returning")
        for _ in range(10):
            run.update(.2)
        self.assertEqual(run.bow_state, "ready")
        self.assertIn("ready", run.events)

    def test_charge_audio_fires_once_at_full_tier(self):
        run = sandbox()
        run.begin_charge()
        for _ in range(8):
            run.update(.2)
        self.assertEqual(run.events.count("charged"), 1)

    def test_mixed_volley_reports_available_recall(self):
        run = sandbox()
        run.arrows = [Arrow(Vec(200, 200), Vec(900, 0), 1), Arrow(Vec(500, 500), Vec(), 1, state="stuck")]
        self.assertEqual(run.bow_state, "recallable")
        self.assertFalse(run.can_shoot)


class WardenTests(unittest.TestCase):
    def test_attacks_telegraph_then_fire_fan_and_expose_core_after_dash(self):
        warden, pos, player = Warden(), Vec(840, 400), Vec(840, 1100)
        self.assertFalse(warden.update(.5, pos, player, (1680, 1680), 140))
        shots = warden.update(.61, pos, player, (1680, 1680), 140)
        self.assertEqual(len(shots), 5)
        self.assertEqual(warden.phase, "fan_recovery")
        warden.update(.61, pos, player, (1680, 1680), 140)
        self.assertEqual(warden.phase, "dash_windup")
        locked = Vec(warden.heading)
        warden.update(.5, pos, Vec(100, 1100), (1680, 1680), 140)
        self.assertEqual(warden.heading, locked)
        warden.update(.61, pos, player, (1680, 1680), 140)
        self.assertEqual(warden.phase, "dash")
        start = Vec(pos)
        warden.update(.5, pos, player, (1680, 1680), 140)
        self.assertGreater(pos.distance_to(start), 500)
        self.assertTrue(warden.exposed)

    def test_front_hit_is_blocked_but_exposed_rear_core_takes_damage(self):
        run = sandbox()
        enemy = Enemy(1, Vec(500, 100), "boss", hp=36, radius=100)
        enemy.warden.heading = Vec(1, 0)
        enemy.warden.target = Vec(1000, 100)
        run.enemies = [enemy]
        run.arrows = [Arrow(Vec(700, 100), Vec(-5000, 0), 99)]
        run.update(.05)
        self.assertEqual(enemy.hp, 36)
        self.assertIn("armor", run.events)
        enemy.warden.phase, enemy.warden.timer = "exposed", 2.6
        run.arrows = [Arrow(Vec(300, 100), Vec(5000, 0), 2)]
        run.update(.05)
        self.assertEqual(enemy.hp, 30)
        self.assertIn("core", run.events)

    def test_maxed_volley_cannot_skip_all_boss_cycles(self):
        run = sandbox({key: u.max_level for key, u in BY_KEY.items()})
        enemy = Enemy(1, Vec(500, 100), "boss", hp=36, radius=100)
        enemy.warden.phase, enemy.warden.timer = "exposed", 2.6
        enemy.warden.heading, enemy.warden.target = Vec(1, 0), Vec(1000, 100)
        run.enemies = [enemy]
        run.arrows = [Arrow(Vec(300, 100), Vec(5000, 0), 100) for _ in range(3)]
        run.update(.05)
        self.assertEqual(enemy.hp, 24)
        self.assertFalse(enemy.warden.exposed)

    def test_boss_entry_restores_a_readable_clock_without_changing_upgrades(self):
        run = sandbox({"damage": 2})
        run.time_left = 1
        run.spawn("boss")
        self.assertEqual(run.time_left, 30)
        self.assertEqual(run.level("damage"), 2)


class SkillshotTests(unittest.TestCase):
    def test_route_bonus_is_flat_bounded_and_only_awarded_on_kill(self):
        run = sandbox()
        run.enemies = [Enemy(1, Vec(300, 100), hp=10, speed=0)]
        run.arrows = [Arrow(Vec(100, 100), Vec(6000, 0), 1, bounces=1, portal_wraps=1)]
        run.update(.05)
        self.assertEqual(run.skillshot_bonus, 0)
        run.enemies = [Enemy(2, Vec(300, 100), hp=1, speed=0)]
        run.arrows = [Arrow(Vec(100, 100), Vec(6000, 0), 5, bounces=1, portal_wraps=1)]
        run.update(.05)
        self.assertEqual(run.skillshot_bonus, 2)
        self.assertEqual(run.skillshot_counts["Portal"], 1)
        self.assertEqual(run.skillshot_counts["Ricochet"], 1)
        self.assertEqual(run.points, 3)
        run.update(.1)
        self.assertEqual(run.skillshot_bonus, 2)

    def test_combo_expires_and_ordinary_kills_break_the_chain(self):
        run = sandbox()
        run.enemies = [Enemy(1, Vec(300, 100), hp=1, speed=0)]
        run.arrows = [Arrow(Vec(100, 100), Vec(6000, 0), 2, portal_wraps=1)]
        run.update(.05)
        self.assertEqual(run.combo, 1)
        run.arrows.clear()
        for _ in range(16):
            run.update(.2)
        self.assertEqual(run.combo, 0)
        run.combo, run.combo_timer = 5, 3
        run.enemies = [Enemy(2, Vec(300, 100), hp=1, speed=0)]
        run.arrows = [Arrow(Vec(100, 100), Vec(6000, 0), 2)]
        run.update(.05)
        self.assertEqual(run.combo, 0)


if __name__ == "__main__":
    unittest.main()
