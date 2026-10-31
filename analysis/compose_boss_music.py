"""Compose the game's original 150 BPM synth/drum boss loop using only stdlib.

No sampled recordings or third-party compositions. Run to regenerate the WAV.
"""
from array import array
import math
from pathlib import Path
import random
import wave


def compose(path):
    rate, beat, beats = 22050, .4, 64
    rng = random.Random(271)
    notes = (36, 36, 39, 34, 36, 43, 41, 34)
    samples = array("h")
    for i in range(round(rate * beat * beats)):
        t = i / rate
        step = int(t / beat)
        q = t % beat
        half = t % (beat / 2)
        sixteenth = t % (beat / 4)
        note = notes[(step // 4) % len(notes)]
        bass = 440 * 2 ** ((note - 69) / 12)
        # Bass harmonics, octave pulses and a rising minor arpeggio.
        duck = min(1, q * 14)
        low = (math.sin(math.tau * bass * t) + .25 * math.sin(math.tau * bass * 2 * t)) * math.exp(-half * 8)
        arp_note = note + (24, 31, 36, 39, 36, 31, 27, 31)[int(t / (beat / 2)) % 8]
        arp = 440 * 2 ** ((arp_note - 69) / 12)
        lead = (math.sin(math.tau * arp * t) + .2 * math.sin(math.tau * arp * 3 * t)) * math.exp(-half * 16)
        kick = math.sin(math.tau * (48 * q + 7 * (1 - math.exp(-q * 38)))) * math.exp(-q * 23)
        noise = rng.uniform(-1, 1)
        snare = noise * math.exp(-q * 32) if step % 4 in (1, 3) else 0
        hat = noise * math.exp(-sixteenth * 110) * (.7 if int(t / (beat / 4)) % 2 else 1)
        bar = step // 4
        drive = .7 + .3 * (bar % 4 / 3)
        value = (.29 * low * duck + .14 * lead * duck + .43 * kick + .24 * snare + .09 * hat) * drive
        # Short boundary fades prevent a click at the seamless bar boundary.
        edge = min(1, t / .008, (beat * beats - t) / .008)
        samples.append(int(28000 * math.tanh(value * 1.3) * max(0, edge)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(samples.tobytes())


if __name__ == "__main__":
    compose(Path(__file__).resolve().parents[1] / "assets/boss_assault.wav")
