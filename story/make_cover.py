"""Aggiunge le info dell'evento al video del ballo (video copertina 1080x1920).

Uso: python3 make_cover.py <video_in.mp4> <video_out.mp4>
"""
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 30
import os
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
SCRIPT = os.path.join(FD, "Pacifico-Regular.ttf")   # corsivo tondo come il logo Baila Bonita
ROUND = os.path.join(FD, "Fredoka-Variable.ttf")    # bastone arrotondato


def load(path, size):
    f = ImageFont.truetype(path, size)
    if path == ROUND:
        f.set_variation_by_name("Bold")
    return f

PINK = (255, 46, 160)
HOT = (255, 20, 147)
WHITE = (255, 255, 255)
RED = (255, 40, 70)
DARK = (22, 14, 18)   # nero delle magliette
DEEP = (200, 0, 110)  # magenta per le sfumature


def big_text(txt, size, fill, stroke, glow, path=SCRIPT):
    font = load(path, size)
    pad = 60
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = d0.textbbox((0, 0), txt, font=font, stroke_width=7)
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # ombra/glow
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((pad - bb[0] + 6, pad - bb[1] + 8), txt, font=font,
                           fill=glow + (230,), stroke_width=10, stroke_fill=glow + (230,))
    img = Image.alpha_composite(img, g.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(img).text((pad - bb[0] + 4, pad - bb[1] + 6), txt, font=font,
                             fill=DEEP + (255,), stroke_width=7, stroke_fill=DEEP + (255,))
    ImageDraw.Draw(img).text((pad - bb[0], pad - bb[1]), txt, font=font, fill=fill + (255,),
                             stroke_width=7, stroke_fill=stroke + (255,))
    return img


def pill(txt, size, fg, bg, border=None):
    font = load(ROUND, size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = d0.textbbox((0, 0), txt, font=font)
    px, py, pad = int(size * 0.7), int(size * 0.32), 30
    w = bb[2] - bb[0] + 2 * px + 2 * pad
    h = bb[3] - bb[1] + 2 * py + 2 * pad
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 6, w - pad, h - pad + 6], radius=h,
                                         fill=(0, 0, 0, 140))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, w - pad, h - pad], radius=h, fill=bg + (255,),
                        outline=(border + (255,)) if border else None, width=5 if border else 0)
    d.text((pad + px - bb[0], pad + py - bb[1]), txt, font=font, fill=fg + (255,))
    return img


# elementi: (immagine, centro_y, ritardo ingresso)
els = [
    (big_text("Venerdì", 92, WHITE, HOT, WHITE), 150, 0.25),
    (big_text("4 DICEMBRE", 120, WHITE, HOT, HOT, ROUND), 285, 0.40),
    (pill("DJ SET", 52, PINK, DARK, PINK), 1325, 0.70),
    (big_text("Baila Bonita", 124, WHITE, HOT, WHITE), 1440, 0.85),
    (big_text("Red Master", 124, WHITE, RED, WHITE), 1580, 1.00),
    (pill("21:00 - 00:00", 58, HOT, WHITE, HOT), 1715, 1.15),
]
els = [(np.asarray(im).astype(np.float32), cy, dl) for im, cy, dl in els]

# sfumatura scura in basso per leggibilità
gy = np.arange(H, dtype=np.float32)
grad = np.clip((gy - 1180) / 420, 0, 1) ** 1.3 * 0.6
grad_top = np.clip((380 - gy) / 380, 0, 1) ** 1.5 * 0.4
shade = np.maximum(grad, grad_top)[:, None, None]
shade_col = np.array(DEEP, np.float32)


def ease_back(x):
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


cap = cv2.VideoCapture(SRC)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
src_fps = cap.get(cv2.CAP_PROP_FPS) or FPS
dur = n / src_fps

ff = subprocess.Popen([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(src_fps), "-i", "-",
    "-i", SRC, "-map", "0:v", "-map", "1:a?",
    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "-shortest", "-movflags", "+faststart", OUT,
], stdin=subprocess.PIPE)

i = 0
while True:
    ok, fr = cap.read()
    if not ok:
        break
    t = i / src_fps
    fr = cv2.cvtColor(cv2.resize(fr, (W, H), interpolation=cv2.INTER_LANCZOS4), cv2.COLOR_BGR2RGB)
    frame = fr.astype(np.float32)
    frame = frame * (1 - shade) + shade_col * shade
    end_fade = 1 - np.clip((t - (dur - 0.4)) / 0.4, 0, 1)
    breathe = 1 + 0.015 * np.sin(2 * np.pi * t / 1.7)
    for k, (im, cy, dl) in enumerate(els):
        p = (t - dl) / 0.45
        if p <= 0:
            continue
        a = min(1.0, p * 1.6) * end_fade
        s = (0.6 + 0.4 * ease_back(p)) * (breathe if k in (1, 3, 4) else 1)
        h0, w0 = im.shape[:2]
        M = np.float32([[s, 0, W / 2 - s * w0 / 2], [0, s, cy - s * h0 / 2]])
        lay = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        al = lay[..., 3:4] / 255 * a
        frame = frame * (1 - al) + lay[..., :3] * al
    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    i += 1

ff.stdin.close()
ff.wait()
print("fatto:", OUT, i, "frame")
