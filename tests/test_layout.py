from loop_archer import config
from loop_archer.layout import arena_radius_for_screen


def test_arena_radius_uses_more_space_on_large_screens():
    large_screen_radius = arena_radius_for_screen(1920, 1080)

    assert large_screen_radius > config.ARENA_RADIUS
    assert large_screen_radius <= 1080 / 2 - 72


def test_arena_radius_keeps_default_size_for_mvp_window():
    assert arena_radius_for_screen(1280, 720) == config.ARENA_RADIUS
