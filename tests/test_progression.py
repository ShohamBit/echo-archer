"""Upgrade and save integrity tests using isolated temporary directories."""
import json
from pathlib import Path
import tempfile
import unittest

from loop_archer.progression import BY_KEY, Progress, load_progress, save_progress


class ProgressionTests(unittest.TestCase):
    def test_unaffordable_or_locked_purchase_does_not_spend_points(self):
        progress = Progress(points=1)
        self.assertFalse(progress.buy("damage"))
        self.assertEqual(progress.points, 1)
        progress.points = 1000
        self.assertFalse(progress.buy("charge"))
        self.assertEqual(progress.points, 1000)
        self.assertFalse(progress.buy("unknown-upgrade"))

    def test_purchase_unlocks_child_and_max_rank_cannot_be_exceeded(self):
        progress = Progress(points=10000)
        initial_cost = progress.cost("damage")
        self.assertTrue(progress.buy("damage"))
        self.assertEqual(progress.points, 10000 - initial_cost)
        self.assertTrue(progress.unlocked("charge"))
        for _ in range(BY_KEY["damage"].max_level - 1):
            self.assertTrue(progress.buy("damage"))
        points_before = progress.points
        self.assertFalse(progress.buy("damage"))
        self.assertEqual(progress.level("damage"), BY_KEY["damage"].max_level)
        self.assertEqual(progress.points, points_before)

    def test_roundtrip_retains_all_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "progress.json"
            original = Progress(points=42, levels={"damage": 2}, loops=3,
                                best_wave=5, best_kills=20)
            save_progress(path, original)
            loaded, warning = load_progress(path)
            self.assertEqual(loaded, original)
            self.assertFalse(warning)
            self.assertFalse(path.with_suffix(".tmp").exists())

    def test_sale_reduces_prices_and_never_makes_them_free(self):
        normal = Progress()
        discounted = Progress(levels={"sale": 1})
        self.assertEqual(discounted.cost("charge"), max(1, normal.cost("charge") - 5))
        self.assertEqual(discounted.cost("damage"), 1)
        discounted.levels["sale"] = 2
        self.assertEqual(discounted.cost("damage"), 1)

    def test_absent_save_starts_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            progress, warning = load_progress(Path(directory) / "missing.json")
            self.assertEqual(progress, Progress())
            self.assertFalse(warning)

    def test_bad_save_is_preserved_and_returns_warning(self):
        invalid = ["broken json", "[]", '{"version": 999}',
                   '{"version": 1, "points": -1}',
                   '{"version": 1, "points": true}',
                   '{"version": 1, "levels": {"damage": 999}}',
                   '{"version": 1, "levels": {"damage": true}}']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            for content in invalid:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    progress, warning = load_progress(path)
                    self.assertEqual(progress, Progress())
                    self.assertTrue(warning)
                    self.assertEqual(path.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
