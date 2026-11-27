"""Genera una storia Instagram 9:16 di 10s dall'immagine Baila Bonita.

Uso: python3 make_story.py <immagine.png> <output.mp4>
Richiede: numpy, opencv-python-headless, Pillow, ffmpeg.
"""
import math
import subprocess
import sys
import wave

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1080, 1920, 30, 10.0
N = int(FPS * DUR)
BPM = 100
BEAT = 60.0 / BPM
SR = 44100
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- audio (dembow)
def make_audio(path):
    n = int(SR * DUR)
    out = np.zeros(n, np.float32)
    six = BEAT / 4

    def add(sig, t):
        i = int(t * SR)
        if i >= n:
            return
        e = min(n, i + len(sig))
        out[i:e] += sig[: e - i]

    tk = np.arange(int(0.35 * SR)) / SR
    kick = np.sin(2 * np.pi * np.cumsum(50 + 110 * np.exp(-tk * 30)) / SR) * np.exp(-tk * 9)
    ts = np.arange(int(0.18 * SR)) / SR
    noise = rng.standard_normal(len(ts))
    snare = (0.6 * noise * np.exp(-ts * 22) + 0.5 * np.sin(2 * np.pi * 190 * ts) * np.exp(-ts * 30))
    th = np.arange(int(0.05 * SR)) / SR
    hat = np.diff(rng.standard_normal(len(th) + 1)) * np.exp(-th * 80) * 0.18
    bass_notes = [43.65, 43.65, 51.91, 49.0]  # F1 F1 G#1 G1
    bar = 4 * BEAT
    t = 0.0
    bi = 0
    while t < DUR:
        for s in range(16):
            ts_ = t + s * six
            if s in (0, 4, 8, 12):
                add(kick * 0.9, ts_)
            if s in (3, 6, 11, 14):
                add(snare * 0.55, ts_)
            if s % 2 == 0:
                add(hat, ts_ + six)
        f = bass_notes[bi % 4]
        tb = np.arange(int(bar * SR)) / SR
        bass = np.tanh(2.5 * np.sin(2 * np.pi * f * 2 * tb)) * 0.18 * (0.6 + 0.4 * np.exp(-(tb % BEAT) * 4))
        add(bass, t)
        t += bar
        bi += 1
    # riser iniziale
    tr = np.arange(int(0.6 * SR)) / SR
    riser = rng.standard_normal(len(tr)) * (tr / 0.6) ** 2 * 0.15
    add(riser[::-1] * 0 + riser, 0)
    fade = np.ones(n, np.float32)
    fl = int(0.4 * SR)
    fade[-fl:] = np.linspace(1, 0, fl)
    out *= fade
    out /= max(1e-6, np.abs(out).max()) / 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- immagini base
src = cv2.cvtColor(cv2.imread(SRC), cv2.COLOR_BGR2RGB)
sh, sw = src.shape[:2]

# sfondo: immagine sfocata a copertura totale
bs = max(W / sw, H / sh) * 1.15
bg_big = cv2.resize(src, (int(sw * bs), int(sh * bs)), interpolation=cv2.INTER_AREA)
bg_big = cv2.GaussianBlur(bg_big, (0, 0), 28).astype(np.float32)
pink = np.array([255, 70, 170], np.float32)
bg_big = bg_big * 0.65 + pink * 0.35

# primo piano
FW = 1180
fs = FW / sw
FH = int(sh * fs)
fg = cv2.resize(src, (FW, FH), interpolation=cv2.INTER_AREA).astype(np.float32)
alpha = np.ones((FH, FW), np.float32)
feather = 140
ramp = np.linspace(0, 1, feather)
alpha[:feather] *= ramp[:, None]
alpha[-feather:] *= ramp[::-1][:, None]
fg_rgba = np.dstack([fg, alpha * 255])

gy, gx = np.mgrid[0:FH, 0:FW].astype(np.float32)
yn, xn = gy / FH, gx / FW

# vignetta
vy, vx = np.mgrid[0:H, 0:W].astype(np.float32)
vd = np.sqrt(((vx - W / 2) / (W * 0.75)) ** 2 + ((vy - H / 2) / (H * 0.7)) ** 2)
vignette = np.clip(1.15 - vd * 0.55, 0.55, 1.0)[..., None]

# testo
font_big = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf", 118)
font_small = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-ExtraBoldItalic.otf", 52)


def text_layer(txt, font, fill, stroke):
    tmp = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), txt, font=font, stroke_width=8)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((W - tw) / 2 - bb[0], (260 - th) / 2 - bb[1]), txt, font=font, fill=fill,
           stroke_width=8, stroke_fill=stroke)
    return np.asarray(tmp).astype(np.float32)


title = text_layer("BAILA BONITA", font_big, (255, 255, 255, 255), (255, 20, 147, 255))
sub = text_layer("FLORA  •  SAFFI", font_small, (255, 20, 147, 255), (255, 255, 255, 255))

# ---------------------------------------------------------------- particelle
def heart_poly(cx, cy, s, rot):
    t = np.linspace(0, 2 * np.pi, 40)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    c, si = math.cos(rot), math.sin(rot)
    xr, yr = x * c - y * si, x * si + y * c
    return np.stack([cx + xr * s / 16, cy + yr * s / 16], 1).astype(np.int32)


def star_poly(cx, cy, r, rot):
    pts = []
    for k in range(8):
        rr = r if k % 2 == 0 else r * 0.22
        a = rot + k * math.pi / 4
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return np.array(pts, np.int32)


NH = 26
hearts = dict(x=rng.uniform(0, W, NH), y0=rng.uniform(0, H + 400, NH), sp=rng.uniform(120, 320, NH),
              s=rng.uniform(22, 60, NH), ph=rng.uniform(0, 6.28, NH),
              col=rng.choice([0, 1, 2], NH))
HCOL = [(255, 255, 255), (255, 105, 180), (255, 20, 147)]
NS = 40
stars = dict(x=rng.uniform(0, W, NS), y=rng.uniform(0, H, NS), r=rng.uniform(14, 40, NS),
             ph=rng.uniform(0, 6.28, NS), f=rng.uniform(1.5, 4, NS))

# ---------------------------------------------------------------- helpers
def screen(a, b):
    return 255 - (255 - a) * (255 - b) / 255


def pulse(t, k=7.0):
    tb = t % BEAT
    return math.exp(-tb * k)


def ease_out(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3


# ---------------------------------------------------------------- render
AUDIO = OUT + ".wav"
make_audio(AUDIO)

ff = subprocess.Popen([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", AUDIO,
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT,
], stdin=subprocess.PIPE)

for i in range(N):
    t = i / FPS
    beat_idx = int(t / BEAT)
    p = pulse(t)
    accent = beat_idx % 4 == 0
    pa = p if accent else 0.0
    intro = ease_out(t / 0.7)
    outro = max(0.0, (t - (DUR - 0.5)) / 0.5)

    # --- sfondo con zoom lento e pulsazione
    bz = 1.0 + 0.04 * (t / DUR) + 0.03 * p
    bh_, bw_ = bg_big.shape[:2]
    M = cv2.getRotationMatrix2D((bw_ / 2, bh_ / 2), 0.0, bz)
    M[0, 2] += W / 2 - bw_ / 2
    M[1, 2] += H / 2 - bh_ / 2
    frame = cv2.warpAffine(bg_big, M, (W, H), borderMode=cv2.BORDER_REFLECT)

    # luce colorata che si muove
    lx = W * (0.5 + 0.45 * math.sin(t * 1.3))
    ly = H * (0.35 + 0.3 * math.cos(t * 0.9))
    d2 = ((vx - lx) ** 2 + (vy - ly) ** 2) / (520 ** 2)
    leak = np.exp(-d2)[..., None] * np.array([255, 120, 220], np.float32) * (0.35 + 0.35 * p)
    frame = screen(frame, leak)

    # --- "ballo": onda del corpo + rimbalzo, ragazze in controfase
    w = 2 * math.pi * t / (2 * BEAT)
    amp = 16 * intro
    dx = amp * np.sin(w + math.pi * xn - 2.2 * yn) * (0.35 + 0.65 * yn)
    sq = 0.028 * p
    dy = -(sq * (gy - FH)) + 6 * np.sin(2 * w + math.pi * xn) * yn * intro
    warped = cv2.remap(fg_rgba, gx - dx, gy - dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    zoom = 1.0 + 0.045 * p + 0.25 * (1 - intro)
    rot = 2.2 * math.sin(w) * intro
    shx = (rng.uniform(-1, 1) * 14 * pa)
    shy = (rng.uniform(-1, 1) * 14 * pa) - 18 * abs(math.sin(w * 2)) * intro
    M = cv2.getRotationMatrix2D((FW / 2, FH * 0.75), rot, zoom)
    M[0, 2] += W / 2 - FW / 2 + shx
    M[1, 2] += (H - FH) / 2 + 60 + shy - FH * 0.25 * (zoom - 1) * 0 + 0
    layer = cv2.warpAffine(warped, M, (W, H), flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = layer[..., 3:4] / 255
    frame = frame * (1 - a) + layer[..., :3] * a

    # --- cuori che salgono
    hl = np.zeros((H, W, 3), np.float32)
    for k in range(NH):
        y = (hearts["y0"][k] - hearts["sp"][k] * t) % (H + 400) - 200
        x = hearts["x"][k] + 30 * math.sin(t * 2 + hearts["ph"][k])
        s = hearts["s"][k] * (1 + 0.25 * p)
        cv2.fillPoly(hl, [heart_poly(x, y, s, 0.3 * math.sin(t * 3 + hearts["ph"][k]))],
                     HCOL[hearts["col"][k]], lineType=cv2.LINE_AA)
    glow = cv2.GaussianBlur(hl, (0, 0), 10)
    hm = (hl.max(axis=2, keepdims=True) > 0).astype(np.float32) * 0.85
    frame = screen(frame, glow * 0.6)
    frame = frame * (1 - hm) + hl * hm

    # --- scintillii
    sl = np.zeros((H, W, 3), np.float32)
    for k in range(NS):
        tw = 0.5 + 0.5 * math.sin(t * stars["f"][k] * 2 + stars["ph"][k])
        tw = tw ** 3 * (0.4 + 0.6 * p)
        if tw < 0.05:
            continue
        cv2.fillPoly(sl, [star_poly(stars["x"][k], stars["y"][k], stars["r"][k] * tw * 1.4, t)],
                     (255, 255, 255), lineType=cv2.LINE_AA)
    sl = sl + cv2.GaussianBlur(sl, (0, 0), 8) * 1.5
    frame = screen(frame, np.clip(sl, 0, 255))

    # --- testo in alto (pop sul beat)
    if t > 0.5:
        ts_ = ease_out((t - 0.5) / 0.35)
        sc = (0.4 + 0.6 * ts_) * (1 + 0.06 * p)
        for lay, cy in ((title, 170), (sub, 1790)):
            M = cv2.getRotationMatrix2D((W / 2, 130), -3 * math.sin(w), sc)
            M[1, 2] += cy - 130
            tl = cv2.warpAffine(lay, M, (W, H), borderValue=(0, 0, 0, 0))
            ta = tl[..., 3:4] / 255 * ts_
            frame = frame * (1 - ta) + tl[..., :3] * ta

    # --- glitch a fasce sugli accenti
    if pa > 0.35:
        for _ in range(6):
            y0 = int(rng.uniform(0, H - 80))
            hgt = int(rng.uniform(10, 70))
            frame[y0:y0 + hgt] = np.roll(frame[y0:y0 + hgt], int(rng.uniform(-60, 60)), axis=1)

    # --- RGB split
    off = int(3 + 14 * p * (1.6 if accent else 0.6))
    frame[..., 0] = np.roll(frame[..., 0], off, axis=1)
    frame[..., 2] = np.roll(frame[..., 2], -off, axis=1)

    frame = frame * vignette
    # flash
    fl = 0.45 * pa + (1 - intro) * 0.9 + outro * 0.9
    frame = frame * (1 - fl) + np.array([255, 235, 245], np.float32) * fl

    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    if i % 30 == 0:
        print(f"frame {i}/{N}", flush=True)

ff.stdin.close()
ff.wait()
print("fatto:", OUT)
