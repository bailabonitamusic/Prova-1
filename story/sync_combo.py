"""Unisce due balli (parte 1: giro + mano alzata, parte 2: ondeggiamento) in un video unico,
omogeneo e sincronizzato sui battiti della canzone.

- stessa risoluzione di partenza (480p) e stessa nitidezza per tutte e due le parti
- colori della parte 2 allineati alla parte 1 (media/deviazione in spazio LAB)
- sfondo della parte 2 allineato alla parte 1; le pose delle due parti sono diverse, quindi
  il passaggio e' uno stacco voluto sul battito forte: zoom rapido + lampo leggero
- ogni colpo di fianco cade a ritmo

Uso: python3 sync_combo.py <giro_96fps.mp4> <ondeggio_96fps.mp4> <audio.m4a> <out.mp4> <periodo_battito_s>
"""
import subprocess
import sys

import cv2
import numpy as np

A_SRC, B_SRC, AUDIO, OUT, P = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
FPS_OUT, DUR, OW, OH = 30, 10.0, 1080, 1920
BW, BH = 480, 854  # risoluzione comune di lavoro
MORPH = 0.22


def load(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(cv2.resize(f, (BW, BH), interpolation=cv2.INTER_AREA))
    return np.stack(fr), fps


A, afps = load(A_SRC)
B, bfps = load(B_SRC)


# --- allineamento colori di B su A (LAB, media e deviazione standard)
def lab_stats(frames):
    s = np.concatenate([cv2.cvtColor(f, cv2.COLOR_BGR2LAB).reshape(-1, 3) for f in frames[::12]]).astype(np.float32)
    return s.mean(0), s.std(0)


ma, sa = lab_stats(A)
mb, sb = lab_stats(B)


def match(f):
    lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab = (lab - mb) / (sb + 1e-6) * sa + ma
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


B = np.stack([match(f) for f in B])
# allineamento geometrico dello sfondo (stimato con ORB + RANSAC sulle due pose iniziali)
M_BA = np.float32([[0.9838, 0.0036, -4.7189], [-0.0036, 0.9838, 0.8175]])
B = np.stack([cv2.warpAffine(f, M_BA, (BW, BH), borderMode=cv2.BORDER_REPLICATE) for f in B])

# --- segmenti: tempi sorgente dei colpi di fianco -> battiti
# parte 1 (giro): colpi a metà battito, 9 battiti
A_HITS = [0.27, 0.85, 1.40, 1.94, 2.56, 3.27, 3.65, 4.23, 4.81]
segA = (A, afps, np.array([0.0] + A_HITS + [5.0]),
        np.array([0.0] + [(k + 0.5) * P for k in range(9)] + [9 * P]))
# parte 2 (ondeggiamento): colpi sui battiti, 8 battiti
B_PTS = [0.20, 0.77, 1.35, 2.02, 2.52, 3.15, 3.60, 4.06, 4.40]
segB = (B, bfps, np.array(B_PTS), np.arange(9) * P)
SEGS = [segA, segB]
starts = [0.0, 9 * P]
ends = [9 * P, 17 * P]


def frame_of(seg, tau):
    fr, fps, sp, dp = seg
    st = np.interp(tau, dp, sp)
    return fr[min(max(int(round(st * fps)), 0), len(fr) - 1)]


def morph(a_img, b_img, a):
    ga = cv2.cvtColor(a_img, cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(b_img, cv2.COLOR_BGR2GRAY)
    f_ab = cv2.calcOpticalFlowFarneback(ga, gb, None, 0.5, 4, 25, 3, 7, 1.5, 0)
    f_ba = cv2.calcOpticalFlowFarneback(gb, ga, None, 0.5, 4, 25, 3, 7, 1.5, 0)
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
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
    k = 0 if t < ends[0] else 1
    tau = min(t - starts[k], ends[k] - starts[k])
    img = frame_of(SEGS[k], tau)
    # stacco sul battito forte: zoom che entra prima del taglio ed esce dopo, piu' un lampo
    dtc = t - ends[0]
    zoom, flash = 1.0, 0.0
    if -0.12 < dtc < 0:
        q = (dtc + 0.12) / 0.12
        zoom, flash = 1 + 0.10 * q * q, 0.35 * q * q
    elif 0 <= dtc < 0.25:
        q = 1 - dtc / 0.25
        zoom, flash = 1 + 0.10 * q ** 3, 0.35 * q ** 2
    if zoom != 1.0:
        Mz = cv2.getRotationMatrix2D((BW / 2, BH * 0.45), 0, zoom)
        img = cv2.warpAffine(img, Mz, (BW, BH), borderMode=cv2.BORDER_REPLICATE)
    big = cv2.resize(img, (OW, OH), interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(big, (0, 0), 2.0)
    big = cv2.addWeighted(big, 1.35, blur, -0.35, 0)
    if flash > 0:
        big = cv2.addWeighted(big, 1 - flash, np.full_like(big, 255), flash, 0)
    ff.stdin.write(big.tobytes())
ff.stdin.close()
ff.wait()
print("fatto:", OUT, "parte1", round(ends[0], 3), "s, totale", round(ends[1], 3), "s")
