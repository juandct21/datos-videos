import numpy as np, math, subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS = 1080, 1920, 30
FD = '/usr/share/fonts/opentype/inter/'
FB, FXB, FSB, FIT = 'InterDisplay-Black.otf', 'InterDisplay-ExtraBold.otf', 'InterDisplay-SemiBold.otf', 'InterDisplay-SemiBoldItalic.otf'
if not os.path.exists(FD + FIT):
    FIT = FSB
YEL = (255, 210, 63, 255); WHITE = (255, 255, 255, 255); MUTED = (170, 192, 220, 255)
CYAN = (111, 211, 255, 255); NAVY = (10, 22, 48, 255); CORAL = (255, 128, 104, 255)
DUR = [4.0, 7.1, 12.1, 14.0, 16.9, 8.6]
START = [sum(DUR[:i]) for i in range(len(DUR))]
TOTAL = sum(DUR)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, s, d): return clamp((t - s) / d)
def eoc(x): x = clamp(x); return 1 - (1 - x) ** 3
def eob(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

@lru_cache(None)
def font(name, size): return ImageFont.truetype(FD + name, size)

def fit(text, name, size, maxw=940):
    while size > 20:
        l, t, r, b = font(name, size).getbbox(text)
        if r - l <= maxw: return size
        size -= 4
    return size

@lru_cache(None)
def timg(text, name, size, fill=WHITE, shadow=True):
    f = font(name, size)
    l, t, r, b = f.getbbox(text)
    pad = 24
    w, h = r - l + 2 * pad, b - t + 2 * pad
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=fill)
    if shadow:
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l, pad - t + 5), text, font=f, fill=(0, 0, 0, 170))
        sh = sh.filter(ImageFilter.GaussianBlur(7))
        sh.alpha_composite(im)
        im = sh
    return im

def with_alpha(img, a):
    if a >= 0.999: return img
    arr = np.array(img)
    arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8)
    return Image.fromarray(arr)

def comp(canvas, img, x, y):
    x, y = int(round(x)), int(round(y))
    sx, sy = max(0, -x), max(0, -y)
    if sx >= img.width or sy >= img.height: return
    if sx or sy: img = img.crop((sx, sy, img.width, img.height))
    if x + sx >= canvas.width or y + sy >= canvas.height: return
    canvas.alpha_composite(img, (x + sx, y + sy))

def put(canvas, img, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.003 or scale <= 0.01: return
    if abs(scale - 1) > 0.002:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
    img = with_alpha(img, alpha)
    comp(canvas, img, cx - img.width / 2, cy - img.height / 2)

def pop(canvas, img, cx, cy, t, s, d=0.35, fs=0.75):
    p = prog(t, s, d)
    if p <= 0: return
    put(canvas, img, cx, cy, fs + (1 - fs) * eob(p), clamp(p * 2.5))

def slide(canvas, img, cx, cy, t, s, d=0.5, dy=50):
    p = eoc(prog(t, s, d))
    if p <= 0: return
    put(canvas, img, cx, cy + dy * (1 - p), 1, p)

@lru_cache(None)
def pill(text, name, size, fg=WHITE, bg=(8, 18, 40, 215), padx=34, pady=18, outline=None):
    t = timg(text, name, size, fg, False)
    w, h = t.width - 48 + 2 * padx, t.height - 48 + 2 * pady
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg, outline=outline, width=3 if outline else 0)
    im.alpha_composite(t, (padx - 24, pady - 24))
    return im

# ---------- background ----------
def make_bg():
    y = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([10, 22, 48]), np.array([12, 52, 68])
    base = top + (bot - top) * y[..., None]
    base = np.repeat(base, W, axis=1)
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - 540) / 650) ** 2 + ((yy - 760) / 750) ** 2))[..., None]
    base = base + g * np.array([22, 48, 70])
    a = np.dstack([np.clip(base, 0, 255).astype(np.uint8), np.full((H, W), 255, np.uint8)])
    return Image.fromarray(a, 'RGBA')

# ---------- tepuy illustration ----------
def gradient_fill(w, h, top, bot):
    y = np.linspace(0, 1, h)[:, None, None]
    c = np.array(top) + (np.array(bot) - np.array(top)) * y
    c = np.repeat(c, w, axis=1)
    return np.clip(c, 0, 255).astype(np.uint8)

def make_tepuy(w, h, seed=3, wx=0.56):
    rng = np.random.default_rng(seed)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # distant tepuy
    d.polygon([(0, .34 * h), (.04 * w, .25 * h), (.40 * w, .23 * h), (.46 * w, .30 * h), (.46 * w, .9 * h), (0, .9 * h)], fill=(30, 58, 86, 255))
    d.polygon([(.70 * w, .30 * h), (.74 * w, .22 * h), (w, .21 * h), (w, .9 * h), (.70 * w, .9 * h)], fill=(26, 52, 78, 255))
    top = .13 * h
    left = [(.12 * w + rng.uniform(-14, 14), top + (0.95 * h - top) * (1 - i / 14)) for i in range(15)]
    right = [(.90 * w + rng.uniform(-14, 14), top + (0.95 * h - top) * i / 14) for i in range(15)]
    topedge = [(.12 * w + (.78 * w) * i / 10, top + rng.uniform(-6, 6)) for i in range(11)]
    poly = left + topedge + right
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    body = Image.fromarray(np.dstack([gradient_fill(w, h, (64, 92, 74), (22, 40, 36)), np.array(mask)]), 'RGBA')
    tex = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(tex)
    for _ in range(140):
        x = rng.uniform(.1 * w, .92 * w); y0 = rng.uniform(top, .8 * h); ln = rng.uniform(40, 260)
        td.line([(x, y0), (x + rng.uniform(-6, 6), y0 + ln)], fill=(0, 0, 0, int(rng.uniform(30, 70))), width=int(rng.uniform(2, 6)))
    ta = np.array(tex); ta[..., 3] = np.minimum(ta[..., 3], np.array(mask)); tex = Image.fromarray(ta)
    body.alpha_composite(tex)
    im.alpha_composite(body)
    # vegetation rim
    rim = [(x, y - 2) for x, y in topedge] + [(x, y + .028 * h) for x, y in reversed(topedge)]
    d.polygon(rim, fill=(74, 140, 86, 255))
    # jungle (front)
    for _ in range(int(w / 9)):
        x = rng.uniform(-20, w + 20); y = rng.uniform(.82 * h, h + 20); r = rng.uniform(26, 58)
        col = [(22, 66, 40), (34, 92, 52), (18, 52, 32), (44, 108, 60)][rng.integers(0, 4)]
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,))
    geo = dict(x=wx * w, y0=top + 4, y1=.84 * h)
    return im, geo

PART = {}
def particles(seed, n=120):
    if seed not in PART:
        r = np.random.default_rng(seed)
        PART[seed] = dict(dx=np.clip(r.normal(0, .22, n), -.5, .5), ph=r.uniform(0, 1, n), ln=r.uniform(.04, .12, n),
                          wd=r.integers(2, 6, n), al=r.integers(120, 245, n), sp=r.uniform(.8, 1.25, n))
    return PART[seed]

@lru_cache(None)
def mist_sprite(w):
    im = Image.new('RGBA', (int(w * 3.2), 220), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((im.width * .15, 60, im.width * .85, 160), fill=(235, 245, 255, 210))
    return im.filter(ImageFilter.GaussianBlur(26))

def water(canvas, t, x, y0, y1, w0, w1, seed=1, speed=520, mist=True, n=120, alpha=1.0):
    p = particles(seed, n)
    bx0 = int(x - w1); by0 = int(y0)
    lay = Image.new('RGBA', (int(2 * w1) + 2, int(y1 - y0) + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    L = y1 - y0
    d.polygon([(x - w0 / 2 - bx0, 0), (x + w0 / 2 - bx0, 0), (x + w1 / 2 - bx0, L), (x - w1 / 2 - bx0, L)], fill=(215, 236, 255, 85))
    f = (p['ph'] + t * speed * p['sp'] / L) % 1.0
    for i in range(n):
        fr = f[i]; yy = L * fr; hw = (w0 + (w1 - w0) * fr) / 2
        xx = x + p['dx'][i] * 2 * hw - bx0
        ye = min(L, yy + p['ln'][i] * L)
        d.line([(xx, yy), (xx, ye)], fill=(240, 248, 255, int(p['al'][i])), width=int(p['wd'][i]))
    put(canvas, lay, bx0 + lay.width / 2, by0 + lay.height / 2, 1, alpha)
    if mist:
        m = mist_sprite(int(w1))
        put(canvas, m, x, y1 - 10, 1.0 + 0.05 * math.sin(t * 2.1), alpha * (0.75 + 0.2 * math.sin(t * 1.7)))

def tepuy_at(canvas, spr, geo, t, ox, oy, alpha=1.0, seed=1, speed=520):
    put(canvas, spr, ox + spr.width / 2, oy + spr.height / 2, 1, alpha)
    sc = spr.width / 1000
    water(canvas, t, ox + geo['x'], oy + geo['y0'], oy + geo['y1'], 22 * sc, 120 * sc, seed=seed, speed=speed, alpha=alpha)

# ---------- small icons ----------
def make_flag(w=190, h=126):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h / 3), fill=(255, 204, 0, 255)); d.rectangle((0, h / 3, w, 2 * h / 3), fill=(0, 36, 125, 255)); d.rectangle((0, 2 * h / 3, w, h), fill=(207, 20, 43, 255))
    cx, cy, R = w / 2, h * .70, h * .30
    for k in range(8):
        a = math.radians(180 - (25 + k * (130 / 7)))
        sx, sy = cx + R * math.cos(a), cy - R * math.sin(a)
        pts = []
        for j in range(10):
            rr = 6 if j % 2 == 0 else 2.6
            aa = -math.pi / 2 + j * math.pi / 5
            pts.append((sx + rr * math.cos(aa), sy + rr * math.sin(aa)))
        d.polygon(pts, fill=(255, 255, 255, 255))
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=14, fill=255)
    im.putalpha(Image.fromarray(np.minimum(np.array(im)[..., 3], np.array(m))))
    return im

def make_pin(s=70):
    im = Image.new('RGBA', (s, int(s * 1.35)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, s, s), fill=(255, 92, 92, 255))
    d.polygon([(s * .14, s * .7), (s * .86, s * .7), (s / 2, s * 1.33)], fill=(255, 92, 92, 255))
    d.ellipse((s * .3, s * .3, s * .7, s * .7), fill=(255, 255, 255, 255))
    return im

def make_plane():
    S = 2; w, h = 300 * S, 130 * S
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(30 * S, 40 * S), (60 * S, 62 * S), (40 * S, 70 * S), (14 * S, 70 * S)], fill=(205, 60, 60, 255))  # tail fin
    d.rounded_rectangle((20 * S, 55 * S, 260 * S, 92 * S), radius=18 * S, fill=(232, 236, 242, 255))  # fuselage
    d.ellipse((230 * S, 52 * S, 280 * S, 95 * S), fill=(232, 236, 242, 255))
    d.rectangle((40 * S, 68 * S, 250 * S, 76 * S), fill=(205, 60, 60, 255))  # stripe
    d.polygon([(150 * S, 50 * S), (210 * S, 50 * S), (200 * S, 58 * S), (160 * S, 58 * S)], fill=(120, 190, 235, 255))  # window
    d.rounded_rectangle((95 * S, 40 * S, 215 * S, 50 * S), radius=5 * S, fill=(120, 130, 145, 255))  # wing (high)
    d.line([(150 * S, 92 * S), (140 * S, 112 * S)], fill=(90, 90, 100, 255), width=4 * S)
    d.line([(195 * S, 92 * S), (205 * S, 112 * S)], fill=(90, 90, 100, 255), width=4 * S)
    d.ellipse((128 * S, 104 * S, 152 * S, 128 * S), fill=(40, 40, 48, 255)); d.ellipse((193 * S, 104 * S, 217 * S, 128 * S), fill=(40, 40, 48, 255))
    d.rectangle((280 * S, 60 * S, 286 * S, 88 * S), fill=(60, 60, 70, 255))
    d.ellipse((282 * S, 30 * S, 292 * S, 118 * S), fill=(200, 210, 220, 110))  # propeller blur
    return im.resize((w // S, h // S), Image.LANCZOS)

# ---------- shared assets (built per process) ----------
A = {}
def build():
    A['bg'] = make_bg()
    A['tep1'], A['geo1'] = make_tepuy(1000, 960, seed=3)
    A['tep5'], A['geo5'] = make_tepuy(900, 760, seed=7, wx=.58)
    A['flag'] = make_flag(); A['pin'] = make_pin(); A['plane'] = make_plane()

# ---------- scenes ----------
def s1(c, t):
    tep, g = A['tep1'], A['geo1']
    p = eoc(prog(t, 0.05, 0.7))
    tepuy_at(c, tep, g, t, 40, 880 + 70 * (1 - p), alpha=p, seed=11)
    pop(c, A['flag'], 540, 250, t, 0.0, 0.4)
    lines = [("¿Sabías que", FXB, 92, WHITE, 410), ("la cascada más alta", FXB, 92, WHITE, 515), ("del mundo está en", FXB, 92, WHITE, 620)]
    for i, (tx, fn, sz, col, y) in enumerate(lines):
        pop(c, timg(tx, fn, fit(tx, fn, sz), col), 540, y, t, 0.0 + i * 0.12, 0.35)
    pop(c, timg("VENEZUELA?", FB, fit("VENEZUELA?", FB, 140), YEL), 540, 760, t, 0.45, 0.45, 0.6)

def s2(c, t):
    tep, g = A['tep1'], A['geo1']
    oy = 540 - 18 * eoc(prog(t, 0, 7.1))
    p = eoc(prog(t, 0, 0.6))
    tepuy_at(c, tep, g, t, 40, oy + 50 * (1 - p), alpha=p, seed=12)
    pop(c, timg("Se llama", FSB, 58, MUTED), 540, 270, t, 0.05)
    pop(c, timg("SALTO ÁNGEL", FB, fit("SALTO ÁNGEL", FB, 140), YEL), 540, 380, t, 0.75, 0.45, 0.6)
    # Auyán-tepui callout
    q = eoc(prog(t, 2.75, 0.5))
    if q > 0:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        ax, ay = 300, oy + 0.13 * 960 + 10
        d.line([(ax, ay - 70), (ax, ay - 70 + 60 * q)], fill=(255, 255, 255, 230), width=4)
        d.ellipse((ax - 9, ay - 19, ax + 9, ay - 1), fill=(255, 210, 63, int(255 * q)))
        put(c, lay, W / 2, H / 2, 1, q)
        pop(c, pill("Auyán-tepui", FXB, 46, YEL), ax, ay - 110, t, 2.75, 0.4)
    # location card
    q = prog(t, 4.15, 0.5)
    if q > 0:
        card = Image.new('RGBA', (900, 190), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle((0, 0, 899, 189), radius=36, fill=(8, 18, 40, 225), outline=(255, 255, 255, 60), width=2)
        card.alpha_composite(A['pin'], (50, 48))
        t1 = timg("Parque Nacional Canaima", FXB, fit("Parque Nacional Canaima", FXB, 52, 700), WHITE, False)
        t2 = timg("Estado Bolívar, Venezuela", FSB, 40, MUTED, False)
        card.alpha_composite(t1, (140 - 24, 40 - 24)); card.alpha_composite(t2, (140 - 24, 112 - 24))
        slide(c, card, 540, 1400, t, 4.15, 0.5, 60)

BARS = [("Niágara", "", 51), ("Torre", "Eiffel", 330), ("Burj", "Khalifa", 828), ("Salto", "Ángel", 979)]
def s3(c, t):
    pop(c, timg("MIDE", FSB, 58, MUTED), 540, 220, t, 0.1)
    n = int(round(979 * eoc(prog(t, 0.6, 1.5))))
    if t >= 0.6:
        put(c, timg(f"{n} m", FB, 190, YEL), 540, 355, 1, clamp((t - 0.6) * 4))
    pop(c, timg("de altura", FSB, 58, WHITE), 540, 485, t, 2.4)
    base, maxh, bw, gap, x0 = 1450, 680, 170, 60, 110
    timing = {3: (0.6, 1.5), 2: (4.5, 0.9), 0: (8.2, 0.6), 1: (8.5, 0.8)}
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.line([(70, base), (1010, base)], fill=(255, 255, 255, 90), width=3)
    labels = []
    for i, (a, b, v) in enumerate(BARS):
        s, du = timing[i]
        q = eoc(prog(t, s, du))
        x = x0 + i * (bw + gap)
        hh = maxh * v / 979 * q
        if q > 0:
            col = (111, 211, 255, 255) if i == 3 else (70, 104, 150, 255)
            d.rounded_rectangle((x, base - max(hh, 16), x + bw, base), radius=14, fill=col)
            if i == 3:
                for k in range(9):
                    yy = base - hh + ((k / 9 + t * 0.55) % 1) * hh
                    xx = x + 22 + (k * 37) % (bw - 44)
                    d.line([(xx, yy), (xx, min(base, yy + 70))], fill=(235, 248, 255, 170), width=4)
            labels.append((f"{int(round(v * q))} m", x + bw / 2, base - hh - 38, q))
        labels.append(((a, b), x + bw / 2, None, prog(t, s, 0.3)))
    c.alpha_composite(lay)
    for lab, x, y, q in labels:
        if y is None:
            a, b = lab
            put(c, timg(a, FSB, 38, MUTED, False), x, base + 42, 1, q)
            if b: put(c, timg(b, FSB, 38, MUTED, False), x, base + 86, 1, q)
        else:
            put(c, timg(lab, FXB, 40, WHITE), x, y, 1, clamp(q * 3))
    if 4.6 <= t < 8.0:
        pop(c, pill("Más alta que el Burj Khalifa", FXB, 44, NAVY, (255, 210, 63, 255)), 540, 610, t, 4.6, 0.4)
    if t >= 8.55:
        pop(c, pill("¡Casi 20× el Niágara!", FXB, 48, NAVY, (255, 210, 63, 255)), 540, 610, t, 8.55, 0.4)

def tepuy_section(c, t):
    reveal = eoc(prog(t, 0.0, 0.8))
    if reveal <= 0: return
    w, h = W, 900
    if 'sect' not in A:
        top = 640
        poly = [(0, 1450), (0, 1180), (60, 1000), (90, 760), (120, top + 8), (300, top), (500, top + 6), (650, top)]
        rng = np.random.default_rng(5)
        wall = [(650 + rng.uniform(0, 22), top + (1450 - top) * k / 12) for k in range(1, 13)]
        poly += wall
        mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(poly, fill=255)
        body = Image.fromarray(np.dstack([gradient_fill(W, H, (40, 64, 56), (24, 44, 40)), np.array(mask)]), 'RGBA')
        d = ImageDraw.Draw(body)
        d.polygon([(120, top + 6), (300, top - 2), (500, top + 4), (650, top - 2), (650, top + 24), (120, top + 30)], fill=(74, 140, 86, 255))
        d.rectangle((0, 1450, W, 1520), fill=(30, 80, 46, 255))
        A['sect'] = body
    body = A['sect']
    cut = int(1520 - (1520 - 600) * reveal)
    crop = body.crop((0, cut, W, H))
    comp(c, crop, 0, cut)

def s4(c, t):
    pop(c, timg("¿Por qué es tan alta?", FXB, fit("¿Por qué es tan alta?", FXB, 86), WHITE), 540, 260, t, 0.0)
    tepuy_section(c, t)
    wa = prog(t, 0.8, 0.5)
    if wa > 0:
        y0, ymid, yb = 646, 1307, 1450
        water(c, t, 686, y0, ymid, 24, 92, seed=21, speed=560, alpha=wa)
        water(c, t + .3, 700, ymid, yb, 70, 110, seed=22, speed=300, n=50, alpha=wa)
    pop(c, timg("TEPUY", FB, 84, YEL), 370, 760, t, 2.65, 0.4)
    pop(c, timg("cima plana y", FSB, 40, WHITE), 370, 840, t, 4.45, 0.35)
    pop(c, timg("paredes verticales", FSB, 40, WHITE), 370, 890, t, 5.35, 0.35)
    pop(c, timg("+1,500 millones", FB, fit("+1,500 millones", FB, 60, 520), YEL), 340, 1060, t, 7.85, 0.4)
    pop(c, timg("de años de antigüedad", FSB, 38, WHITE), 340, 1125, t, 8.0, 0.35)
    q = eoc(prog(t, 10.9, 0.9))
    if q > 0:
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        x, ya, yb = 900, 646, 646 + (1307 - 646) * q
        d.line([(x, ya), (x, yb)], fill=(255, 210, 63, 255), width=6)
        d.line([(x - 26, ya), (x + 26, ya)], fill=(255, 210, 63, 255), width=6)
        d.line([(x - 26, yb), (x + 26, yb)], fill=(255, 210, 63, 255), width=6)
        c.alpha_composite(lay)
    pop(c, pill("807 m", FB, 60, NAVY, (255, 210, 63, 255), 26, 12), 900, 960, t, 11.05, 0.4)
    pop(c, pill("caída libre", FXB, 36, WHITE, (8, 18, 40, 235), 20, 10), 900, 1040, t, 11.25, 0.35)

def foot_path():
    pts = [(430, 905), (300, 915), (170, 935), (130, 1050), (110, 1200), (90, 1330), (60, 1470)]
    out = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        L = math.hypot(x2 - x1, y2 - y1); k = int(L / 34)
        for j in range(k):
            u = j / k; out.append((x1 + (x2 - x1) * u, y1 + (y2 - y1) * u, math.atan2(y2 - y1, x2 - x1)))
    return out

def s5(c, t):
    tep, g = A['tep5'], A['geo5']
    tepuy_at(c, tep, g, t, 90, 820, alpha=eoc(prog(t, 0, .5)), seed=31)
    pop(c, timg("Su nombre viene de", FSB, 54, MUTED), 540, 220, t, 0.0)
    pop(c, timg("JIMMIE ANGEL", FB, fit("JIMMIE ANGEL", FB, 130), YEL), 540, 330, t, 1.05, 0.45, 0.6)
    pop(c, timg("piloto estadounidense", FSB, 50, WHITE), 540, 440, t, 2.45)
    fade_story = 1 - prog(t, 13.9, 0.35)
    if t < 8.85:
        pop(c, pill("1933", FB, 76, WHITE), 540, 590, t, 5.05, 0.4)
        if t >= 7.25: pop(c, timg("buscando oro", FXB, 48, YEL), 540, 690, t, 7.25)
    elif t < 14.25:
        q = prog(t, 8.85, 0.35)
        put(c, pill("1937", FB, 76, WHITE), 540, 590, 0.75 + 0.25 * eob(q), clamp(q * 2.5) * fade_story)
        if t >= 12.25:
            q2 = prog(t, 12.25, 0.35)
            put(c, timg("¡Atascada en el lodo!", FXB, 54, CORAL), 540, 690, 0.75 + 0.25 * eob(q2), clamp(q2 * 2.5) * fade_story)
    plane = A['plane']; land = (430, 868)
    if 3.9 <= t < 8.85:
        u = prog(t, 3.9, 4.7)
        x = -170 + (W + 340) * u; y = 790 + 14 * math.sin(t * 3)
        put(c, plane, x, y)
    elif t >= 8.85:
        u = eoc(prog(t, 8.85, 1.8))
        x = -170 + (land[0] + 170) * u; y = 680 + (land[1] - 680) * u
        ang = -8 * (1 - prog(t, 10.05, 0.6)) if t < 10.65 else 0
        if t >= 12.25: ang = -26 * eob(prog(t, 12.25, 0.45))
        pr = plane.rotate(ang, resample=Image.BICUBIC, expand=True)
        put(c, pr, x, y + (14 if t >= 12.25 else 0) * eob(prog(t, 12.25, 0.45)))
    if t >= 14.25:
        n = 1 + int(10 * eoc(prog(t, 14.3, 0.75)))
        pop(c, timg(f"{n} DÍAS", FB, 120, YEL), 540, 600, t, 14.25, 0.4)
        pop(c, timg("caminando por la selva", FSB, 46, WHITE), 540, 705, t, 14.45)
        steps = foot_path(); k = int(len(steps) * prog(t, 14.25, 2.3))
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for i, (x, y, a) in enumerate(steps[:k]):
            off = 9 if i % 2 else -9
            px, py = x - off * math.sin(a), y + off * math.cos(a)
            d.ellipse((px - 7, py - 10, px + 7, py + 10), fill=(255, 255, 255, 220))
        c.alpha_composite(lay)

def s6(c, t):
    tepuy_at(c, A['tep1'], A['geo1'], t, 40, 880, alpha=0.38 * eoc(prog(t, 0, .6)), seed=41)
    pop(c, timg("Pero los pemones", FSB, 58, MUTED), 540, 360, t, 0.15)
    pop(c, timg("ya la llamaban", FSB, 58, MUTED), 540, 435, t, 0.95)
    pop(c, timg("KEREPAKUPAI", FB, fit("KEREPAKUPAI", FB, 132), YEL), 540, 600, t, 1.85, 0.45, 0.6)
    pop(c, timg("MERÚ", FB, 132, YEL), 540, 740, t, 2.65, 0.45, 0.6)
    pop(c, timg("“el salto del lugar", FIT, 66, WHITE), 540, 900, t, 3.45)
    pop(c, timg("más profundo”", FIT, 66, WHITE), 540, 985, t, 4.35)
    q = prog(t, 6.2, 0.4)
    if q > 0:
        btn = pill("SÍGUENOS", FB, 72, NAVY, (255, 210, 63, 255), 80, 26)
        pulse = 1 + 0.035 * math.sin((t - 6.2) * 7) * clamp((t - 6.6) * 3)
        put(c, btn, 540, 1260, (0.7 + 0.3 * eob(q)) * pulse, clamp(q * 2.5))
        pop(c, timg("para otro dato mañana", FSB, 50, WHITE), 540, 1385, t, 6.75)

SCENES = [s1, s2, s3, s4, s5, s6]

def frame(k, t):
    c = A['bg'].copy()
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    SCENES[k](lay, t)
    a = 1.0
    if k > 0: a = min(a, clamp(t / 0.18))
    if k < len(SCENES) - 1: a = min(a, clamp((DUR[k] - t) / 0.18))
    c.alpha_composite(with_alpha(lay, a))
    # global overlays
    gt = START[k] + t
    put(c, pill("DATO DEL DÍA", FXB, 32, YEL, (8, 18, 40, 200), 28, 12, (255, 210, 63, 120)), 540, 110)
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, W, 10), fill=(255, 255, 255, 50))
    d.rectangle((0, 0, int(W * gt / TOTAL), 10), fill=YEL)
    return c

def render(k, out):
    build()
    n = int(round(DUR[k] * FPS))
    tmp = out.replace('.mp4', '.part.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(k, i / FPS).convert('RGB').tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)
    else: sys.exit(1)

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'still':
        build()
        for spec in sys.argv[2:]:
            k, t = spec.split(':'); k = int(k); t = float(t)
            frame(k, t).convert('RGB').save(f'/home/claude/salto/still_{k}_{t}.jpg', quality=88)
    elif mode == 'scene':
        render(int(sys.argv[2]), f'/home/claude/salto/scene{sys.argv[2]}.mp4')
