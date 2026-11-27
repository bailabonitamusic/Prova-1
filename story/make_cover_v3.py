"""Video copertina minimalista: solo testo bianco pulito, spaziato, con dissolvenza.

Uso: python3 make_cover_v3.py <video_in.mp4> <video_out.mp4>
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
COND = os.path.join(FD, "BarlowCondensed-Bold.ttf")

WHITE = (255, 255, 255)
LIGHT = (255, 214, 236)


def text(txt, size, col, tracking):
    font = ImageFont.truetype(COND, size)
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    ws = [d0.textlength(c, font=font) for c in txt]
    tw = int(sum(ws) + tracking * (len(txt) - 1))
    asc, desc = font.getmetrics()
    pad = 24
    w, h = tw + 2 * pad, asc + desc + 2 * pad
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = pad
    for c, cw in zip(txt, ws):
        ImageDraw.Draw(sh).text((x, pad + 2), c, font=font, fill=(110, 0, 55, 150))
        ImageDraw.Draw(img).text((x, pad), c, font=font, fill=col + (255,))
        x += cw + tracking
    out = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), img)
    return np.asarray(out).astype(np.float32)


# (immagine, centro_y, ritardo)
els = [
    (text("VENERDÌ 4 DICEMBRE", 62, WHITE, 12), 165, 0.4),
    (text("DJ SET", 34, LIGHT, 16), 1470, 0.9),
    (text("BAILA BONITA  ·  RED MASTER", 64, WHITE, 5), 1535, 1.05),
    (text("21:00 - 00:00", 42, WHITE, 12), 1610, 1.2),
]

# sfumatura leggerissima solo dietro ai testi
yy = np.arange(H, dtype=np.float32)[:, None, None]
shade = np.maximum(np.clip((300 - yy) / 300, 0, 1) ** 2 * 0.25,
                   np.clip((yy - 1300) / 450, 0, 1) ** 1.5 * 0.3)
SHADE_COL = np.array((150, 0, 80), np.float32)


def clamp01(x):
    return min(max(x, 0.0), 1.0)


def ease_out(x):
    return 1 - (1 - clamp01(x)) ** 3


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
    frame = frame * (1 - shade) + SHADE_COL * shade
    for im, cy, dl in els:
        p = ease_out((t - dl) / 0.8)
        if p <= 0:
            continue
        h0, w0 = im.shape[:2]
        x0 = int(W / 2 - w0 / 2)
        y0 = int(cy - h0 / 2 + 18 * (1 - p))
        a = im[..., 3:4] / 255 * p * end
        frame[y0:y0 + h0, x0:x0 + w0] = frame[y0:y0 + h0, x0:x0 + w0] * (1 - a) + im[..., :3] * a
    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    i += 1

ff.stdin.close()
ff.wait()
print("fatto:", OUT, i, "frame")
