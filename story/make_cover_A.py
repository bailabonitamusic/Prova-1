"""Video copertina stile A (retro come il logo Baila Bonita) con scritte animate appariscenti.

- lettere che saltano dentro una alla volta (rimbalzo, rotazione)
- effetto 3D (estrusione rosa scuro) + alone rosa
- esplosione di scintille quando ogni riga e' completa
- riflesso luminoso che passa sulle scritte e leggera onda delle lettere

Uso: python3 make_cover_A.py <video_in.mp4> <video_out.mp4> [bpm] [offset_primo_battito_s]
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
BEAT0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
SHR = os.path.join(FD, "Shrikhand-Regular.ttf")

WHITE, HOT, DEEP = (255, 255, 255), (255, 20, 147), (150, 0, 80)
rng = np.random.default_rng(3)


# ------------------------------------------------------------------ rendering lettere
def render_letters(txt, size, fill, stroke, stroke_col, extrude=9):
    """Ritorna lista di (img RGBA float, cx_rel, cy_rel) per ogni lettera + larghezza riga."""
    f = ImageFont.truetype(SHR, size)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    ws = [d0.textlength(c, font=f) for c in txt]
    total = sum(ws)
    asc, desc = f.getmetrics()
    pad = stroke + extrude + 40
    out = []
    x = -total / 2
    for c, cw in zip(txt, ws):
        if c == " ":
            x += cw
            continue
        bw, bh = int(cw + 2 * pad + size * 0.3), int(asc + desc + 2 * pad)
        ox, oy = pad, pad
        glow = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((ox, oy), c, font=f, fill=HOT + (255,), stroke_width=stroke + 8,
                                  stroke_fill=HOT + (255,))
        glow = glow.filter(ImageFilter.GaussianBlur(16))
        img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        img = Image.alpha_composite(img, glow)
        d = ImageDraw.Draw(img)
        for e in range(extrude, 0, -1):  # estrusione 3D
            shade = tuple(int(v * (0.75 + 0.25 * (1 - e / extrude))) for v in DEEP)
            d.text((ox + e * 0.6, oy + e), c, font=f, fill=shade + (255,), stroke_width=stroke,
                   stroke_fill=shade + (255,))
        d.text((ox, oy), c, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=stroke_col + (255,))
        # lucentezza: meta' superiore leggermente piu' chiara
        arr = np.asarray(img).astype(np.float32)
        fillmask = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(fillmask).text((ox, oy), c, font=f, fill=255)
        fm = np.asarray(fillmask).astype(np.float32) / 255
        grad = np.clip(1 - (np.arange(bh)[:, None] - oy) / (asc * 0.9), 0, 1) * 0.25
        arr[..., :3] = arr[..., :3] * (1 - fm[..., None] * grad[..., None]) + 255 * fm[..., None] * grad[..., None]
        cx_rel = x + cw / 2
        img_cx = ox + cw / 2
        img_cy = oy + (asc + desc) / 2
        out.append(dict(img=arr, fill=fm, cx=cx_rel, ax=img_cx, ay=img_cy))
        x += cw
    return out, total


# riga: testo, dimensione, colore, contorno, colore contorno, centro_y, inizio, ritardo lettere, onda
LINES = [
    ("Venerdì 4 Dicembre", 92, WHITE, 9, HOT, 190, 0.30, 0.035, False),
    ("DJ SET", 72, HOT, 7, WHITE, 1395, 1.00, 0.05, False),
    ("Baila Bonita", 128, WHITE, 11, HOT, 1510, 1.20, 0.045, True),
    ("Red Master", 128, WHITE, 11, HOT, 1650, 1.55, 0.045, True),
    ("21:00 - 00:00", 74, WHITE, 9, HOT, 1785, 1.95, 0.03, False),
]
lines = []
for txt, size, fill, stroke, scol, cy, start, stag, wave in LINES:
    letters, total = render_letters(txt, size, fill, stroke, scol)
    done = start + stag * (len(letters) - 1) + 0.4
    lines.append(dict(letters=letters, total=total, cy=cy, start=start, stag=stag, wave=wave, done=done,
                      size=size))


# ------------------------------------------------------------------ scintille
def star_img(r):
    s = int(r * 2 + 30)
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    pts = []
    for k in range(8):
        rr = r if k % 2 == 0 else r * 0.22
        a = k * math.pi / 4 - math.pi / 2
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon(pts, fill=(255, 255, 255, 255))
    g = im.filter(ImageFilter.GaussianBlur(5))
    out = Image.alpha_composite(Image.new("RGBA", (s, s), (0, 0, 0, 0)), g)
    out = Image.alpha_composite(out, g)
    out = Image.alpha_composite(out, im)
    return np.asarray(out).astype(np.float32)


STAR = star_img(26)
bursts = []
for ln in lines:
    n = 10 if ln["size"] > 100 else 6
    for _ in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        bursts.append(dict(t0=ln["done"] - 0.15 + rng.uniform(0, 0.15),
                           x=W / 2 + rng.uniform(-0.5, 0.5) * ln["total"],
                           y=ln["cy"] + rng.uniform(-0.4, 0.4) * ln["size"],
                           vx=math.cos(ang) * rng.uniform(120, 320), vy=math.sin(ang) * rng.uniform(80, 240),
                           s=rng.uniform(0.5, 1.2)))


# ------------------------------------------------------------------ helpers
def clamp01(x):
    return min(max(x, 0.0), 1.0)


def ease_back(x, k=2.4):
    x = clamp01(x)
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


def paste_local(frame, img, ax, ay, X, Y, scale=1.0, angle=0.0, alpha=1.0, extra_rgb=None):
    """Incolla img (ancora ax,ay) centrata in X,Y con scala/rotazione, solo nella zona interessata."""
    if alpha <= 0.01 or scale <= 0.01:
        return
    h0, w0 = img.shape[:2]
    M = cv2.getRotationMatrix2D((ax, ay), angle, scale)
    M[0, 2] += X - ax
    M[1, 2] += Y - ay
    corners = np.array([[0, 0, 1], [w0, 0, 1], [0, h0, 1], [w0, h0, 1]], np.float32) @ M.T
    x0, y0 = np.floor(corners.min(0)).astype(int)
    x1, y1 = np.ceil(corners.max(0)).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0:
        return
    M2 = M.copy()
    M2[0, 2] -= x0
    M2[1, 2] -= y0
    lay = cv2.warpAffine(img, M2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = lay[..., 3:4] / 255 * alpha
    rgb = lay[..., :3]
    if extra_rgb is not None:
        rgb = np.clip(rgb + extra_rgb, 0, 255)
    region = frame[y0:y1, x0:x1]
    frame[y0:y1, x0:x1] = region * (1 - a) + rgb * a


def beat_pulse(t):
    if BPM <= 0:
        return 0.0
    per = 60.0 / BPM
    if t < BEAT0:
        return 0.0
    return math.exp(-((t - BEAT0) % per) * 9)


# ------------------------------------------------------------------ render
cap = cv2.VideoCapture(SRC)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
dur = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps
ff = subprocess.Popen([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
    "-i", SRC, "-map", "0:v", "-map", "1:a?",
    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "-shortest", "-movflags", "+faststart", OUT,
], stdin=subprocess.PIPE)

i = 0
while True:
    ok, fr = cap.read()
    if not ok:
        break
    t = i / fps
    end = 1 - clamp01((t - (dur - 0.4)) / 0.4)
    frame = cv2.cvtColor(cv2.resize(fr, (W, H), interpolation=cv2.INTER_LANCZOS4),
                         cv2.COLOR_BGR2RGB).astype(np.float32)
    bp = beat_pulse(t)

    for li, ln in enumerate(lines):
        n = len(ln["letters"])
        # riflesso: banda che attraversa la riga ogni 3 s dopo l'ingresso
        sh_t = (t - ln["done"] - 0.3 - li * 0.12) % 3.0 if t > ln["done"] + 0.3 else None
        band_x = None
        if sh_t is not None and sh_t < 0.7:
            band_x = -ln["total"] / 2 - 150 + (ln["total"] + 300) * (sh_t / 0.7)
        for k, L in enumerate(ln["letters"]):
            p = (t - ln["start"] - k * ln["stag"]) / 0.42
            if p <= 0:
                continue
            e = ease_back(p)
            scale = 0.15 + 0.85 * e
            rot = (18 if k % 2 else -18) * (1 - clamp01(p * 1.2)) ** 2
            dy = -70 * (1 - clamp01(p)) ** 2
            if ln["wave"] and t > ln["done"]:
                dy += 5 * math.sin(t * 4.2 - k * 0.55)
            scale *= 1 + 0.05 * bp
            extra = None
            if band_x is not None:
                d = abs(L["cx"] - band_x)
                if d < 110:
                    extra = (1 - d / 110) * 110
            paste_local(frame, L["img"], L["ax"], L["ay"], W / 2 + L["cx"], ln["cy"] + dy,
                        scale=scale, angle=rot, alpha=clamp01(p * 3) * end, extra_rgb=extra)

    for b in bursts:
        dt = t - b["t0"]
        if 0 <= dt < 0.7:
            pr = dt / 0.7
            x = b["x"] + b["vx"] * dt
            y = b["y"] + b["vy"] * dt + 120 * dt * dt
            s = b["s"] * (1 - pr) * (0.6 + 0.4 * math.sin(pr * math.pi))
            paste_local(frame, STAR, STAR.shape[1] / 2, STAR.shape[0] / 2, x, y, scale=s, angle=dt * 200,
                        alpha=(1 - pr) * end)

    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    i += 1
ff.stdin.close()
ff.wait()
print("fatto:", OUT, i, "frame")
