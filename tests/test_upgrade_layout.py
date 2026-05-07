from loop_archer.main import upgrade_screen_layout
from loop_archer.upgrades import UPGRADE_DEFINITIONS


def test_upgrade_screen_layout_places_cards_in_branch_columns():
    layout = upgrade_screen_layout(1280, 720, UPGRADE_DEFINITIONS.values())

    assert set(layout.card_rects) == set(UPGRADE_DEFINITIONS)

    branch_x_positions = {}
    for branch in ("Archer", "Survivor", "Echo"):
        x_positions = {
            layout.card_rects[upgrade.id].x
            for upgrade in UPGRADE_DEFINITIONS.values()
            if upgrade.branch == branch
        }
        assert len(x_positions) == 1
        branch_x_positions[branch] = x_positions.pop()

    assert branch_x_positions["Archer"] < branch_x_positions["Survivor"]
    assert branch_x_positions["Survivor"] < branch_x_positions["Echo"]


def test_upgrade_screen_layout_keeps_cards_visible_and_clear_of_restart_button():
    layout = upgrade_screen_layout(1280, 720, UPGRADE_DEFINITIONS.values())
    rects = list(layout.card_rects.values())

    assert all(layout.panel_rect.contains(rect) for rect in rects)
    assert all(rect.bottom <= layout.restart_button_rect.top - 12 for rect in rects)

    for index, rect in enumerate(rects):
        for other in rects[index + 1 :]:
            assert not rect.colliderect(other)


def test_upgrade_screen_layout_compresses_on_smaller_windows():
    layout = upgrade_screen_layout(800, 600, UPGRADE_DEFINITIONS.values())
    rects = list(layout.card_rects.values())

    assert layout.compact_cards is True
    assert all(layout.panel_rect.contains(rect) for rect in rects)
    assert all(rect.bottom <= layout.restart_button_rect.top - 12 for rect in rects)

    for index, rect in enumerate(rects):
        for other in rects[index + 1 :]:
            assert not rect.colliderect(other)
