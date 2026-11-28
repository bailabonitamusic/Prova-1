"""Rimappa il tempo del ballo così ogni colpo di fianco cade su un battito della canzone.

Uso: python3 sync_dance.py <ballo_96fps.mp4> <audio.m4a> <out.mp4> <periodo_battito_s>
I colpi di fianco nel clip Canva originale sono stati misurati con il flusso ottico.
"""
import subprocess
import sys

import cv2
import numpy as np

SRC, AUDIO, OUT, P = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
FPS_OUT, DUR = 30, 10.0

# tempo nel clip sorgente -> battito di destinazione (un giro = 8 battiti = 2 battute)
src_pts = np.array([0.20, 0.77, 1.35, 2.02, 2.52, 3.15, 3.60, 4.06, 4.40])
dst_pts = np.arange(len(src_pts)) * P
LOOP = dst_pts[-1]

cap = cv2.VideoCapture(SRC)
sfps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
frames = np.stack(frames)
H, W = frames.shape[1:3]

ff = subprocess.Popen([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS_OUT), "-i", "-",
    "-i", AUDIO, "-map", "0:v", "-map", "1:a",
    "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "-shortest", "-movflags", "+faststart", OUT,
], stdin=subprocess.PIPE)

# avanti e indietro (ping-pong): nessun taglio, il movimento resta continuo.
# Le inversioni cadono sul battito 8 e 16, come un normale cambio di direzione dei fianchi.
for i in range(int(DUR * FPS_OUT)):
    t = i / FPS_OUT
    tau = t % (2 * LOOP)
    if tau > LOOP:
        tau = 2 * LOOP - tau
    src_t = np.interp(tau, dst_pts, src_pts)
    fi = min(int(round(src_t * sfps)), len(frames) - 1)
    out = frames[fi].astype(np.float32)
    ff.stdin.write(out.astype(np.uint8).tobytes())
ff.stdin.close()
ff.wait()
print("fatto:", OUT, "giro", round(LOOP, 3), "s")
