#!/usr/bin/env python3
"""Synthesize the Halloween cat sounds: a quiet curious meow (approach) and a magical meow plus tiny cackle (ring).

Additive vocal model: harmonics of a gliding pitch weighted by moving formant peaks. Writes 44.1 kHz mono WAV,
then ffmpeg encodes ogg (doorbell-local ring sound) and mp3 (Home Assistant approach cue).
Usage: python3 make_sounds.py OUTDIR
"""
import subprocess, sys, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def interp(points, t, dur):
    xs = [p[0] * dur for p in points]
    ys = [p[1] for p in points]
    return np.interp(t, xs, ys)


def voice(dur, f0_pts, f1_pts, f2_pts, amp_pts, vib=6.0, vib_depth=0.015, breath=0.04, f3=2900):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = interp(f0_pts, t, dur) * (1 + vib_depth * np.sin(2 * np.pi * vib * t))
    f1, f2 = interp(f1_pts, t, dur), interp(f2_pts, t, dur)
    amp = interp(amp_pts, t, dur)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    out = np.zeros(n)
    for k in range(1, 45):
        fk = k * f0
        g = (1.0 / (1 + ((fk - f1) / 140) ** 2)
             + 0.8 / (1 + ((fk - f2) / 220) ** 2)
             + 0.35 / (1 + ((fk - f3) / 350) ** 2)) / k ** 0.6
        g = np.where(fk < 6500, g, 0)
        out += g * np.sin(k * phase)
    noise = rng.standard_normal(n)
    noise = np.convolve(noise, np.ones(12) / 12, mode="same")
    out = out / np.max(np.abs(out)) + breath * noise
    return out * amp


def env(n, attack=0.01, release=0.05):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] = np.linspace(1, 0, r)
    return e


def sparkle(start_hz, steps, step_s, decay_s):
    """Rising bell arpeggio: the 'magic' in the ring meow."""
    n = int((steps * step_s + decay_s) * SR)
    out = np.zeros(n)
    for i in range(steps):
        f = start_hz * (1.26 ** i)
        t = np.arange(int(decay_s * SR)) / SR
        bell = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 11)
        o = int(i * step_s * SR)
        out[o:o + len(bell)] += bell * (0.8 ** i)
    return out


def curious_meow():
    d = 0.8
    v = voice(d, [(0, 520), (0.35, 640), (0.75, 900), (1, 820)], [(0, 450), (0.5, 700), (1, 550)],
              [(0, 2100), (0.5, 1500), (1, 1700)], [(0, 0), (0.08, 1), (0.7, 0.9), (1, 0)])
    return v * env(len(v), 0.02, 0.12)


def ring_meow():
    meow = voice(1.1, [(0, 480), (0.25, 780), (0.6, 700), (1, 430)], [(0, 400), (0.35, 820), (0.7, 700), (1, 480)],
                 [(0, 2300), (0.4, 1500), (1, 1100)], [(0, 0), (0.06, 1), (0.8, 0.85), (1, 0)])
    meow *= env(len(meow), 0.02, 0.15)
    sp = sparkle(1300, 5, 0.07, 0.45) * 0.35
    cack = []
    for i in range(5):
        c = voice(0.11, [(0, 900 - 40 * i), (1, 620 - 30 * i)], [(0, 700), (1, 600)], [(0, 1500), (1, 1300)],
                  [(0, 0), (0.15, 1), (1, 0)], vib_depth=0.03, breath=0.08)
        cack += [c * env(len(c), 0.005, 0.03), np.zeros(int(0.075 * SR))]
    cack = np.concatenate(cack) * 0.75
    gap = np.zeros(int(0.12 * SR))
    body = np.concatenate([meow, gap])
    mix = np.zeros(len(body) + len(cack) + 200)
    mix[:len(body)] += body
    mix[:len(sp)] += np.pad(sp, (0, max(0, 0)))[:len(mix)]
    mix[len(body):len(body) + len(cack)] += cack
    return mix


def save(path, x, peak):
    x = x / np.max(np.abs(x)) * peak
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    out = sys.argv[1]
    save(f"{out}/meow-curious.wav", curious_meow(), 0.5)
    save(f"{out}/meow-ring.wav", ring_meow(), 0.7)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{out}/meow-curious.wav", "-af", "volume=0.25", "-codec:a", "libmp3lame", "-q:a", "4", f"{out}/meow-curious.mp3"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{out}/meow-ring.wav", "-strict", "-2", "-codec:a", "vorbis", "-ar", "44100", "-ac", "2", "-q:a", "5", f"{out}/halloween-ring.ogg"], check=True)
    print("ok")
