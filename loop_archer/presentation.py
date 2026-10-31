"""Presentation preferences. Smooth vector rendering needs no full-frame filter."""


class Presentation:
    def __init__(self):
        self.shake = True
        self.flashes = True
        self.trails = True

    def apply(self, surface):
        # Deliberate no-op: pixelation and channel/glow copies caused ~89ms/frame.
        # Local vector trails are drawn with geometry in the arena, without
        # touching a full-frame pixel buffer or scaling the text down.
        return surface
