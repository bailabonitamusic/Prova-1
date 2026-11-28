"""Video copertina con lo stile A (retro come il logo Baila Bonita).

Uso: python3 make_cover_A.py <video_in.mp4> <video_out.mp4>
"""
import subprocess
import sys

import cv2
import numpy as np

import cover_styles as cs

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 1080, 1920
els = cs.style_A()
delays = [0.3, 0.8, 0.95, 1.1, 1.3]


def clamp01(x):
    return min(max(x, 0.0), 1.0)


def ease_back(x):
    x = clamp01(x)
    return 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2


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
    for (im, cy), dl in zip(els, delays):
        p = clamp01((t - dl) / 0.45)
        if p <= 0:
            continue
        s = 0.7 + 0.3 * ease_back(p)
        h0, w0 = im.shape[:2]
        M = np.float32([[s, 0, W / 2 - s * w0 / 2], [0, s, cy - s * h0 / 2]])
        lay = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        a = lay[..., 3:4] / 255 * clamp01(p * 2) * end
        frame = frame * (1 - a) + lay[..., :3] * a
    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    i += 1
ff.stdin.close()
ff.wait()
print("fatto:", OUT, i, "frame")
