"""Estrae fotogrammi nitidi dai video e li ingrandisce con super-risoluzione EDSR (1440x2560).

Uso: python3 upscale_frames.py <cartella_modelli>
"""
import sys
import time

import cv2
import numpy as np

cv2.setNumThreads(4)

MD = sys.argv[1]
JOBS = [  # (video, fotogramma, fattore, nome)
    ("storia_flora_ballo_canva.mp4", 0, 2, "hd_posa_cartello"),
    ("storia_flora_ballo_canva.mp4", 60, 2, "hd_ondeggio"),
    ("storia_flora_ballo_canva.mp4", 117, 2, "hd_posa_finale"),
    ("ballo_giro_canva_480p.mp4", 42, 3, "hd_giro"),
    ("ballo_giro_canva_480p.mp4", 92, 3, "hd_mano_alzata"),
]
srs = {}
for k in (2, 3):
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(f"{MD}/EDSR_x{k}.pb")
    sr.setModel("edsr", k)
    srs[k] = sr
def upsample_tiled(sr, img, k, tile=200, ov=16):
    """Applica il modello a riquadri sovrapposti (piu' veloce e meno memoria)."""
    h, w = img.shape[:2]
    out = np.zeros((h * k, w * k, 3), np.float32)
    wsum = np.zeros((h * k, w * k, 1), np.float32)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            y0, x0 = max(y - ov, 0), max(x - ov, 0)
            y1, x1 = min(y + tile + ov, h), min(x + tile + ov, w)
            up = sr.upsample(np.ascontiguousarray(img[y0:y1, x0:x1])).astype(np.float32)
            th, tw = up.shape[:2]
            wy = np.minimum(np.arange(th) + 1, np.arange(th)[::-1] + 1).clip(max=ov * k)[:, None]
            wx = np.minimum(np.arange(tw) + 1, np.arange(tw)[::-1] + 1).clip(max=ov * k)[None, :]
            wgt = (wy * wx).astype(np.float32)[..., None]
            out[y0 * k:y1 * k, x0 * k:x1 * k] += up * wgt
            wsum[y0 * k:y1 * k, x0 * k:x1 * k] += wgt
    return np.clip(out / wsum, 0, 255).astype(np.uint8)


for vid, idx, k, name in JOBS:
    cap = cv2.VideoCapture(vid)
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = cap.read()
    t0 = time.time()
    up = upsample_tiled(srs[k], f, k)
    up = cv2.resize(up, (1440, 2560), interpolation=cv2.INTER_AREA if up.shape[1] > 1440 else cv2.INTER_CUBIC)
    cv2.imwrite(f"immagini/{name}.png", up, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    print(name, f.shape[1], "x", f.shape[0], "->", up.shape[1], "x", up.shape[0], f"{time.time() - t0:.0f}s", flush=True)
