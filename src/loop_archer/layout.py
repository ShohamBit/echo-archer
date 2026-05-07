from loop_archer import config


def arena_radius_for_screen(width: int, height: int) -> float:
    available_radius = min(width, height) / 2 - 72
    return max(config.ARENA_RADIUS, available_radius)
