"""Small original synthesized cues; the remake needs no extracted audio assets."""
from array import array
import math
from pathlib import Path
import pygame


class Audio:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self.music_playing = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            for name, frequency, duration in (("shoot", 700, .08), ("recall", 350, .16),
                                               ("hit", 180, .045), ("kill", 500, .09),
                                               ("shield", 950, .2), ("death", 100, .5),
                                               ("win", 800, .5), ("buy", 1100, .12),
                                               ("recallable", 480, .07), ("ready", 850, .08),
                                               ("pickup", 1050, .06), ("charged", 1200, .10),
                                               ("armor", 140, .06), ("core", 950, .16),
                                               ("skillshot", 1300, .1)):
                samples = array("h", (int(6000 * (1 - i / (22050 * duration)) ** 2 *
                                          math.sin(2 * math.pi * frequency * (i / 22050) *
                                                   (1 + .4 * i / (22050 * duration))))
                                      for i in range(int(22050 * duration))))
                self.sounds[name] = pygame.mixer.Sound(buffer=samples)
        except pygame.error:
            self.enabled = False

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def sync_music(self, battle, paused=False):
        """One streamed loop; pause preserves the beat and M mutes music and cues."""
        if not pygame.mixer.get_init():
            return
        if not battle or not self.enabled:
            if self.music_playing:
                pygame.mixer.music.stop()
                self.music_playing = False
            return
        if not self.music_playing:
            try:
                pygame.mixer.music.load(str(Path(__file__).resolve().parents[1] / "assets/boss_assault.wav"))
                pygame.mixer.music.set_volume(.48)
                pygame.mixer.music.play(-1, fade_ms=500)
                self.music_playing = True
            except (pygame.error, OSError):
                return
        if paused:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
