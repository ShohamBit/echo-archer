"""Behavior checks for the spatial tree and its purchase gestures."""
import unittest
from pygame import Vector2
from loop_archer.shop import SkillTree, POSITIONS, VIEW
from loop_archer.progression import Progress, BY_KEY


class SpatialTreeTests(unittest.TestCase):
    def test_fresh_profile_starts_with_only_damage_and_reveals_its_children(self):
        tree, progress = SkillTree(), Progress(points=100)
        self.assertEqual(tree.visible(progress), {"damage"})
        progress.buy("damage")
        self.assertEqual(tree.visible(progress), {"damage", "charge", "time", "movement", "recall"})

    def test_map_preserves_original_branch_directions(self):
        self.assertEqual(POSITIONS["damage"], [0, 0])
        self.assertLess(POSITIONS["recall"][0], 0)
        self.assertLess(POSITIONS["charge"][1], 0)
        self.assertGreater(POSITIONS["time"][1], 0)

    def test_short_click_does_not_buy_and_one_hold_only_requests_one_rank(self):
        tree, progress = SkillTree(), Progress(points=100)
        mouse = tree.point("damage")
        tree.begin(mouse, progress)
        self.assertIsNone(tree.update(.2, mouse, progress))
        tree.release()
        self.assertIsNone(tree.update(1, mouse, progress))
        tree.begin(mouse, progress)
        self.assertEqual(tree.update(.6, mouse, progress), "damage")
        self.assertIsNone(tree.update(3, mouse, progress))

    def test_leaving_node_or_panning_cancels_purchase(self):
        tree, progress = SkillTree(), Progress(points=100)
        mouse = tree.point("damage")
        tree.begin(mouse, progress)
        self.assertIsNone(tree.update(.6, (VIEW.left - 10, 400), progress))
        self.assertIsNone(tree.holding)
        tree.begin(mouse, progress)
        tree.pan((20, 10))
        self.assertIsNone(tree.holding)

    def test_zoom_keeps_cursor_world_position_and_pan_keeps_nodes_clickable(self):
        tree, progress = SkillTree(), Progress(points=100)
        mouse = Vector2(700, 450)
        before = (mouse - VIEW.center) / tree.zoom + tree.camera
        tree.zoom_at(3, mouse)
        after = (mouse - VIEW.center) / tree.zoom + tree.camera
        self.assertLess(before.distance_to(after), .00001)
        tree.pan((80, 50))
        self.assertEqual(tree.hit(tree.point("damage"), progress), "damage")

    def test_maxed_profile_keeps_every_node_visible(self):
        tree = SkillTree()
        progress = Progress(levels={key: u.max_level for key, u in BY_KEY.items()})
        self.assertEqual(tree.visible(progress), set(BY_KEY))


if __name__ == "__main__":
    unittest.main()
