"""Regression for the Windows mixer freeze caused by repeated music resumes."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest
from unittest.mock import Mock, patch


class MusicFreezeTests(unittest.TestCase):
    def test_unchanged_playback_does_not_reissue_pause_or_resume(self):
        from loop_archer.audio import Audio
        # A fake mixer tests control traffic without risking a native deadlock.
        audio = Audio.__new__(Audio)
        audio.enabled = True
        audio.music_playing = False
        audio.music_paused = False
        audio.music_sound = Mock()
        audio.music_channel = music = Mock()
        with patch("pygame.mixer.get_init", return_value=(22050, -16, 1)):
            for _ in range(60):
                audio.sync_music(True)
            music.play.assert_called_once()
            music.unpause.assert_not_called()
            for _ in range(60):
                audio.sync_music(True, paused=True)
            music.pause.assert_called_once()
            for _ in range(60):
                audio.sync_music(True)
            music.unpause.assert_called_once()
            for _ in range(60):
                audio.sync_music(False)
            music.stop.assert_called_once()

    def test_real_mixer_remains_responsive_with_music_cues_and_state_changes(self):
        # Keep a native freeze isolated so it cannot hang the whole test suite.
        code = textwrap.dedent("""
            import faulthandler
            import time
            import pygame
            from loop_archer.audio import Audio
            faulthandler.dump_traceback_later(3)
            audio = Audio()
            assert audio.enabled, 'Dummy audio driver failed to initialize'
            for frame in range(600):
                audio.enabled = not 400 <= frame < 410
                audio.sync_music(True, paused=200 <= frame < 210)
                if frame % 20 == 0:
                    audio.play('shoot')
                time.sleep(.002)
            audio.sync_music(False)
            pygame.quit()
            faulthandler.cancel_dump_traceback_later()
            print('Music and controls completed')
        """)
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=Path(__file__).resolve().parents[1],
                env={**os.environ, "SDL_AUDIODRIVER": "dummy", "SDL_VIDEODRIVER": "dummy"},
                capture_output=True, text=True, timeout=8,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(f"Audio mixer froze while syncing boss music:\n{exc.stderr}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Music and controls completed", result.stdout)


if __name__ == "__main__":
    unittest.main()
