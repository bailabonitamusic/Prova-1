"""Stili di testo per la copertina (stile A-D). Ognuno ritorna una lista di (RGBA np, centro_y)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
P = lambda n: os.path.join(FD, n)
WHITE, HOT, BLACK, LIGHT = (255, 255, 255), (255, 20, 147), (20, 12, 16), (255, 190, 225)


def font(name, size, var=None):
    f = ImageFont.truetype(P(name), size)
    if var:
        f.set_variation_by_name(var)
    return f


def styled(txt, f, fill, stroke=0, stroke_col=None, shadow=(0, 0, 0, 170), sh_off=(6, 9), box=None,
           box_pad=(34, 16), radius=999, track=0):
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    ws = [d0.textlength(c, font=f) for c in txt]
    tw = int(sum(ws) + track * (len(txt) - 1)) + 2 * stroke
    asc, desc = f.getmetrics()
    th = asc + desc + 2 * stroke
    bx, by = box_pad if box else (0, 0)
    pad = 40
    w, h = tw + 2 * bx + 2 * pad, th + 2 * by + 2 * pad
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ds, dt = ImageDraw.Draw(sh), ImageDraw.Draw(top)
    if box:
        r = min(radius, (h - 2 * pad) // 2)
        ds.rounded_rectangle([pad + sh_off[0], pad + sh_off[1], w - pad + sh_off[0], h - pad + sh_off[1]], r, fill=shadow)
        dt.rounded_rectangle([pad, pad, w - pad, h - pad], r, fill=box + (255,))
    x = pad + bx + stroke
    y = pad + by + stroke
    for c, cw in zip(txt, ws):
        if not box and shadow:
            ds.text((x + sh_off[0], y + sh_off[1]), c, font=f, fill=shadow, stroke_width=stroke, stroke_fill=shadow)
        dt.text((x, y), c, font=f, fill=fill + (255,), stroke_width=stroke,
                stroke_fill=(stroke_col + (255,)) if stroke else None)
        x += cw + track
    out = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(7)))
    out = Image.alpha_composite(out, top)
    return np.asarray(out).astype(np.float32)


def style_A():  # retro come il logo Baila Bonita
    S = "Shrikhand-Regular.ttf"
    return [
        (styled("Venerdì 4 Dicembre", font(S, 92), WHITE, 9, HOT), 190),
        (styled("DJ SET", font(S, 72), HOT, 6, WHITE), 1395),
        (styled("Baila Bonita", font(S, 128), WHITE, 11, HOT), 1510),
        (styled("Red Master", font(S, 128), WHITE, 11, HOT), 1650),
        (styled("21:00 - 00:00", font(S, 74), WHITE, 9, HOT), 1785),
    ]


def style_B():  # riquadri neri come le magliette
    R = "Fredoka-Variable.ttf"
    return [
        (styled("VENERDÌ 4 DICEMBRE", font(R, 76, "Bold"), WHITE, box=BLACK), 185),
        (styled("DJ SET", font(R, 58, "Bold"), BLACK, box=HOT, box_pad=(30, 10)), 1390),
        (styled("BAILA BONITA", font(R, 104, "Bold"), HOT, box=BLACK), 1505),
        (styled("RED MASTER", font(R, 104, "Bold"), HOT, box=BLACK), 1650),
        (styled("21:00 - 00:00", font(R, 68, "Bold"), WHITE, box=BLACK), 1785),
    ]


def style_C():  # pennellata + riquadri
    K, R = "KaushanScript-Regular.ttf", "Fredoka-Variable.ttf"
    return [
        (styled("VENERDÌ 4 DICEMBRE", font(R, 72, "Bold"), WHITE, box=HOT), 185),
        (styled("DJ SET", font(R, 56, "Bold"), WHITE, box=BLACK, box_pad=(30, 10)), 1385),
        (styled("Baila Bonita", font(K, 140), WHITE, 8, BLACK), 1505),
        (styled("Red Master", font(K, 140), WHITE, 8, BLACK), 1650),
        (styled("21:00 - 00:00", font(R, 68, "Bold"), WHITE, box=HOT), 1790),
    ]


def style_D():  # elegante corsivo con contorno
    PF = "PlayfairDisplay-Italic-Variable.ttf"
    return [
        (styled("Venerdì 4 Dicembre", font(PF, 92, "Black Italic"), WHITE, 6, HOT), 185),
        (styled("DJ SET", font(PF, 64, "Black Italic"), HOT, 6, WHITE), 1390),
        (styled("Baila Bonita", font(PF, 132, "Black Italic"), WHITE, 8, HOT), 1505),
        (styled("Red Master", font(PF, 132, "Black Italic"), WHITE, 8, HOT), 1650),
        (styled("21:00 - 00:00", font(PF, 76, "Black Italic"), WHITE, 6, HOT), 1785),
    ]


STYLES = {"A": style_A, "B": style_B, "C": style_C, "D": style_D}


def compose(frame, els, alphas=None):
    H, W = frame.shape[:2]
    for k, (im, cy) in enumerate(els):
        a_mul = 1.0 if alphas is None else alphas[k]
        if a_mul <= 0:
            continue
        h0, w0 = im.shape[:2]
        x0, y0 = int(W / 2 - w0 / 2), int(cy - h0 / 2)
        xs, ys = max(0, -x0), max(0, -y0)
        xe, ye = min(w0, W - x0), min(h0, H - y0)
        sub = im[ys:ye, xs:xe]
        a = sub[..., 3:4] / 255 * a_mul
        region = frame[y0 + ys:y0 + ye, x0 + xs:x0 + xe]
        frame[y0 + ys:y0 + ye, x0 + xs:x0 + xe] = region * (1 - a) + sub[..., :3] * a
    return frame
