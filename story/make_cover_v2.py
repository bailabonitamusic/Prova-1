"""Video copertina in stile flyer club (neon, data impilata, adesivi a pennarello, frecce).

Uso: python3 make_cover_v2.py <video_in.mp4> <video_out.mp4>
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
SLAB = os.path.join(FD, "AlfaSlabOne-Regular.ttf")
COND = os.path.join(FD, "BarlowCondensed-ExtraBold.ttf")
MARKER = os.path.join(FD, "PermanentMarker-Regular.ttf")

WHITE = (255, 255, 255)
HOT = (255, 20, 147)
PINK = (255, 105, 190)
LIGHT = (255, 200, 230)
MINT = (130, 245, 220)
BLACK = (22, 14, 18)


def F(path, size):
    return ImageFont.truetype(path, size)


def to_np(img):
    return np.asarray(img).astype(np.float32)


# ------------------------------------------------------------- titolo al neon
def neon_title(txt, size):
    font = F(SLAB, size)
    pad = 70
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), txt, font=font, stroke_width=8)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    org = (pad - bb[0], pad - bb[1])
    outer = Image.new("L", (w, h), 0)
    ImageDraw.Draw(outer).text(org, txt, font=font, fill=255, stroke_width=8, stroke_fill=255)
    fill = Image.new("L", (w, h), 0)
    ImageDraw.Draw(fill).text(org, txt, font=font, fill=255)
    inner = fill.filter(ImageFilter.MinFilter(7))
    ring = np.clip(to_np(outer) - to_np(inner), 0, 255) / 255
    inner_a = to_np(inner) / 255
    glow1 = to_np(Image.fromarray((ring * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))) / 255
    glow2 = to_np(Image.fromarray((ring * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(26))) / 255
    rgb = np.zeros((h, w, 3), np.float32)
    a = np.zeros((h, w), np.float32)

    def over(col, al):
        nonlocal rgb, a
        al = np.clip(al, 0, 1)
        rgb = rgb * (1 - al[..., None]) + np.array(col, np.float32) * al[..., None]
        a = a + al * (1 - a)

    over((200, 0, 110), inner_a * 0.45)          # interno traslucido
    over(HOT, glow2 * 1.6)                        # alone largo
    over(PINK, glow1 * 1.4)                       # alone stretto
    over((255, 235, 248), ring)                   # tubo luminoso
    return np.dstack([rgb, a * 255]), np.dstack([rgb, ring * 255])  # (completo, solo tubo)


# ------------------------------------------------------------- testo condensato
def cond_text(txt, size, col, shadow=True, tracking=0):
    font = F(COND, size)
    pad = 30
    chars = list(txt)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    widths = [d0.textlength(c, font=font) for c in chars]
    tw = int(sum(widths) + tracking * (len(chars) - 1))
    asc, desc = font.getmetrics()
    w, h = tw + 2 * pad, asc + desc + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x = pad
        for c, cw in zip(chars, widths):
            ImageDraw.Draw(sh).text((x + 4, pad + 5), c, font=font, fill=(120, 0, 60, 200))
            x += cw + tracking
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(5)))
    x = pad
    d = ImageDraw.Draw(img)
    for c, cw in zip(chars, widths):
        d.text((x, pad), c, font=font, fill=col + (255,))
        x += cw + tracking
    return to_np(img)


# ------------------------------------------------------------- adesivo a pennarello
def sticker(lines, size, fg, bg, angle):
    font = F(MARKER, size)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    boxes = [d0.textbbox((0, 0), l, font=font) for l in lines]
    lh = int(size * 1.05)
    tw = max(b[2] - b[0] for b in boxes)
    px, py, pad = int(size * 0.45), int(size * 0.28), 50
    w = tw + 2 * px + 2 * pad
    h = lh * len(lines) + 2 * py + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad + 6, pad + 10, w - pad + 6, h - pad + 10], fill=(90, 0, 45, 150))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.rectangle([pad, pad, w - pad, h - pad], fill=bg + (255,))
    for k, (l, b) in enumerate(zip(lines, boxes)):
        lw = b[2] - b[0]
        d.text((pad + px + (tw - lw) / 2 - b[0], pad + py + k * lh - b[1] + (lh - size) * 0.3), l,
               font=font, fill=fg + (255,))
    img = img.rotate(angle, resample=Image.BICUBIC, expand=True)
    return to_np(img)


def chevron(col, size=70, thick=16):
    w, h = size * 2 + 40, size + 40
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(20, 20), (w / 2, 20 + size * 0.75), (w - 20, 20)]
    d.line(pts, fill=col + (255,), width=thick, joint="curve")
    for p in (pts[0], pts[2]):
        d.ellipse([p[0] - thick / 2, p[1] - thick / 2, p[0] + thick / 2, p[1] + thick / 2], fill=col + (255,))
    return to_np(img)


# ------------------------------------------------------------- elementi
title_full, title_tube = neon_title("BAILA BONITA", 116)
date_lines = [
    (cond_text("VENERDÌ", 74, LIGHT), 380),
    (cond_text("04.12", 168, WHITE), 482),
    (cond_text("DICEMBRE", 66, MINT), 590),
]
time_big = cond_text("21:00 - 00:00", 132, WHITE)
st_dj = sticker(["DJ SET"], 76, HOT, MINT, 6)
st_names = sticker(["Baila Bonita", "+ Red Master"], 82, WHITE, HOT, -5)
chev = chevron(WHITE)

# texture a mezzitoni (puntini)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dots = ((np.sin(xx * 0.9) * np.sin(yy * 0.9)) > 0.75).astype(np.float32)
halftone = (dots * 0.06)[..., None]
# leggero scurimento in alto e in basso per staccare i testi
shade = np.maximum(np.clip((260 - yy[:, :1]) / 260, 0, 1) ** 1.5 * 0.35,
                   np.clip((yy[:, :1] - 1250) / 500, 0, 1) ** 1.4 * 0.45)[..., None][:, :, 0:1]
SHADE_COL = np.array((170, 0, 95), np.float32)


def paste(frame, im, cx, cy, alpha=1.0, scale=1.0, angle=0.0):
    h0, w0 = im.shape[:2]
    M = cv2.getRotationMatrix2D((w0 / 2, h0 / 2), angle, scale)
    M[0, 2] += cx - w0 / 2
    M[1, 2] += cy - h0 / 2
    lay = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = lay[..., 3:4] / 255 * alpha
    return frame * (1 - a) + lay[..., :3] * a


def clamp01(x):
    return min(max(x, 0.0), 1.0)


def ease_back(x):
    x = clamp01(x)
    return 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2


def neon_on(t):
    """accensione tremolante del neon"""
    if t < 0.15:
        return 0.0
    seq = [(0.15, 0.25, 1), (0.25, 0.32, 0), (0.32, 0.38, 1), (0.38, 0.5, 0.15), (0.5, 0.56, 1),
           (0.56, 0.62, 0.3)]
    for a, b, v in seq:
        if a <= t < b:
            return v
    return 1.0


cap = cv2.VideoCapture(SRC)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
dur = n / fps

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
    frame = frame * (1 - shade) + SHADE_COL * shade
    frame = frame * (1 - halftone) + 255 * halftone

    # neon: accensione, poi leggero tremolio/pulsazione
    on = neon_on(t)
    flick = 0.9 + 0.1 * math.sin(t * 7.3) * math.sin(t * 3.1)
    if on > 0:
        frame = paste(frame, title_full, W / 2, 205, alpha=on * flick * end)

    # data impilata: entra da sinistra
    for k, (im, cy) in enumerate(date_lines):
        p = clamp01((t - 0.6 - 0.15 * k) / 0.4)
        if p > 0:
            x = 572 - 120 * (1 - ease_back(p))
            frame = paste(frame, im, x, cy, alpha=clamp01(p * 2) * end)

    # adesivi "schiaffati"
    for im, cx, cy, dl in ((st_dj, 300, 1170, 1.1), (st_names, 575, 1335, 1.3)):
        p = clamp01((t - dl) / 0.35)
        if p > 0:
            s = 1.35 - 0.35 * ease_back(p)
            wob = 1 + 0.02 * math.sin(t * 2.2 + cx)
            frame = paste(frame, im, cx, cy, alpha=clamp01(p * 3) * end, scale=s * wob)

    # frecce che lampeggiano in sequenza verso il basso
    if t > 1.6:
        for k in range(3):
            ph = (t * 1.6 - k * 0.25) % 1.0
            a = 0.35 + 0.65 * max(0.0, math.cos(ph * 2 * math.pi)) ** 2
            frame = paste(frame, chev, W / 2, 1478 + k * 42, alpha=a * end * clamp01((t - 1.6) / 0.3))

    # orario in basso, dove puntano le frecce
    p = clamp01((t - 1.8) / 0.4)
    if p > 0:
        frame = paste(frame, time_big, W / 2, 1655 - 30 * (1 - ease_back(p)), alpha=clamp01(p * 2) * end)

    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    i += 1

ff.stdin.close()
ff.wait()
print("fatto:", OUT, i, "frame")
