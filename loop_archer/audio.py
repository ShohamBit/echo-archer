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
        self.music_paused = False
        self.music_sound = None
        self.music_channel = None
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            pygame.mixer.set_reserved(1)
            self.music_channel = pygame.mixer.Channel(0)
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
        """Reserved PCM loop; pause preserves the beat and M mutes all audio."""
        if not pygame.mixer.get_init() or self.music_channel is None:
            return
        if not battle or not self.enabled:
            if self.music_playing:
                self.music_channel.stop()
                self.music_playing = False
                self.music_paused = False
            return
        if not self.music_playing:
            try:
                if self.music_sound is None:
                    self.music_sound = pygame.mixer.Sound(str(Path(__file__).resolve().parents[1] / "assets/boss_assault.wav"))
                self.music_channel.set_volume(.48)
                self.music_channel.play(self.music_sound, loops=-1, fade_ms=500)
                self.music_playing = True
                self.music_paused = False
            except (pygame.error, OSError):
                return
        # The short PCM track avoids SDL_mixer's streaming-music resume deadlock.
        # Change playback controls only on a state transition.
        if paused != self.music_paused:
            if paused:
                self.music_channel.pause()
            else:
                self.music_channel.unpause()
            self.music_paused = paused
