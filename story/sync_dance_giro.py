"""Sincronizza il ballo con giro e mano alzata sui battiti della canzone.

Ogni colpo di fianco (misurato col flusso ottico) cade a metà tra due battiti in modo regolare;
il giro dura 9 battiti e si ripete. Alla giunzione l'ultima posa si trasforma nella prima
con un morphing a flusso ottico, così non si vede il taglio.

Uso: python3 sync_dance_giro.py <ballo_96fps.mp4> <audio.m4a> <out.mp4> <periodo_battito_s>
"""
import subprocess
import sys

import cv2
import numpy as np

SRC, AUDIO, OUT, P = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
FPS_OUT, DUR, OW, OH = 30, 10.0, 1080, 1920
HITS = [0.27, 0.85, 1.40, 1.94, 2.56, 3.27, 3.65, 4.23, 4.81]
SRC_END = 5.0
src_pts = np.array([0.0] + HITS + [SRC_END])
dst_pts = np.array([0.0] + [(k + 0.5) * P for k in range(len(HITS))] + [9 * P])
LOOP = 9 * P
MORPH = 0.2  # secondi finali del giro dedicati al morphing verso la prima posa

cap = cv2.VideoCapture(SRC)
sfps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
frames = np.stack(frames)
h, w = frames.shape[1:3]
first = frames[0]


def frame_at(src_t):
    return frames[min(max(int(round(src_t * sfps)), 0), len(frames) - 1)]


def morph(a_img, b_img, a):
    ga = cv2.cvtColor(a_img, cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(b_img, cv2.COLOR_BGR2GRAY)
    f_ab = cv2.calcOpticalFlowFarneback(ga, gb, None, 0.5, 4, 25, 3, 7, 1.5, 0)
    f_ba = cv2.calcOpticalFlowFarneback(gb, ga, None, 0.5, 4, 25, 3, 7, 1.5, 0)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wa = cv2.remap(a_img, xx - f_ab[..., 0] * a, yy - f_ab[..., 1] * a, cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REPLICATE)
    wb = cv2.remap(b_img, xx - f_ba[..., 0] * (1 - a), yy - f_ba[..., 1] * (1 - a), cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REPLICATE)
    return (wa.astype(np.float32) * (1 - a) + wb.astype(np.float32) * a).astype(np.uint8)


ff = subprocess.Popen([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}", "-r", str(FPS_OUT), "-i", "-",
    "-i", AUDIO, "-map", "0:v", "-map", "1:a",
    "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "-shortest", "-movflags", "+faststart", OUT,
], stdin=subprocess.PIPE)

for i in range(int(DUR * FPS_OUT)):
    t = i / FPS_OUT
    tau = t % LOOP
    img = frame_at(np.interp(tau, dst_pts, src_pts))
    if tau > LOOP - MORPH:
        a = (tau - (LOOP - MORPH)) / MORPH
        a = a * a * (3 - 2 * a)
        img = morph(img, first, a)
    big = cv2.resize(img, (OW, OH), interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(big, (0, 0), 2.0)
    big = cv2.addWeighted(big, 1.35, blur, -0.35, 0)  # leggera nitidezza dopo l'ingrandimento
    ff.stdin.write(big.tobytes())
ff.stdin.close()
ff.wait()
print("fatto:", OUT, "giro", round(LOOP, 3), "s")
