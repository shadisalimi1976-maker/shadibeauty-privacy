#!/usr/bin/env python3
"""Background music bed for @art_rada_dxb reels (no samples, no licences needed).

Usage: python3 music.py out.wav --dur 17 --bpm 100 --drop 2.5 [--prog 0] [--end 14.5]
  --drop : time (s) of the first downbeat where drums come in (sync with the first big cut)
  --end  : time (s) where drums stop for the end card (pad + pluck carry the outro)
  --prog : chord progression 0..3 (change it day to day for variety)
Cut the video on beats: beat times are drop + k*60/bpm.
"""
import argparse, wave
import numpy as np

SR = 44100
ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('--dur', type=float, default=17)
ap.add_argument('--bpm', type=float, default=100); ap.add_argument('--drop', type=float, default=2.5)
ap.add_argument('--end', type=float, default=None); ap.add_argument('--prog', type=int, default=0)
a = ap.parse_args()
D, B = a.dur, 60 / a.bpm
END = a.end if a.end is not None else D - 2.5
N = int(SR * D); t = np.arange(N) / SR
rng = np.random.default_rng(7)
mix = np.zeros((N, 2))

def midi(n): return 440 * 2 ** ((n - 69) / 12)
def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N or i + len(sig) <= 0: return
    j0 = max(0, -i); s = sig[j0:N - i] * gain
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    mix[i + j0:i + j0 + len(s), 0] += s * l; mix[i + j0:i + j0 + len(s), 1] += s * r
def env(n, a_, d_):
    e = np.ones(n); ai = int(a_ * SR); e[:ai] = np.linspace(0, 1, ai) if ai else 1
    e *= np.exp(-np.arange(n) / SR / d_); return e
def lp(x, cutoff):  # one-pole low-pass
    k = np.exp(-2 * np.pi * cutoff / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc = (1 - k) * x[i] + k * acc; y[i] = acc
    return y

PROGS = [  # (root, chord intervals) per bar, minor-ish cinematic
    [(57, [0, 3, 7, 10, 14]), (53, [0, 4, 7, 11, 14]), (48, [0, 4, 7, 11, 14]), (55, [0, 4, 7, 9, 14])],
    [(50, [0, 3, 7, 10, 14]), (55, [0, 4, 7, 10, 14]), (48, [0, 4, 7, 11, 14]), (53, [0, 4, 7, 11, 14])],
    [(52, [0, 3, 7, 10, 14]), (48, [0, 4, 7, 11, 14]), (55, [0, 4, 7, 11, 14]), (50, [0, 3, 7, 10, 14])],
    [(57, [0, 3, 7, 10, 14]), (55, [0, 4, 7, 9, 14]), (53, [0, 4, 7, 11, 14]), (52, [0, 3, 7, 10, 14])],
]
prog = PROGS[a.prog % 4]
BAR = 4 * B
first_bar = a.drop - BAR * np.ceil(a.drop / BAR)
bars = []
s = first_bar
while s < D: bars.append(s); s += BAR

# sidechain envelope from kicks
side = np.ones(N)
kicks = [a.drop + k * B for k in range(int((END - a.drop) / B) + 1) if a.drop + k * B < END]
for kt in kicks:
    i = int(kt * SR); n = min(int(B * SR), N - i)
    side[i:i + n] = np.minimum(side[i:i + n], 1 - 0.55 * np.exp(-np.arange(n) / SR / 0.12))

# pads: detuned saws, low-passed, full length
pad = np.zeros(N)
for bi, bs in enumerate(bars):
    root, iv = prog[bi % 4]
    n = int((BAR + 0.4) * SR); tt = np.arange(n) / SR; sig = np.zeros(n)
    for x in iv:
        f = midi(root + x)
        for det in (-0.12, 0.12):
            ph = (f * (1 + det / 100 * 3)) * tt
            sig += 2 * (ph % 1) - 1
    e = np.minimum(1, tt / 0.25) * np.minimum(1, (n / SR - tt) / 0.4)
    i = int(bs * SR)
    if i < 0: sig, e, i = sig[-i:], e[-i:], 0
    m = min(len(sig), N - i); pad[i:i + m] += (sig * e)[:m]
pad = lp(lp(pad, 900), 1400) * 0.05
mix[:, 0] += pad * side; mix[:, 1] += pad * side

# sub bass: 8th pulse on chord root, from the drop
for bi, bs in enumerate(bars):
    root, _ = prog[bi % 4]
    for k in range(8):
        st = bs + k * B / 2
        if st < a.drop or st >= END: continue
        n = int(B / 2 * SR); tt = np.arange(n) / SR
        sig = np.sin(2 * np.pi * midi(root - 24) * tt) + 0.3 * np.sin(2 * np.pi * midi(root - 12) * tt)
        add(sig * env(n, 0.005, 0.18), st, 0, 0.22)

# kick
for kt in kicks:
    n = int(0.35 * SR); tt = np.arange(n) / SR
    f = 45 + 110 * np.exp(-tt / 0.04)
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.16)
    add(sig, kt, 0, 0.55)
# clap on 2 and 4
for k, kt in enumerate(kicks):
    if k % 2 == 1:
        n = int(0.25 * SR); nz = lp(rng.standard_normal(n), 3000) - lp(rng.standard_normal(n), 600) * 0.3
        add(nz * np.exp(-np.arange(n) / SR / 0.07), kt, 0.1, 0.22)
# hats: offbeat 8ths + 16th ghosts
for kt in kicks:
    for off, g in ((B / 2, 0.16), (B / 4, 0.05), (3 * B / 4, 0.05)):
        n = int(0.06 * SR); nz = rng.standard_normal(n); nz = nz - lp(nz, 6000)
        add(nz * np.exp(-np.arange(n) / SR / 0.02), kt + off, 0.35 if off == B / 2 else -0.35, g)

# pluck arpeggio (16ths) with ping-pong delay, whole track
step = B / 2
k = 0; tt0 = first_bar
while tt0 < D:
    bi = int((tt0 - first_bar) // BAR); root, iv = prog[bi % 4]
    note = root + 12 + iv[[0, 2, 4, 2, 1, 3, 4, 3][k % 8]]
    if tt0 >= 0:
        n = int(0.5 * SR); tt = np.arange(n) / SR
        sig = (np.sin(2 * np.pi * midi(note) * tt) + 0.25 * np.sin(4 * np.pi * midi(note) * tt)) * env(n, 0.003, 0.14)
        g = 0.09 if tt0 < a.drop else 0.12
        add(sig, tt0, -0.25, g); add(sig, tt0 + B * 0.75, 0.45, g * 0.45); add(sig, tt0 + B * 1.5, -0.45, g * 0.2)
    tt0 += step; k += 1

# riser into the drop + impact at the drop and at the end card
rl = min(1.6, a.drop - 0.1)
if rl > 0.3:
    n = int(rl * SR); tt = np.arange(n) / SR; nz = rng.standard_normal(n)
    nz = lp(nz, 1200) * (tt / rl) ** 2
    add(nz, a.drop - rl, 0, 0.25)
for it in (a.drop, END):
    n = int(1.5 * SR); tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-tt / 0.08)) / SR) * np.exp(-tt / 0.6)
    add(boom, it, 0, 0.45)
    nz = lp(rng.standard_normal(n), 2500) * np.exp(-tt / 0.35)
    add(nz, it, 0, 0.08)

# master: fades, soft clip, normalise to -1 dBFS
fi = np.minimum(1, t / 0.4); fo = np.clip((D - t) / 1.8, 0, 1)
mix *= (fi * fo)[:, None]
mix = np.tanh(mix * 1.6)
mix *= 0.89 / np.max(np.abs(mix))
with wave.open(a.out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('beats from', a.drop, 'every', round(B, 3), 's; drums stop at', END)
