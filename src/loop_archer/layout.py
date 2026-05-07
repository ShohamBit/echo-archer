from loop_archer import config


def arena_radius_for_screen(width: int, height: int) -> float:
    available_radius = min(width, height) / 2 - 72
    return max(config.ARENA_RADIUS, available_radius)


def health_bar_rect_for_screen(width: int, height: int) -> tuple[int, int, int, int]:
    bar_width = int(width * 0.5)
    bar_height = 30
    x = int(width * 0.25)
    y = height - 58
    return x, y, bar_width, bar_height


def dash_indicator_rect_for_screen(width: int, height: int) -> tuple[int, int, int, int]:
    health_x, health_y, health_width, health_height = health_bar_rect_for_screen(
        width,
        height,
    )
    return health_x + health_width + 18, health_y + health_height - 12, 120, 12
