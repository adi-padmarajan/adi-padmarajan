#!/usr/bin/env python3
"""
Generates the animated SVG assets for adi-padmarajan's profile README.

Night edition (what the README shows now): night-hero, night-notes,
night-card-*, night-footer — one clear night at an alpine lake.

Original concept: the README is a day on the trail in the Pacific Northwest. Reading top
to bottom you walk from dawn to night:

    06:12  dawn       alpenglow on glacier peaks, a lake holding the sunrise
    10:40  forest     old-growth fir, fog, light falling through the canopy
           field notes  who I am, plotted on a trail map (Victoria -> Vancouver)
    15:20  river      golden hour, salmon running, the valley floor
           trails     three signposted ways to reach me
    22:47  camp       aurora over an alpine lake, a fire still going

Every landscape is procedural (midpoint-displacement ridgelines, generated
conifers, contour maps), so re-running with the same seeds reproduces the
exact same files. Everything animates with CSS / SMIL only, which is what
GitHub allows inside an <img>.

Run:  python3 generate_assets.py
Out:  assets/*.svg
"""

import math
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)

# ── design tokens ────────────────────────────────────────────────────────────
NIGHT  = "#050A14"
INK    = "#0A1714"   # darkest forest
PINE   = "#12302A"
MOSS   = "#3F6B4E"
FERN   = "#8CC09A"
SAGE   = "#A9C4AA"
CREAM  = "#FFF4E2"
GOLD   = "#F4C27A"
EMBER  = "#F28B4C"
AURORA = "#6CF5BE"
LILAC  = "#A98BFF"

SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,'Book Antiqua',Georgia,'Times New Roman',serif"
SANS  = "ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"
MONO  = "ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace"

EASE = "cubic-bezier(.16,1,.3,1)"   # expo-out: everything settles, nothing bounces


def write(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  assets/{name:<22} {len(content) / 1024:6.1f} KB")


def n(v):
    """Compact number for path data."""
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def P(x, y):
    return f"{n(x)} {n(y)}"


# ── geometry ─────────────────────────────────────────────────────────────────
def ridge(rnd, x0, x1, base, rough, peaks=(), iters=7, decay=.56):
    """Midpoint-displacement ridgeline with hand-placed peaks laid on top."""
    N = 2 ** iters + 1
    ys = [0.0] * N
    ys[0], ys[-1] = rnd.uniform(-1, 1) * rough, rnd.uniform(-1, 1) * rough
    step, s = N - 1, rough
    while step > 1:
        h = step // 2
        for i in range(h, N - 1, step):
            ys[i] = (ys[i - h] + ys[i + h]) / 2 + rnd.uniform(-1, 1) * s
        s *= decay
        step = h
    pts = []
    for i, y in enumerate(ys):
        x = x0 + (x1 - x0) * i / (N - 1)
        lift = sum(ph * max(0.0, 1 - abs(x - px) / pw) ** 1.45 for px, ph, pw in peaks)
        pts.append((x, base + y - lift))
    return pts


def yat(pts, x):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if ax <= x <= bx:
            return ay + (by - ay) * (x - ax) / (bx - ax)
    return pts[-1][1] if x > pts[-1][0] else pts[0][1]


def fill_under(pts, bottom):
    return (f"M{P(pts[0][0], bottom)} L" + " L".join(P(x, y) for x, y in pts)
            + f" L{P(pts[-1][0], bottom)}Z")


def line_of(pts):
    return "M" + " L".join(P(x, y) for x, y in pts)


def smooth(pts, closed=False):
    """Catmull-Rom through the points, emitted as cubic Béziers."""
    if closed:
        Q = [pts[-1]] + list(pts) + [pts[0], pts[1]]
        segs = range(1, len(pts) + 1)
    else:
        Q = [pts[0]] + list(pts) + [pts[-1]]
        segs = range(1, len(pts))
    d = f"M{P(*Q[1])}"
    for i in segs:
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{P(*c1)} {P(*c2)} {P(*p2)}"
    return d + ("Z" if closed else "")


def snowcap(rnd, pts, snowline, depth=(10, 34)):
    """Snow follows the ridge down to a ragged line just below the snowline."""
    top, bot = [], []
    for x, y in pts:
        if y < snowline + 6:
            top.append((x, y))
            bot.append((x, max(y, min(y + rnd.uniform(*depth), snowline + rnd.uniform(-8, 10)))))
        elif top:
            top.append((x, y))
            bot.append((x, y))
    if not top:
        return ""
    return "M" + " L".join(P(x, y) for x, y in top) + " L" + " L".join(P(x, y) for x, y in reversed(bot)) + "Z"


def fir(rnd, x, base, h, wr=.34):
    """A Douglas-fir / spruce silhouette: drooping tiers, slightly asymmetric."""
    w = h * wr * rnd.uniform(.85, 1.15)
    tiers = max(3, min(10, int(h / 8)))
    top = base - h
    crown = base - h * .06
    R, L = [], []
    for i in range(tiers):
        t = (i + 1) / tiers
        ty = top + (crown - top) * t
        for side, out in ((1, R), (-1, L)):
            tw = w / 2 * (.16 + .84 * t) * rnd.uniform(.78, 1.16)
            out.append((x + side * tw, ty + h * .016))
            if i < tiers - 1:
                out.append((x + side * tw * .38, ty - h * .006))
    tr = max(.6, w * .045)
    pts = [(x, top + rnd.uniform(-h * .02, 0))] + R + [(x + tr, crown), (x + tr, base), (x - tr, base), (x - tr, crown)] + L[::-1]
    return "M" + "L".join(P(px, py) for px, py in pts) + "Z"


def faces(rnd, pts, peaks, sun_x, bottom):
    """The face of each peak turned away from the sun, from crest to a ragged crease."""
    out = []
    for px, ph, pw in peaks:
        cand = [p for p in pts if abs(p[0] - px) < 26]
        if not cand:
            continue
        top = min(cand, key=lambda p: p[1])
        side = -1 if px < sun_x else 1
        edge, lowest = [], top[1]
        for p in sorted((p for p in pts if (p[0] - top[0]) * side >= 0), key=lambda p: p[0] * side):
            if abs(p[0] - top[0]) > pw * .9 or p[1] < lowest - 7:
                break
            lowest = max(lowest, p[1])
            edge.append(p)
        if len(edge) < 3:
            continue
        vx, vy = edge[-1]
        foot_y = min(bottom, vy + (vy - top[1]) * .7)
        foot = (top[0] + (vx - top[0]) * .55, foot_y)
        crease, steps = [], 7
        for k in range(steps, 0, -1):
            t = k / steps
            crease.append((top[0] + (foot[0] - top[0]) * t ** 1.3 + (rnd.uniform(-4, 4) if k < steps else 0),
                           top[1] + (foot[1] - top[1]) * t))
        out.append("M" + " L".join(P(*p) for p in edge) + f" L{P(vx, (vy + foot_y) / 2)} L"
                   + " L".join(P(*p) for p in crease) + "Z")
    return "".join(out)


def fern(rnd, x, y, length, angle, curl, leaf):
    """A sword fern frond: an arching stem with alternating leaflets."""
    N = 14
    a, px, py = math.radians(angle), x, y
    stem, blades = [(px, py)], []
    for i in range(1, N + 1):
        t = i / N
        a += math.radians(curl) / N
        px, py = px + math.cos(a) * length / N, py + math.sin(a) * length / N
        stem.append((px, py))
        lw = leaf * math.sin(math.pi * min(1, t * 1.15)) * (1 - .35 * t) + .6
        for s_ in (1, -1):
            nx, ny = math.cos(a + s_ * 1.15), math.sin(a + s_ * 1.15)
            tx, ty = math.cos(a), math.sin(a)
            blades.append(f"M{P(px - tx * 2, py - ty * 2)} L{P(px + nx * lw + tx * 2.5, py + ny * lw + ty * 2.5)} L{P(px + tx * 1.5, py + ty * 1.5)}Z")
    return line_of(stem), "".join(blades)


def treeline(rnd, rid, hmin, hmax, gap, sink=2, x0=None, x1=None, hscale=None):
    """A band of firs standing on a ridgeline."""
    x0 = rid[0][0] if x0 is None else x0
    x1 = rid[-1][0] if x1 is None else x1
    out, x = [], x0 + rnd.uniform(0, gap)
    while x < x1:
        h = rnd.uniform(hmin, hmax) * (hscale(x) if hscale else 1)
        out.append(fir(rnd, x, yat(rid, x) + sink, h))
        x += gap * rnd.uniform(.55, 1.25)
    return "".join(out)


# ── shared bits ──────────────────────────────────────────────────────────────
def motes(rnd, count, x0, x1, y0, y1, color, rmax=1.5, cls="mote"):
    out = []
    for _ in range(count):
        d = rnd.uniform(7, 16)
        out.append(f'<circle class="{cls}" cx="{n(rnd.uniform(x0, x1))}" cy="{n(rnd.uniform(y0, y1))}" '
                   f'r="{n(rnd.uniform(.5, rmax))}" fill="{color}" '
                   f'style="animation-duration:{d:.1f}s;animation-delay:-{rnd.uniform(0, d):.1f}s"/>')
    return "".join(out)


MOTE_CSS = """.mote { animation:mote ease-in-out infinite; }
    @keyframes mote {
      0%   { transform:translate(0,0);      opacity:0; }
      20%  { opacity:.9; }
      50%  { transform:translate(9px,-14px); opacity:.35; }
      80%  { opacity:.85; }
      100% { transform:translate(-4px,-30px); opacity:0; }
    }"""


def bird(x, y, s, dur, delay):
    a = "M-7 0 Q-3.5 -4.5 0 0 Q3.5 -4.5 7 0"
    b = "M-7 1.5 Q-3.5 2.5 0 0 Q3.5 2.5 7 1.5"
    c = "M-7 -2 Q-3.5 -1 0 0 Q3.5 -1 7 -2"
    return (f'<g transform="translate({n(x)},{n(y)}) scale({s})"><path d="{a}">'
            f'<animate attributeName="d" dur="{dur}s" begin="-{delay}s" repeatCount="indefinite" values="{a};{c};{b};{c};{a}"/>'
            f'</path></g>')


def ripple_mask(mid, H, W, y0, period=5, on=3.4, gap="#8c8c8c"):
    """Horizontal bands that break a reflection up like moving water."""
    return f"""<pattern id="{mid}p" width="{W}" height="{period}" patternUnits="userSpaceOnUse">
      <rect width="{W}" height="{on}" fill="#fff"/>
      <rect y="{on}" width="{W}" height="{period - on}" fill="{gap}"/>
    </pattern>
    <mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="{y0}" width="{W}" height="{H - y0}">
      <rect x="0" y="{y0}" width="{W}" height="{H - y0}" fill="url(#{mid}p)"/>
    </mask>"""


def frame(W, H, rx, stroke, op=".35"):
    return f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{rx}" fill="none" stroke="{stroke}" stroke-opacity="{op}"/>'


def reduced(selectors, extra=""):
    return f"@media (prefers-reduced-motion: reduce) {{ {selectors} {{ animation:none !important; }} {extra} }}"


# ═════════════════════════════════════════════════════════════════════════════
# 1. HERO — GOLDEN HOUR
# ═════════════════════════════════════════════════════════════════════════════
def banner():
    rnd = random.Random(4928)
    W, H0, HZ = 1200, 620, 476            # scene is drawn on a 620-high canvas...
    OFF = 54                              # ...then pushed down to give the title open sky
    H = H0 + OFF
    SX, SY = 760, 336                     # a low evening sun, settling into the valley

    PK1 = [(150, 140, 260), (330, 160, 230), (560, 92, 200), (990, 168, 250), (1150, 112, 200)]
    PK2 = [(60, 150, 220), (420, 110, 210), (1120, 175, 260), (880, 58, 140)]
    L1 = ridge(rnd, -20, W + 20, 372, 14, PK1)
    L2 = ridge(rnd, -20, W + 20, 420, 16, PK2)
    L3 = ridge(rnd, -20, W + 20, 448, 10, [(250, 72, 260), (620, 36, 180), (1000, 80, 240)], iters=6)
    L4 = ridge(rnd, -20, W + 20, 466, 6, [(130, 32, 240), (520, 16, 200), (900, 36, 260)], iters=5)
    L5 = ridge(rnd, -20, W + 20, 478, 3, [], iters=4)

    snow1 = snowcap(rnd, L1, 300)
    shade1 = faces(rnd, L1, PK1, SX, HZ + 20)
    shade2 = faces(rnd, L2, PK2, SX, HZ + 20)
    snow2 = snowcap(rnd, L2, 296, (6, 22))
    trees3 = treeline(rnd, L3, 5, 10, 4.5, sink=3)
    trees4 = treeline(rnd, L4, 9, 22, 6, sink=3)
    trees5 = treeline(rnd, L5, 16, 46, 7.5, sink=4)

    # long, soft rays fanning out of the sun, behind every range
    rays = []
    for k in range(15):
        a = math.radians(-176 + k * 12 + rnd.uniform(-3, 3))
        w = math.radians(rnd.uniform(1.2, 3.4))
        r = 900
        rays.append(f'<path d="M{SX} {SY} L{P(SX + r * math.cos(a - w), SY + r * math.sin(a - w))} '
                    f'L{P(SX + r * math.cos(a + w), SY + r * math.sin(a + w))}Z" '
                    f'style="animation-delay:-{rnd.uniform(0, 9):.1f}s"/>')
    rays = "".join(rays)

    # long bands of cloud, lit gold from underneath
    clouds = []
    for cx, cy, rx, ry, op, dur in [(300, 262, 260, 7, .7, 46), (930, 246, 280, 9, .65, 58),
                                    (620, 290, 200, 5, .6, 40), (110, 222, 170, 5, .45, 52),
                                    (1090, 292, 190, 6, .5, 44), (520, 206, 150, 3.5, .4, 60),
                                    (820, 196, 120, 3, .35, 50)]:
        clouds.append(f'<ellipse class="cloud" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#cloud)" '
                      f'opacity="{op}" style="animation-duration:{dur}s;animation-delay:-{rnd.uniform(0, dur):.0f}s"/>')
    clouds = "".join(clouds)

    mist = []
    for cx, cy, rx, ry, dur in [(200, 452, 260, 14, 38), (720, 458, 300, 12, 46), (1080, 448, 240, 16, 34),
                                (480, 470, 220, 9, 52), (950, 472, 260, 10, 42)]:
        mist.append(f'<ellipse class="mist" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#mistg)" '
                    f'style="animation-duration:{dur}s;animation-delay:-{rnd.uniform(0, dur):.0f}s"/>')
    mist = "".join(mist)

    # a wide road of light across the lake
    glints = []
    for i in range(24):
        y = HZ + 4 + i * 5.8 + rnd.uniform(-1, 1)
        w = 90 * (1 - i / 30) * rnd.uniform(.45, 1.1) + 6
        glints.append(f'<rect class="glint" x="{n(SX - w / 2 + rnd.uniform(-10, 10))}" y="{n(y)}" width="{n(w)}" height="1.4" rx=".7" '
                      f'style="animation-delay:-{rnd.uniform(0, 2.4):.2f}s;animation-duration:{rnd.uniform(1.6, 3):.2f}s"/>')
    glints = "".join(glints)

    ripples = "".join(
        f'<rect class="rip" x="{n(rnd.uniform(-200, W))}" y="{n(HZ + 14 + i * 9 + rnd.uniform(-2, 2))}" '
        f'width="{n(rnd.uniform(60, 260))}" height=".8" style="animation-duration:{rnd.uniform(14, 26):.1f}s;'
        f'animation-delay:-{rnd.uniform(0, 26):.1f}s"/>'
        for i in range(14))

    # near shore: a meadow bank, two stands of old fir, and the rock the hiker stands on
    bank = smooth([(-20, 588), (160, 596), (380, 610), (640, 606), (900, 600), (1080, 588), (1220, 578)]) + f" L{W + 20} {H + 10} L-20 {H + 10}Z"
    fg_back = "".join(f'<g class="sway" style="animation-delay:-{d}s"><path d="{fir(rnd, x, b, h, .30)}"/></g>'
                      for x, b, h, d in [(20, 650, 250, 1), (135, 652, 300, 3), (1085, 652, 290, 2), (1190, 650, 230, 4)])
    fg_front = "".join(f'<g class="sway" style="animation-delay:-{d}s"><path d="{fir(rnd, x, b, h, .30)}"/></g>'
                       for x, b, h, d in [(-30, 660, 560, 0), (62, 664, 450, 2.5), (1150, 664, 440, 1.5), (1236, 660, 580, 3.5)])

    grass, flowers = [], []
    for _ in range(140):
        x = rnd.uniform(170, 1060)
        if 600 < x < 790:
            continue
        base = yat([(-20, 588), (160, 596), (380, 610), (640, 606), (900, 600), (1080, 588), (1220, 578)], x) + rnd.uniform(-1, 6)
        h = rnd.uniform(8, 24)
        lean = rnd.uniform(-5, 5)
        grass.append(f'<path class="reed" d="M{n(x)} {n(base)} q{n(lean * .3)} -{n(h / 2)} {n(lean)} -{n(h)}" '
                     f'style="animation-delay:-{rnd.uniform(0, 4):.1f}s"/>')
        if rnd.random() < .45:
            c = rnd.choice(["#FFC768", "#FFE3A6", "#F59A6B", "#F2B6C2", "#FFD98A"])
            flowers.append(f'<g class="reed" style="animation-delay:-{rnd.uniform(0, 4):.1f}s">'
                           f'<path d="M{n(x)} {n(base)} q{n(lean * .2)} -{n(h * .4)} {n(lean * .6)} -{n(h * .75)}" fill="none" stroke="#0D1A14" stroke-width="1"/>'
                           f'<circle cx="{n(x + lean * .6)}" cy="{n(base - h * .75)}" r="{n(rnd.uniform(1.2, 2.2))}" fill="{c}"/></g>')
    grass, flowers = "".join(grass), "".join(flowers)

    rock = smooth([(560, 640), (600, 606), (640, 594), (672, 588), (708, 587), (736, 592), (770, 606), (812, 640)]) + "Z"

    # the backpacker: back to us, poles planted, hat brim and a tall pack against the light
    hx, hy = 688, 588
    hiker = f"""<g transform="translate({hx} {hy}) scale(1.6)">
        <path d="M-12.6 -31 L-18.5 0 M12.6 -31 L18.5 0" fill="none" stroke="#0A120E" stroke-width="1.1" stroke-linecap="round"/>
        <path d="M-8.2 -2.8 L-7.8 -17 L-7.4 -31 L-.6 -31 L-1.6 -17 L-2.6 -2.8Z M8.2 -2.8 L7.8 -17 L7.4 -31 L.6 -31 L1.6 -17 L2.6 -2.8Z"/>
        <path d="M-9.8 0 h8.2 l-.5 -3.8 h-7.2z M1.6 0 h8.2 l-.5 -3.8 h-7.2z"/>
        <path d="M-9 -30 C-10 -40 -10.4 -48 -8.4 -53 L8.4 -53 C10.4 -48 10 -40 9 -30Z"/>
        <path d="M-8.6 -51 C-11.6 -44 -13 -37 -13.6 -31.4 L-11.2 -30.6 C-10.8 -36 -9.8 -42 -7.4 -47Z M8.6 -51 C11.6 -44 13 -37 13.6 -31.4 L11.2 -30.6 C10.8 -36 9.8 -42 7.4 -47Z"/>
        <circle cx="-12.6" cy="-30.8" r="1.8"/><circle cx="12.6" cy="-30.8" r="1.8"/>
        <rect x="-2.1" y="-61" width="4.2" height="8"/>
        <ellipse cy="-64" rx="4.8" ry="5.4"/>
        <rect x="-12.4" y="-36" width="24.8" height="3.2" rx="1.4"/>
        <path d="M-10.8 -58.5 Q-10.8 -63.5 -6.6 -64.2 Q0 -67.6 6.6 -64.2 Q10.8 -63.5 10.8 -58.5 V-31.5 Q10.8 -27.6 7 -27.6 H-7 Q-10.8 -27.6 -10.8 -31.5Z" fill="#17241C" stroke="#08100C" stroke-width=".9"/>
        <path d="M-9.6 -60.5 Q0 -64.6 9.6 -60.5" fill="none" stroke="#08100C" stroke-width=".9"/>
        <path d="M-7 -49 H7 V-37.5 Q7 -36 5.5 -36 H-5.5 Q-7 -36 -7 -37.5Z" fill="#132019" stroke="#08100C" stroke-width=".7"/>
        <rect x="-13" y="-30" width="26" height="6.4" rx="3.2" fill="#1E2C23" stroke="#08100C" stroke-width=".8"/>
        <path d="M-6 -30 V-23.6 M6 -30 V-23.6" stroke="#08100C" stroke-width=".9"/>
        <rect x="10.2" y="-46" width="3.8" height="10.5" rx="1.3"/>
        <ellipse cy="-67.8" rx="9.4" ry="1.9"/>
        <path d="M-4.9 -67.6 Q-4.7 -74.4 0 -74.4 Q4.7 -74.4 4.9 -67.6Z"/>
        <g fill="none" stroke="url(#rimlight)" stroke-width="1.1" stroke-linecap="round">
          <path d="M4.9 -73 Q5.2 -70 4.9 -67.8"/>
          <path d="M5.5 -68.6 Q9 -68.4 9.4 -67.8"/>
          <path d="M10.8 -60 V-32"/>
          <path d="M14 -45 V-36"/>
          <path d="M12.6 -29 Q13.2 -27 12.6 -24"/>
          <path d="M13 -38 Q13.4 -34.5 13.6 -31.6"/>
          <path d="M7.6 -27 L8.2 -3"/>
          <path d="M13 -31 L18.5 0" stroke-width=".7"/>
        </g>
      </g>"""

    flock = "".join(bird(dx, dy, s, d, de) for dx, dy, s, d, de in
                    [(0, 0, 1.1, .9, 0), (-20, -9, .9, .85, .3), (-38, 6, .95, .95, .5), (-56, -14, .8, .8, .2), (-74, 2, .75, .9, .6)])
    flock2 = "".join(bird(dx, dy, s, d, de) for dx, dy, s, d, de in
                     [(0, 0, .6, .7, 0), (-12, -6, .55, .75, .2), (-22, 4, .5, .7, .4)])

    pollen = motes(rnd, 56, 120, 1080, 300, 610, "#FFD98C", 1.6)

    fx, fy = W / 2, (H0 / 2) + 20
    flare = "".join(
        f'<circle cx="{n(SX + (fx - SX) * t)}" cy="{n(SY + (fy - SY) * t)}" r="{r}" fill="{c}" fill-opacity="{o}"/>'
        for t, r, c, o in [(.55, 6, "#FFE2A0", .25), (1.25, 18, "#FFC070", .09), (1.6, 5, "#FFF0C8", .18),
                           (2.1, 32, "#FFB060", .05), (2.5, 9, "#FFE2A0", .10)])

    intro = "\n    ".join(
        f"@keyframes up{i} {{ from {{ transform:translateY({d}px); }} to {{ transform:none; }} }}\n"
        f"    .in{i} {{ animation:up{i} {dur}s {EASE} {dl}s both; }}"
        for i, (d, dur, dl) in enumerate([(26, 3.2, .05), (44, 3.0, .15), (64, 2.8, .25), (84, 2.6, .35), (104, 2.4, .45), (150, 2.6, .2)], 1))

    TITLE = "ADITYA PADMARAJAN"
    TY, TRACK = 148, 15
    title_shadow = "".join(
        f'<text class="title" x="{W / 2 + TRACK / 2}" y="{TY}" text-anchor="middle" stroke-width="{sw}" stroke-opacity="{so}">{TITLE}</text>'
        for sw, so in [(26, .05), (14, .08), (6, .12)])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Aditya Padmarajan — a backpacker watching the mountains at golden hour">
  <title>Aditya Padmarajan</title>
  <defs>
    <linearGradient id="sky" x1="0" y1="-{OFF}" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#1C2B4E"/>
      <stop offset=".26" stop-color="#3F5481"/>
      <stop offset=".50" stop-color="#A88A8E"/>
      <stop offset=".70" stop-color="#EFA662"/>
      <stop offset=".87" stop-color="#FFC66C"/>
      <stop offset="1"   stop-color="#FFE3A2"/>
    </linearGradient>
    <radialGradient id="glow" cx="{SX}" cy="{SY + 10}" r="680" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFF0BC" stop-opacity="1"/>
      <stop offset=".16" stop-color="#FFC970" stop-opacity=".65"/>
      <stop offset=".42" stop-color="#F5A05C" stop-opacity=".22"/>
      <stop offset="1"   stop-color="#F5A05C" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="sun" cx="50%" cy="50%" r="50%">
      <stop offset="0"   stop-color="#FFFDF2"/>
      <stop offset=".55" stop-color="#FFF0C2"/>
      <stop offset="1"   stop-color="#FFD27A"/>
    </radialGradient>
    <radialGradient id="corona" cx="50%" cy="50%" r="50%">
      <stop offset=".25" stop-color="#FFE29A" stop-opacity=".95"/>
      <stop offset="1"   stop-color="#FFE29A" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="rayg" cx="{SX}" cy="{SY}" r="460" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFE7AE" stop-opacity=".22"/>
      <stop offset="1"   stop-color="#FFE7AE" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="rim" cx="{SX}" cy="{SY}" r="460" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFC266" stop-opacity=".75"/>
      <stop offset="1"   stop-color="#FFC266" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="cloud" cx="50%" cy="50%" r="50%">
      <stop offset="0"   stop-color="#FFD38E"/>
      <stop offset="1"   stop-color="#FFB873" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="mistg" cx="50%" cy="50%" r="50%">
      <stop offset="0"   stop-color="#FFE3B4" stop-opacity=".6"/>
      <stop offset="1"   stop-color="#FFE3B4" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="g1" x1="0" y1="190" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#C6907A"/><stop offset="1" stop-color="#F4BE84"/></linearGradient>
    <linearGradient id="g2" x1="0" y1="240" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#9C6A6C"/><stop offset="1" stop-color="#DC9A6C"/></linearGradient>
    <linearGradient id="g3" x1="0" y1="360" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#5B4E62"/><stop offset="1" stop-color="#8C6660"/></linearGradient>
    <linearGradient id="g4" x1="0" y1="420" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#2E3C3A"/><stop offset="1" stop-color="#3E443E"/></linearGradient>
    <linearGradient id="snow" x1="0" y1="180" x2="0" y2="320" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFF6E0"/>
      <stop offset="1"   stop-color="#FFD69E" stop-opacity=".6"/>
    </linearGradient>
    <linearGradient id="shade" x1="0" y1="190" x2="0" y2="{HZ - 40}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#5A3A62" stop-opacity=".48"/>
      <stop offset="1"   stop-color="#5A3A62" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="haze" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"   stop-color="#FFC983" stop-opacity="0"/>
      <stop offset=".7"  stop-color="#FFC983" stop-opacity=".5"/>
      <stop offset="1"   stop-color="#FFC983" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="lake" x1="0" y1="{HZ}" x2="0" y2="{H0}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFD68F"/>
      <stop offset=".22" stop-color="#E29C60"/>
      <stop offset=".6"  stop-color="#6B4F58"/>
      <stop offset="1"   stop-color="#1F2229"/>
    </linearGradient>
    <linearGradient id="deep" x1="0" y1="{HZ}" x2="0" y2="{H0}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#16141A" stop-opacity="0"/>
      <stop offset="1"   stop-color="#16141A" stop-opacity=".7"/>
    </linearGradient>
    <linearGradient id="hzline" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="#FFE7B0" stop-opacity="0"/>
      <stop offset=".63" stop-color="#FFF2CF" stop-opacity="1"/>
      <stop offset="1"   stop-color="#FFE7B0" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="vig" cx="50%" cy="48%" r="75%">
      <stop offset=".6"  stop-color="#160E0C" stop-opacity="0"/>
      <stop offset="1"   stop-color="#160E0C" stop-opacity=".5"/>
    </radialGradient>
    <linearGradient id="topshade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"   stop-color="#101A36" stop-opacity=".55"/>
      <stop offset="1"   stop-color="#101A36" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="titlefill" x1="0" y1="{TY - 44}" x2="0" y2="{TY}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFFFFF"/>
      <stop offset="1"   stop-color="#FFEBC8"/>
    </linearGradient>
    <linearGradient id="rimlight" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="#FFC76E" stop-opacity=".2"/>
      <stop offset="1"   stop-color="#FFD98C" stop-opacity="1"/>
    </linearGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="#FFE3B0" stop-opacity="0"/>
      <stop offset=".5"  stop-color="#FFE3B0" stop-opacity=".75"/>
      <stop offset="1"   stop-color="#FFE3B0" stop-opacity="0"/>
    </linearGradient>
    {ripple_mask("rm", H0, W, HZ)}
    <clipPath id="lakeclip"><rect y="{HZ}" width="{W}" height="{H0 - HZ}"/></clipPath>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>

  <style>
    {intro}
    @keyframes sunup  {{ from {{ transform:translateY(70px); }} to {{ transform:none; }} }}
    @keyframes fadein {{ from {{ opacity:0; }} to {{ opacity:1; }} }}

    .sunrise {{ animation:sunup 4.2s {EASE} both; }}
    .rays    {{ fill:url(#rayg); animation:fadein 4s ease 1s both; }}
    .rays path {{ animation:ray 9s ease-in-out infinite; }}
    @keyframes ray {{ 0%,100% {{ opacity:.35; }} 50% {{ opacity:1; }} }}
    .corona  {{ transform-box:fill-box; transform-origin:center; animation:corona 6s ease-in-out infinite; }}
    @keyframes corona {{ 0%,100% {{ transform:scale(1); opacity:.8; }} 50% {{ transform:scale(1.14); opacity:1; }} }}

    .cloud {{ animation:cloud ease-in-out infinite alternate; }}
    @keyframes cloud {{ from {{ transform:translateX(-50px); }} to {{ transform:translateX(50px); }} }}
    .mist  {{ animation:cloud ease-in-out infinite alternate; }}

    .glint {{ fill:#FFF1C4; animation:glint ease-in-out infinite; }}
    @keyframes glint {{ 0%,100% {{ opacity:.15; }} 50% {{ opacity:1; }} }}
    .rip   {{ fill:#FFE7B8; opacity:.18; animation:rip linear infinite; }}
    @keyframes rip {{ from {{ transform:translateX(0); }} to {{ transform:translateX(260px); }} }}

    .sway {{ transform-box:fill-box; transform-origin:50% 100%; animation:sway 8s ease-in-out infinite alternate; }}
    @keyframes sway {{ from {{ transform:rotate(-.7deg); }} to {{ transform:rotate(.7deg); }} }}
    .reed {{ fill:none; stroke:#0D1A14; stroke-width:1.2; stroke-linecap:round;
             transform-box:fill-box; transform-origin:50% 100%; animation:reed 3.6s ease-in-out infinite alternate; }}
    @keyframes reed {{ from {{ transform:rotate(-5deg); }} to {{ transform:rotate(5deg); }} }}

    .flock  {{ fill:none; stroke:#2B1F28; stroke-width:1.5; stroke-linecap:round; animation:fly 30s linear infinite; }}
    .flock2 {{ fill:none; stroke:#4E3640; stroke-width:1.4; stroke-linecap:round; animation:fly 44s linear -18s infinite; }}
    @keyframes fly {{ from {{ transform:translate(-120px,30px); }} to {{ transform:translate({W + 160}px,-40px); }} }}
    {MOTE_CSS}

    .title {{ font-family:{SERIF}; font-size:58px; letter-spacing:{TRACK}px; }}
    .reveal {{ transform-box:fill-box; transform-origin:center; animation:reveal 3.4s {EASE} .9s both; }}
    @keyframes reveal {{ from {{ opacity:0; transform:translateY(14px) scale(1.05); }} to {{ opacity:1; transform:none; }} }}
    .rulein {{ transform-box:fill-box; transform-origin:center; animation:rulein 2.6s {EASE} 2s both; }}
    @keyframes rulein {{ from {{ transform:scaleX(0); opacity:0; }} to {{ transform:scaleX(1); opacity:1; }} }}
    .flare {{ animation:flare 7s ease-in-out infinite; }}
    @keyframes flare {{ 0%,100% {{ opacity:.6; }} 50% {{ opacity:1; }} }}

    {reduced(".in1,.in2,.in3,.in4,.in5,.in6,.sunrise,.rays,.rays path,.corona,.cloud,.mist,.glint,.rip,.sway,.reed,.flock,.flock2,.mote,.reveal,.rulein,.flare,pattern",
              ".flock,.flock2,.mote { opacity:0; }")}
  </style>

  <g clip-path="url(#frame)">
   <g transform="translate(0 {OFF})">
    <!-- sky -->
    <rect y="-{OFF}" width="{W}" height="{HZ + 4 + OFF}" fill="url(#sky)"/>
    <rect y="-{OFF}" width="{W}" height="{HZ + 4 + OFF}" fill="url(#glow)"/>
    <rect y="-{OFF}" width="{W}" height="260" fill="url(#topshade)"/>
    <g class="rays">{rays}</g>
    <g>{clouds}</g>

    <!-- land: also reflected in the lake below -->
    <g id="land">
      <g class="sunrise">
        <circle class="corona" cx="{SX}" cy="{SY}" r="110" fill="url(#corona)"/>
        <circle cx="{SX}" cy="{SY}" r="44" fill="url(#sun)"/>
      </g>
      <g class="in1">
        <path d="{fill_under(L1, HZ + 160)}" fill="url(#g1)"/>
        <path d="{fill_under(L1, HZ + 160)}" fill="url(#rim)"/>
        <path d="{snow1}" fill="url(#snow)"/>
        <path d="{shade1}" fill="url(#shade)"/>
      </g>
      <rect y="300" width="{W}" height="110" fill="url(#haze)" class="in1"/>
      <g class="in2">
        <path d="{fill_under(L2, HZ + 160)}" fill="url(#g2)"/>
        <path d="{fill_under(L2, HZ + 160)}" fill="url(#rim)"/>
        <path d="{snow2}" fill="url(#snow)" opacity=".8"/>
        <path d="{shade2}" fill="url(#shade)" opacity=".85"/>
      </g>
      <rect y="350" width="{W}" height="90" fill="url(#haze)" opacity=".85" class="in2"/>
      <g class="in3">
        <path d="{fill_under(L3, HZ + 160)}" fill="url(#g3)"/>
        <path d="{trees3}" fill="#5B4E62"/>
        <path d="{fill_under(L3, HZ + 160)}" fill="url(#rim)" opacity=".55"/>
      </g>
      <g class="in4">{mist}</g>
      <g class="in4">
        <path d="{fill_under(L4, HZ + 160)}" fill="url(#g4)"/>
        <path d="{trees4}" fill="#2E3C3A"/>
      </g>
      <g class="in5">
        <path d="{fill_under(L5, HZ + 160)}" fill="#1C2A22"/>
        <path d="{trees5}" fill="#1C2A22"/>
      </g>
    </g>

    <g class="flock2"><g transform="translate(0,236)">{flock2}</g></g>
    <g class="flock"><g transform="translate(0,300)">{flock}</g></g>

    <!-- lake -->
    <rect y="{HZ}" width="{W}" height="{H0 - HZ}" fill="url(#lake)"/>
    <g clip-path="url(#lakeclip)" mask="url(#rm)" opacity=".6">
      <use xlink:href="#land" href="#land" transform="matrix(1 0 0 -1 0 {2 * HZ})"/>
    </g>
    <rect y="{HZ}" width="{W}" height="{H0 - HZ}" fill="url(#deep)"/>
    <rect y="{HZ}" width="{W}" height="1.4" fill="url(#hzline)"/>
    <g>{glints}</g>
    <g>{ripples}</g>

    <!-- near shore -->
    <g class="in6">
      <path d="{bank}" fill="#0B1610"/>
      <path d="{rock}" fill="#0A140F"/>
      <path d="{smooth([(600, 606), (640, 594), (672, 588), (708, 587), (736, 592), (770, 606)])}" fill="none" stroke="#FFC76E" stroke-opacity=".35" stroke-width="1.2"/>
      <g fill="#0A120E">{hiker}</g>
      <g>{grass}</g>
      <g>{flowers}</g>
      <g fill="#14231B">{fg_back}</g>
      <g fill="#08100C">{fg_front}</g>
    </g>
    {pollen}

    <g class="flare">{flare}</g>
   </g>

    <rect width="{W}" height="{H}" fill="url(#vig)"/>

    {frame(W, H, 18, "#FFE3B0", ".2")}
  </g>
</svg>
"""


# ═════════════════════════════════════════════════════════════════════════════
# 2. CHAPTER I — THE OLD-GROWTH
# ═════════════════════════════════════════════════════════════════════════════
def chapter_forest():
    rnd = random.Random(1040)
    W, H = 1000, 230

    F1 = ridge(rnd, -20, W + 20, 108, 8, [(700, 26, 260), (300, 14, 200)], iters=5)
    F2 = ridge(rnd, -20, W + 20, 140, 7, [(520, 18, 240)], iters=5)
    F3 = ridge(rnd, -20, W + 20, 178, 6, [], iters=5)
    F4 = ridge(rnd, -20, W + 20, 236, 3, [], iters=4)

    t1 = treeline(rnd, F1, 22, 40, 8, sink=6)
    t2 = treeline(rnd, F2, 32, 60, 11, sink=6)
    t3 = treeline(rnd, F3, 54, 96, 17, sink=8)
    t4 = treeline(rnd, F4, 130, 210, 52, sink=8)
    stems, blades = [], []
    for x in [rnd.uniform(-10, W + 10) for _ in range(26)]:
        for ang, curl in [(-150 + rnd.uniform(-12, 12), 70), (-30 + rnd.uniform(-12, 12), -70), (-95 + rnd.uniform(-10, 10), rnd.choice([-40, 40]))]:
            st, bl = fern(rnd, x, H + 6, rnd.uniform(30, 52), ang, curl, rnd.uniform(5, 8))
            stems.append(st)
            blades.append(bl)
    ferns = f'<path d="{"".join(blades)}" fill="#0A2016"/><path d="{"".join(stems)}" fill="none" stroke="#0A2016" stroke-width="1.2"/>'
    under = smooth([(-20, 214), (120, 206), (260, 216), (420, 204), (600, 212), (780, 202), (920, 212), (1020, 206)]) + f" L{W + 20} {H + 5} L-20 {H + 5}Z"

    beams = "".join(
        f'<polygon class="beam" points="{x},-10 {x + w},-10 {x + w - 260},{H} {x - 260 - w * .6},{H}" '
        f'style="animation-delay:-{rnd.uniform(0, 7):.1f}s"/>'
        for x, w in [(560, 36), (650, 70), (760, 30), (830, 58), (930, 44), (1010, 64)])

    fog = "".join(
        f'<ellipse class="fog" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#fogg)" opacity="{op}" '
        f'style="animation-duration:{d}s;animation-delay:-{rnd.uniform(0, d):.0f}s"/>'
        for cx, cy, rx, ry, op, d in [(250, 132, 300, 18, .9, 40), (780, 128, 280, 16, .8, 48),
                                      (520, 170, 320, 16, .7, 36), (900, 176, 220, 14, .6, 44), (120, 172, 200, 12, .6, 50)])

    dust = motes(rnd, 30, 360, 980, 20, 210, "#FFF6DA", 1.3)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Waypoint one, the old-growth: who I am">
  <title>I am Aditya Padmarajan</title>
  <defs>
    <linearGradient id="fsky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"   stop-color="#EAF1DC"/>
      <stop offset=".5"  stop-color="#B2D2BB"/>
      <stop offset="1"   stop-color="#7AA693"/>
    </linearGradient>
    <radialGradient id="fsun" cx="880" cy="-30" r="460" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFF4CF" stop-opacity=".95"/>
      <stop offset="1"   stop-color="#FFF4CF" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="beamg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"   stop-color="#FFF8DD" stop-opacity=".42"/>
      <stop offset="1"   stop-color="#FFF8DD" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="fogg" cx="50%" cy="50%" r="50%">
      <stop offset="0"   stop-color="#F2F7EE" stop-opacity=".75"/>
      <stop offset="1"   stop-color="#F2F7EE" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="fscrim" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="#0B2119" stop-opacity=".92"/>
      <stop offset=".32" stop-color="#0B2119" stop-opacity=".66"/>
      <stop offset=".6"  stop-color="#0B2119" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="ff"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .beam {{ fill:url(#beamg); animation:beam 8s ease-in-out infinite; }}
    @keyframes beam {{ 0%,100% {{ opacity:.3; }} 50% {{ opacity:1; }} }}
    .fog  {{ animation:fog ease-in-out infinite alternate; }}
    @keyframes fog {{ from {{ transform:translateX(-70px); }} to {{ transform:translateX(70px); }} }}
    .sway {{ transform-box:fill-box; transform-origin:50% 100%; animation:sway 9s ease-in-out infinite alternate; }}
    .fern {{ transform-box:fill-box; transform-origin:50% 100%; animation:fern 6s ease-in-out infinite alternate; }}
    @keyframes fern {{ from {{ transform:skewX(-1.2deg); }} to {{ transform:skewX(1.2deg); }} }}
    @keyframes sway {{ from {{ transform:rotate(-.5deg); }} to {{ transform:rotate(.5deg); }} }}
    {MOTE_CSS}
    .k  {{ font-family:{MONO}; font-size:11px; letter-spacing:3px; fill:{GOLD}; }}
    .h  {{ font-family:{SERIF}; font-size:48px; fill:{CREAM}; letter-spacing:-.5px; }}
    .s  {{ font-family:{SANS}; font-size:14px; letter-spacing:.4px; fill:{SAGE}; }}
    .cue {{ animation:cue 2.4s ease-in-out infinite; }}
    @keyframes cue {{ 0%,100% {{ transform:translateY(-2px); opacity:.45; }} 50% {{ transform:translateY(3px); opacity:1; }} }}
    {reduced(".beam,.fog,.sway,.fern,.mote,.cue", ".mote { opacity:0; }")}
  </style>
  <g clip-path="url(#ff)">
    <rect width="{W}" height="{H}" fill="url(#fsky)"/>
    <rect width="{W}" height="{H}" fill="url(#fsun)"/>
    <g>{beams}</g>
    <path d="{fill_under(F1, H + 5)}" fill="#A6C7B4"/><path d="{t1}" fill="#A6C7B4"/>
    <g>{fog}</g>
    <path d="{fill_under(F2, H + 5)}" fill="#78A28D"/><path d="{t2}" fill="#78A28D"/>
    <rect y="120" width="{W}" height="70" fill="url(#fogg)" opacity=".35"/>
    <path d="{fill_under(F3, H + 5)}" fill="#3E6D59"/><path d="{t3}" fill="#3E6D59"/>
    <g fill="#163A2D" class="sway"><path d="{t4}"/></g>
    <path d="{under}" fill="#10291F"/>
    {dust}
    <g class="fern">{ferns}</g>
    <rect width="{W}" height="{H}" fill="url(#fscrim)"/>

    <text class="k" x="56" y="84"></text>
    <text class="h" x="{W / 2}" y="138" text-anchor="middle">I am<tspan font-style="italic" fill="#CDE6C4"> Aditya Padmarajan</tspan></text>
    <text class="s" x="56" y="172"></text>
    <g class="cue"><path d="M{W / 2 - 5} 163 l5 5 l5 -5" fill="none" stroke="{GOLD}" stroke-width="1.4" stroke-linecap="round"/></g>

    {frame(W, H, 16, CREAM, ".14")}
  </g>
</svg>
"""


# ═════════════════════════════════════════════════════════════════════════════
# 3. FIELD NOTES — IDENTITY + TRAIL MAP
# ═════════════════════════════════════════════════════════════════════════════
def identity():
    rnd = random.Random(2026)
    W, H = 1000, 400
    MX0, MY0, MX1, MY1 = 600, 30, 970, 370          # map panel

    def blob(cx, cy, rx, ry, rot, harmonics, k, rings, shift):
        """One contour ring: a noisy rotated ellipse; inner rings shrink toward a peak."""
        s = 1 - .14 * k
        ccx, ccy = cx + shift[0] * k / rings, cy + shift[1] * k / rings
        cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        pts = []
        for i in range(56):
            th = 2 * math.pi * i / 56
            m = 1 + sum(a * (1 - .05 * k) * math.sin(j * th + ph) for j, a, ph in harmonics)
            ex, ey = rx * s * m * math.cos(th), ry * s * m * math.sin(th)
            pts.append((ccx + ex * cr - ey * sr, ccy + ex * sr + ey * cr))
        return pts

    def land(cx, cy, rx, ry, rot, rings, shift, seed):
        r2 = random.Random(seed)
        harm = [(j, r2.uniform(.03, .09) / (j * .5), r2.uniform(0, 6.3)) for j in range(2, 7)]
        return [blob(cx, cy, rx, ry, rot, harm, k, rings, shift) for k in range(rings)]

    isle = land(636, 196, 168, 64, 52, 6, (-30, -36), 7)        # Vancouver Island, running NW-SE
    main = land(1046, 196, 206, 262, 20, 7, (40, -40), 11)      # the mainland and the Coast Mountains

    def contours(rings, fill, peak):
        out = [f'<path d="{smooth(rings[0], True)}" fill="{fill}" stroke="#5F8F70" stroke-opacity=".75" stroke-width="1.1"/>']
        for k, r in enumerate(rings[1:], 1):
            out.append(f'<path d="{smooth(r, True)}" fill="none" stroke="{FERN}" stroke-opacity="{.16 + .07 * k:.2f}" '
                       f'stroke-width="{.8 if k % 3 else 1.2}"/>')
        px = sum(p[0] for p in rings[-1]) / len(rings[-1])
        py = sum(p[1] for p in rings[-1]) / len(rings[-1])
        out.append(f'<path d="M{n(px - 4)} {n(py + 3)} l4 -7 l4 7z" fill="{GOLD}" fill-opacity=".7"/>'
                   f'<text class="pk" x="{n(px + 8)}" y="{n(py + 3)}">{peak}</text>')
        return "".join(out)

    def inside(pt, poly):
        x, y, c = pt[0], pt[1], False
        for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                c = not c
        return c

    def woods(rings, count):
        """Little fir glyphs scattered across the lowlands, between the coast and the third contour."""
        out, tries = [], 0
        while len(out) < count and tries < 4000:
            tries += 1
            x, y = rnd.uniform(MX0, MX1), rnd.uniform(MY0, MY1)
            if inside((x, y), rings[0]) and not inside((x, y), rings[2]):
                s_ = rnd.uniform(.8, 1.3)
                out.append(f"M{n(x)} {n(y - 5 * s_)} l{n(2.4 * s_)} {n(5 * s_)} h-{n(4.8 * s_)}z")
        return "".join(out)

    forest_glyphs = woods(isle, 46) + woods(main, 70)

    # Victoria sits at the island's south-east tip; Vancouver on the mainland's west coast
    vic = isle[0][0]
    vic = (636 + (vic[0] - 636) * .9, 196 + (vic[1] - 196) * .9)
    van = main[0][28]
    van = (1046 + (van[0] - 1046) * .96, 196 + (van[1] - 196) * .96)

    c1 = (vic[0] + 60, vic[1] - 10)
    c2 = (van[0] - 40, van[1] + 70)
    route = f"M{P(*vic)} C{P(*c1)} {P(*c2)} {P(*van)}"

    def bez(t):
        u = 1 - t
        return (u ** 3 * vic[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * van[0],
                u ** 3 * vic[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * van[1])
    L = sum(math.dist(bez(i / 200), bez((i + 1) / 200)) for i in range(200))

    waves = "".join(
        f'<path class="wv" d="M{n(x)} {n(y)} q4 -2.4 8 0 t8 0" style="animation-delay:-{rnd.uniform(0, 6):.1f}s"/>'
        for x, y in [(rnd.uniform(MX0, MX1), rnd.uniform(MY0, MY1)) for _ in range(70)])

    grid = "".join(f'<line x1="{x}" y1="{MY0}" x2="{x}" y2="{MY1}"/>' for x in range(MX0 + 74, MX1, 74)) + \
           "".join(f'<line x1="{MX0}" y1="{y}" x2="{MX1}" y2="{y}"/>' for y in range(MY0 + 68, MY1, 68))

    rows = [("CURRENT ROLE", "Software Developer", "STEMCELL Technologies"),
            ("STUDIED", "B.Sc. Computer Science", "University of Victoria"),
            ("BASECAMP", "Vancouver", "British Columbia")]
    rowsvg = []
    for i, (k, a, b) in enumerate(rows):
        y = 196 + i * 50
        rowsvg.append(f'<line x1="56" y1="{y - 26}" x2="546" y2="{y - 26}" stroke="{SAGE}" stroke-opacity=".16"/>'
                      f'<text class="lbl" x="56" y="{y}">{k}</text>'
                      f'<text class="val" x="190" y="{y}">{a}<tspan class="valb">  —  {b}</tspan></text>')
    rowsvg.append(f'<line x1="56" y1="{196 + 3 * 50 - 26}" x2="546" y2="{196 + 3 * 50 - 26}" stroke="{SAGE}" stroke-opacity=".16"/>')
    rowsvg = "".join(rowsvg)

    alt = ("Field notes: Aditya Padmarajan — Software Developer at STEMCELL Technologies; "
           "B.Sc. Computer Science, University of Victoria; based in Vancouver, British Columbia")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{alt}">
  <title>{alt}</title>
  <defs>
    <linearGradient id="pg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0"   stop-color="#13302A"/>
      <stop offset=".55" stop-color="#0C211C"/>
      <stop offset="1"   stop-color="#081613"/>
    </linearGradient>
    <radialGradient id="pglow" cx="160" cy="40" r="520" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="{GOLD}" stop-opacity=".10"/>
      <stop offset="1"   stop-color="{GOLD}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="sea" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0"   stop-color="#0F3236"/>
      <stop offset="1"   stop-color="#0A2226"/>
    </linearGradient>
    <linearGradient id="mapfade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0"   stop-color="#081613" stop-opacity="0"/>
      <stop offset="1"   stop-color="#081613" stop-opacity=".35"/>
    </linearGradient>
    <clipPath id="ic"><rect width="{W}" height="{H}" rx="16"/></clipPath>
    <clipPath id="mc"><rect x="{MX0}" y="{MY0}" width="{MX1 - MX0}" height="{MY1 - MY0}" rx="12"/></clipPath>
    <filter id="pinglow" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .eb  {{ font-family:{MONO}; font-size:11px; letter-spacing:3px; fill:{GOLD}; }}
    .hi  {{ font-family:{SERIF}; font-size:50px; fill:{CREAM}; letter-spacing:-.5px; }}
    .lbl {{ font-family:{SANS}; font-size:10px; font-weight:600; letter-spacing:2.2px; fill:{FERN}; fill-opacity:.85; }}
    .val {{ font-family:{SERIF}; font-size:18.5px; fill:{CREAM}; }}
    .valb{{ fill:{SAGE}; font-style:italic; }}
    .qt  {{ font-family:{SERIF}; font-size:16px; font-style:italic; fill:{SAGE}; }}
    .mt  {{ font-family:{MONO}; font-size:9.5px; letter-spacing:2.2px; fill:{SAGE}; fill-opacity:.7; }}
    .pk  {{ font-family:{MONO}; font-size:8.5px; letter-spacing:1px; fill:{GOLD}; fill-opacity:.75; }}
    .pl  {{ font-family:{MONO}; font-size:10px; font-weight:700; letter-spacing:2.2px; fill:{CREAM}; }}
    .ps  {{ font-family:{MONO}; font-size:9px; letter-spacing:1.2px; fill:{SAGE}; }}
    .sea {{ font-family:{SERIF}; font-size:13px; font-style:italic; letter-spacing:3px; fill:#7FB7B4; fill-opacity:.7; }}
    .wv  {{ fill:none; stroke:#5FA3A0; stroke-opacity:.35; stroke-width:.8; animation:wv 6s ease-in-out infinite alternate; }}
    @keyframes wv {{ from {{ transform:translateX(-4px); }} to {{ transform:translateX(4px); }} }}
    .rt  {{ fill:none; stroke:{GOLD}; stroke-width:2; stroke-linecap:round; stroke-dasharray:{L:.0f} {L:.0f};
            animation:draw 7s {EASE} infinite; }}
    @keyframes draw {{ 0% {{ stroke-dashoffset:{L:.0f}; opacity:1; }} 60% {{ stroke-dashoffset:0; opacity:1; }} 88% {{ stroke-dashoffset:0; opacity:0; }} 100% {{ stroke-dashoffset:{L:.0f}; opacity:0; }} }}
    .ring {{ fill:none; stroke:{GOLD}; transform-box:fill-box; transform-origin:center; animation:ring 2.8s ease-out infinite; }}
    @keyframes ring {{ from {{ transform:scale(.4); opacity:.9; }} to {{ transform:scale(2.6); opacity:0; }} }}
    .car {{ fill:{GOLD}; animation:blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 0%,50% {{ opacity:1; }} 51%,100% {{ opacity:0; }} }}
    {reduced(".wv,.rt,.ring,.car", ".ring { opacity:0; } .rt { stroke-dashoffset:0; }")}
  </style>

  <g clip-path="url(#ic)">
    <rect width="{W}" height="{H}" fill="url(#pg)"/>
    <rect width="{W}" height="{H}" fill="url(#pglow)"/>

    <!-- notes -->
    <text class="eb" x="56" y="66">FIELD NOTES  —  Nº 001</text>
    <text class="hi" x="54" y="124">Hi, I'm <tspan font-style="italic" fill="#FFD9A0">Aditya</tspan>.</text>
    {rowsvg}
    <text class="qt" x="56" y="{H - 44}">“Solitude in Silence.”</text>
    <rect class="car" x="56" y="{H - 30}" width="9" height="2"/>

    <!-- trail map -->
    <g clip-path="url(#mc)">
      <rect x="{MX0}" y="{MY0}" width="{MX1 - MX0}" height="{MY1 - MY0}" fill="url(#sea)"/>
      <g>{waves}</g>
      {contours(isle, "#173A2E", "1,603")}
      {contours(main, "#173A2E", "2,678")}
      <path d="{forest_glyphs}" fill="#5E9C72" fill-opacity=".5"/>
      <g stroke="{SAGE}" stroke-opacity=".08">{grid}</g>
      <text class="sea" transform="translate(760 190) rotate(-56)" text-anchor="middle">Salish Sea</text>

      <path d="{route}" fill="none" stroke="{GOLD}" stroke-opacity=".35" stroke-width="1.4" stroke-dasharray="2 5" stroke-linecap="round"/>
      <path class="rt" d="{route}"/>
      <circle r="3.4" fill="{CREAM}" filter="url(#pinglow)">
        <animateMotion dur="7s" repeatCount="indefinite" path="{route}" keyPoints="0;1;1" keyTimes="0;.6;1" calcMode="spline" keySplines=".16 1 .3 1;0 0 1 1"/>
        <animate attributeName="opacity" dur="7s" repeatCount="indefinite" values="1;1;0;0" keyTimes="0;.6;.88;1"/>
      </circle>

      <!-- pins -->
      <circle cx="{n(vic[0])}" cy="{n(vic[1])}" r="4.5" fill="#0A2226" stroke="{SAGE}" stroke-width="1.4"/>
      <circle cx="{n(vic[0])}" cy="{n(vic[1])}" r="1.6" fill="{SAGE}"/>
      <rect x="{n(vic[0] - 128)}" y="{n(vic[1] - 52)}" width="114" height="34" rx="5" fill="#081613" fill-opacity=".72" stroke="{SAGE}" stroke-opacity=".2"/>
      <text class="pl" x="{n(vic[0] - 118)}" y="{n(vic[1] - 37)}" fill="{SAGE}">VICTORIA</text>
      <text class="ps" x="{n(vic[0] - 118)}" y="{n(vic[1] - 24)}">UVic · B.Sc. CS</text>

      <circle class="ring" cx="{n(van[0])}" cy="{n(van[1])}" r="7"/>
      <circle class="ring" cx="{n(van[0])}" cy="{n(van[1])}" r="7" style="animation-delay:-1.4s"/>
      <circle cx="{n(van[0])}" cy="{n(van[1])}" r="5" fill="{GOLD}" filter="url(#pinglow)"/>
      <rect x="{n(van[0] - 126)}" y="{n(van[1] - 40)}" width="112" height="34" rx="5" fill="#081613" fill-opacity=".72" stroke="{GOLD}" stroke-opacity=".3"/>
      <text class="pl" x="{n(van[0] - 116)}" y="{n(van[1] - 25)}">VANCOUVER</text>
      <text class="ps" x="{n(van[0] - 116)}" y="{n(van[1] - 12)}">STEMCELL · now</text>

      <!-- compass + scale -->
      <g transform="translate({MX1 - 340} {MY0 + 40})">
        <circle r="15" fill="none" stroke="{SAGE}" stroke-opacity=".3"/>
        <path d="M0 -12 l4 12 l-4 -3 l-4 3z" fill="{GOLD}"/>
        <path d="M0 12 l4 -12 l-4 3 l-4 -3z" fill="{SAGE}" fill-opacity=".35"/>
        <text class="mt" y="-20" text-anchor="middle" fill="{GOLD}" fill-opacity=".9">N</text>
      </g>
      <g transform="translate({MX0 + 24} {MY1 - 22})">
        <path d="M0 0 h80 M0 -4 v8 M40 -3 v6 M80 -4 v8" stroke="{SAGE}" stroke-opacity=".6"/>
        <rect width="40" height="3" y="-1.5" fill="{SAGE}" fill-opacity=".5"/>
        <text class="mt" x="90" y="3.5">25 km</text>
      </g>
      <rect x="{MX0}" y="{MY0}" width="{MX1 - MX0}" height="{MY1 - MY0}" fill="url(#mapfade)"/>
    </g>
    <rect x="{MX0 + .5}" y="{MY0 + .5}" width="{MX1 - MX0 - 1}" height="{MY1 - MY0 - 1}" rx="12" fill="none" stroke="{SAGE}" stroke-opacity=".22"/>
    <text class="mt" x="{MX1 - 14}" y="{MY0 + 22}" text-anchor="end">TRAIL MAP · VICTORIA → VANCOUVER</text>

    {frame(W, H, 16, CREAM, ".12")}
  </g>
</svg>
"""


# ═════════════════════════════════════════════════════════════════════════════
# 4. CHAPTER II — THE RIVER
# ═════════════════════════════════════════════════════════════════════════════
def chapter_river():
    rnd = random.Random(1520)
    W, H, RY = 1000, 240, 172            # RY: waterline

    R1 = ridge(rnd, -20, W + 20, 132, 8, [(160, 70, 220), (360, 92, 200), (560, 50, 170)], iters=6)
    R2 = ridge(rnd, -20, W + 20, 154, 5, [(250, 14, 220), (640, 10, 200)], iters=5)
    R3 = ridge(rnd, -20, W + 20, RY + 2, 2, [], iters=4)
    snow = snowcap(rnd, R1, 82, (6, 20))

    def calm(x):                         # keep the trees low under the headline
        return .5 if x > 640 else 1
    t2 = treeline(rnd, R2, 10, 22, 6, sink=3, hscale=calm)
    t3 = treeline(rnd, R3, 22, 58, 8, sink=3, hscale=lambda x: .55 if x > 640 else 1)

    streaks = "".join(
        f'<rect class="st" x="{n(rnd.uniform(-160, W))}" y="{n(y)}" width="{n(rnd.uniform(18, 60) * (1 + (y - RY) / 40))}" '
        f'height="{n(.7 + (y - RY) / 70)}" rx=".6" fill-opacity="{rnd.uniform(.15, .45):.2f}" '
        f'style="animation-duration:{18 - (y - RY) / 6 + rnd.uniform(-2, 2):.1f}s;animation-delay:-{rnd.uniform(0, 20):.1f}s"/>'
        for y in [rnd.uniform(RY + 4, H - 2) for _ in range(46)])

    rocks = []
    for x, y, rx in [(300, 212, 18), (334, 218, 10), (520, 200, 12)]:
        rocks.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{rx * .42:.1f}" fill="#3B4C45"/><ellipse cx="{x - rx * .25:.1f}" cy="{y - rx * .15:.1f}" rx="{rx * .5:.1f}" ry="{rx * .16:.1f}" fill="#6E8379" fill-opacity=".7"/>'
                     f'<path d="M{x - rx * 1.1:.1f} {y + 1} q{rx * .4:.1f} -{rx * .5:.1f} {rx * .9:.1f} -{rx * .45:.1f}" fill="none" stroke="#FFF6E2" stroke-opacity=".7" stroke-width="1.1" stroke-linecap="round"/>'
                     f'<ellipse class="foam" cx="{x}" cy="{y + 2}" rx="{rx * 1.4:.1f}" ry="{rx * .45:.1f}" style="animation-delay:-{rnd.uniform(0, 3):.1f}s"/>')
    rocks = "".join(rocks)

    jump = "M600 214 Q640 132 690 210"
    glitter = "".join(
        f'<rect class="gl" x="{n(230 - w / 2 + rnd.uniform(-10, 10))}" y="{n(RY + 4 + i * 4.6)}" width="{n(w)}" height="1.2" rx=".6" '
        f'style="animation-delay:-{rnd.uniform(0, 2.4):.2f}s;animation-duration:{rnd.uniform(1.4, 2.8):.2f}s"/>'
        for i, w in enumerate([46, 40, 52, 34, 44, 30, 36, 24, 30, 18, 22, 14, 16, 10]))
    fish = "M-11 0 C-6 -4 4 -5 9 -1 L13 -4 L12 0 L13 4 L9 1 C4 5 -6 4 -11 0Z"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Waypoint two, the river: say hello">
  <title>Waypoint 02 · The River</title>
  <defs>
    <linearGradient id="rsky" x1="0" y1="0" x2="0" y2="{RY}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#F6D29E"/>
      <stop offset=".5"  stop-color="#F3CFA3"/>
      <stop offset="1"   stop-color="#D5DCC4"/>
    </linearGradient>
    <radialGradient id="rsun" cx="230" cy="70" r="420" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFF3D2"/>
      <stop offset=".2"  stop-color="#FFE3AE" stop-opacity=".6"/>
      <stop offset="1"   stop-color="#FFE3AE" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="m1" x1="0" y1="40" x2="0" y2="{RY}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#9FAFC2"/><stop offset="1" stop-color="#CFCDC2"/></linearGradient>
    <linearGradient id="water" x1="0" y1="{RY}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#E8CFA2"/>
      <stop offset=".35" stop-color="#7FA79C"/>
      <stop offset="1"   stop-color="#244A4A"/>
    </linearGradient>
    <linearGradient id="rdeep" x1="0" y1="{RY}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#173434" stop-opacity="0"/>
      <stop offset="1"   stop-color="#173434" stop-opacity=".6"/>
    </linearGradient>
    <linearGradient id="salmon" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#C2533F"/><stop offset="1" stop-color="#F08B6A"/>
    </linearGradient>
    {ripple_mask("rrm", H, W, RY, 4, 2.8)}
    <clipPath id="rclip"><rect y="{RY}" width="{W}" height="{H - RY}"/></clipPath>
    <clipPath id="rf"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .st   {{ fill:#FFF6E2; animation:flow linear infinite; }}
    @keyframes flow {{ from {{ transform:translateX(0); }} to {{ transform:translateX(1160px); }} }}
    .gl   {{ fill:#FFF3D0; animation:gl ease-in-out infinite; }}
    @keyframes gl {{ 0%,100% {{ opacity:.1; }} 50% {{ opacity:.9; }} }}
    .foam {{ fill:none; stroke:#FFF6E2; stroke-width:.9; transform-box:fill-box; transform-origin:center; animation:foam 3s ease-out infinite; }}
    @keyframes foam {{ from {{ transform:scale(.7); opacity:.8; }} to {{ transform:scale(1.5); opacity:0; }} }}
    .splash {{ fill:none; stroke:#FFF6E2; stroke-width:1; transform-box:fill-box; transform-origin:center; opacity:0; }}
    .s1 {{ animation:sp1 7s ease-out infinite; }}
    .s2 {{ animation:sp2 7s ease-out infinite; }}
    @keyframes sp1 {{ 0%,54% {{ transform:scale(.3); opacity:0; }} 55% {{ opacity:.9; }} 70%,100% {{ transform:scale(2.2); opacity:0; }} }}
    @keyframes sp2 {{ 0%,74% {{ transform:scale(.3); opacity:0; }} 75% {{ opacity:.9; }} 90%,100% {{ transform:scale(2.4); opacity:0; }} }}
    .gull {{ fill:none; stroke:#5A4A3A; stroke-width:1.3; stroke-linecap:round; animation:glide 36s linear infinite; }}
    @keyframes glide {{ from {{ transform:translate(-60px,0); }} to {{ transform:translate({W + 80}px,-24px); }} }}
    .k  {{ font-family:{MONO}; font-size:11px; letter-spacing:3px; fill:#9A5A2C; }}
    .h  {{ font-family:{SERIF}; font-size:48px; fill:#183A30; letter-spacing:-.5px; }}
    .s  {{ font-family:{SANS}; font-size:14px; letter-spacing:.4px; fill:#3C5A4C; }}
    .cue {{ animation:cue 2.4s ease-in-out infinite; }}
    @keyframes cue {{ 0%,100% {{ transform:translateY(-2px); opacity:.45; }} 50% {{ transform:translateY(3px); opacity:1; }} }}
    {reduced(".st,.gl,.foam,.s1,.s2,.gull,.cue,pattern", ".gull,.salmon { opacity:0; }")}
  </style>
  <g clip-path="url(#rf)">
    <rect width="{W}" height="{RY + 2}" fill="url(#rsky)"/>
    <rect width="{W}" height="{RY + 2}" fill="url(#rsun)"/>
    <g id="bank">
      <path d="{fill_under(R1, RY + 40)}" fill="url(#m1)"/>
      <path d="{snow}" fill="#FFF8EE" fill-opacity=".85"/>
      <path d="{fill_under(R2, RY + 40)}" fill="#7C9A84"/><path d="{t2}" fill="#7C9A84"/>
      <path d="{fill_under(R3, RY + 40)}" fill="#2E4C3E"/><path d="{t3}" fill="#2E4C3E"/>
    </g>
    <g class="gull"><g transform="translate(0,64)">{bird(0, 0, 1, 1.1, 0)}{bird(-18, 7, .8, 1.2, .4)}</g></g>

    <rect y="{RY}" width="{W}" height="{H - RY}" fill="url(#water)"/>
    <g clip-path="url(#rclip)" mask="url(#rrm)" opacity=".55">
      <use xlink:href="#bank" href="#bank" transform="matrix(1 0 0 -1 0 {2 * RY})"/>
    </g>
    <rect y="{RY}" width="{W}" height="{H - RY}" fill="url(#rdeep)"/>
    <g>{glitter}</g>
    <g>{streaks}</g>
    {rocks}

    <!-- a salmon running upstream -->
    <path class="salmon" d="{fish}" fill="url(#salmon)" opacity="0">
      <animateMotion dur="7s" repeatCount="indefinite" path="{jump}" rotate="auto" keyPoints="0;0;1;1" keyTimes="0;.55;.75;1" calcMode="linear"/>
      <animate attributeName="opacity" dur="7s" repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="0;.55;.56;.74;.75;1"/>
    </path>
    <ellipse class="splash s1" cx="600" cy="214" rx="8" ry="2.5"/>
    <ellipse class="splash s2" cx="690" cy="210" rx="8" ry="2.5"/>

    <text class="k" x="{W - 56}" y="50" text-anchor="end">WAYPOINT 02  —  15:20</text>
    <text class="h" x="{W - 54}" y="100" text-anchor="end">The <tspan font-style="italic" fill="#9A4E2A">River</tspan></text>
    <text class="s" x="{W - 74}" y="128" text-anchor="end">Elevation 120 m  ·  say hello</text>
    <g class="cue"><path d="M{W - 66} 119 l5 5 l5 -5" fill="none" stroke="#9A5A2C" stroke-width="1.4" stroke-linecap="round"/></g>

    {frame(W, H, 16, "#3C2A1A", ".18")}
  </g>
</svg>
"""


# ═════════════════════════════════════════════════════════════════════════════
# 5. TRAIL CARDS
# ═════════════════════════════════════════════════════════════════════════════
def card(kind, label, target, trail, dist, idx):
    rnd = random.Random(300 + idx)
    W, H = 340, 128

    if kind == "summit":
        bg = ("#2B2A4C", "#4A3A5E", "#B9746A")
        peak = f"M150 {H} L222 70 L246 84 L272 40 L300 66 L318 58 L360 {H}Z"
        cap = "M272 40 L262 58 L268 55 L274 62 L281 54 L289 60 L300 66 Z"
        scene = f"""
    <circle class="sunp" cx="300" cy="46" r="34" fill="url(#glow{idx})"/>
    <circle cx="300" cy="46" r="13" fill="#FFE2AE"/>
    <path d="M110 {H} L190 86 L214 98 L250 80 L300 104 L360 92 L360 {H}Z" fill="#6A5478" fill-opacity=".7"/>
    <path d="{peak}" fill="#2C2840"/>
    <path d="{cap}" fill="#F7E5EA"/>
    <path d="M272 40 v-16" stroke="#FFF4E2" stroke-width="1"/>
    <path fill="{EMBER}"><animate attributeName="d" dur="1.2s" repeatCount="indefinite"
      values="M272 24 q5 1 10 0 q-1 3 0 6 q-5 1 -10 0z;M272 24 q5 -2 10 1 q-1 3 0 6 q-5 -2 -10 -1z;M272 24 q5 1 10 0 q-1 3 0 6 q-5 1 -10 0z"/></path>
    {motes(rnd, 8, 190, 340, 20, 110, "#FFE2AE", 1.1)}"""
    elif kind == "forest":
        bg = ("#1C4636", "#123228", "#0B1F18")
        def stand(spec):
            return "".join(f'<g class="sw" style="animation-delay:-{rnd.uniform(0, 5):.1f}s"><path d="{fir(rnd, x, H + 4, h, .34)}"/></g>'
                           for x, h in spec)
        back = stand([(196, 58), (222, 74), (250, 66), (276, 82), (304, 70), (330, 86), (356, 64)])
        front = stand([(214, 92), (246, 118), (292, 132), (326, 104), (352, 124)])
        scene = f"""
    <circle cx="282" cy="48" r="70" fill="url(#glow{idx})"/>
    <g fill="#3F7D5E">{back}</g>
    <ellipse class="fogc" cx="270" cy="104" rx="130" ry="12" fill="url(#glow{idx})"/>
    <g fill="#0A1E16">{front}</g>
    {motes(rnd, 12, 190, 340, 30, 120, "#D9FF9E", 1.3)}"""
    else:  # river
        bg = ("#14404A", "#0E2E36", "#081C22")
        waves = "".join(
            f'<path class="wave" d="M160 {y} ' + " ".join(f"q10 -{a} 20 0 t20 0" for _ in range(12)) +
            f'" stroke-opacity="{op}" style="animation-duration:{d}s"/>'
            for y, a, op, d in [(78, 2.4, .25, 5), (92, 3, .35, 4.2), (106, 3.6, .5, 3.4), (120, 4.2, .65, 2.8)])
        scene = f"""
    <circle cx="300" cy="36" r="30" fill="url(#glow{idx})"/>
    <g fill="none" stroke="#9FE0D8" stroke-width="1.3" stroke-linecap="round">{waves}</g>
    <g class="boat">
      <path d="M244 92 h38 l-7 9 h-24z" fill="#FFF4E2"/>
      <path d="M262 92 v-22 l-14 22z" fill="#FFF4E2" fill-opacity=".9"/>
      <path d="M264 92 v-18 l11 18z" fill="#F4C27A"/>
    </g>"""

    glowc = {"summit": "#FFD39A", "forest": "#E8F6EA", "river": "#9FE0D8"}[kind]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{label} — {target}">
  <title>{label} — {target}</title>
  <defs>
    <linearGradient id="bg{idx}" x1="0" y1="0" x2=".4" y2="1">
      <stop offset="0"  stop-color="{bg[0]}"/>
      <stop offset=".6" stop-color="{bg[1]}"/>
      <stop offset="1"  stop-color="{bg[2]}"/>
    </linearGradient>
    <radialGradient id="glow{idx}" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="{glowc}" stop-opacity=".55"/>
      <stop offset="1" stop-color="{glowc}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="scrim{idx}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0"   stop-color="{bg[2] if kind != 'summit' else '#1E1C36'}" stop-opacity=".92"/>
      <stop offset=".5"  stop-color="{bg[2] if kind != 'summit' else '#1E1C36'}" stop-opacity=".55"/>
      <stop offset=".75" stop-color="{bg[2] if kind != 'summit' else '#1E1C36'}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="cc{idx}"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  </defs>
  <style>
    .tg {{ font-family:{MONO}; font-size:9.5px; letter-spacing:2.6px; fill:{GOLD}; }}
    .ds {{ font-family:{MONO}; font-size:9.5px; letter-spacing:1.6px; fill:{CREAM}; fill-opacity:.5; }}
    .lb {{ font-family:{SERIF}; font-size:30px; fill:{CREAM}; letter-spacing:-.3px; }}
    .tx {{ font-family:{MONO}; font-size:11.5px; letter-spacing:.3px; fill:{SAGE}; }}
    .ar {{ animation:ar 2.6s ease-in-out infinite; }}
    @keyframes ar {{ 0%,100% {{ transform:translate(0,0); }} 50% {{ transform:translate(2px,-2px); }} }}
    .sunp {{ transform-box:fill-box; transform-origin:center; animation:sunp 5s ease-in-out infinite; }}
    @keyframes sunp {{ 0%,100% {{ transform:scale(1); opacity:.7; }} 50% {{ transform:scale(1.2); opacity:1; }} }}
    .sw {{ transform-box:fill-box; transform-origin:50% 100%; animation:sw 5s ease-in-out infinite alternate; }}
    @keyframes sw {{ from {{ transform:rotate(-1.4deg); }} to {{ transform:rotate(1.4deg); }} }}
    .fogc {{ animation:fogc 12s ease-in-out infinite alternate; }}
    @keyframes fogc {{ from {{ transform:translateX(-30px); }} to {{ transform:translateX(30px); }} }}
    .wave {{ animation:wave linear infinite; }}
    @keyframes wave {{ from {{ transform:translateX(0); }} to {{ transform:translateX(40px); }} }}
    .boat {{ transform-box:fill-box; transform-origin:50% 100%; animation:boat 4s ease-in-out infinite; }}
    @keyframes boat {{ 0%,100% {{ transform:translateY(0) rotate(-3deg); }} 50% {{ transform:translateY(3px) rotate(3deg); }} }}
    {MOTE_CSS}
    {reduced(".ar,.sunp,.sw,.fogc,.wave,.boat,.mote", ".mote { opacity:0; }")}
  </style>
  <g clip-path="url(#cc{idx})">
    <rect width="{W}" height="{H}" fill="url(#bg{idx})"/>
    {scene}
    <rect width="{W}" height="{H}" fill="url(#scrim{idx})"/>

    <text class="tg" x="24" y="32">{trail}</text>
    <text class="ds" x="24" y="32" dx="{len(trail) * 8.6 + 6:.0f}">· {dist}</text>
    <text class="lb" x="22" y="78">{label}</text>
    <text class="tx" x="24" y="102">{target}</text>

    <g class="ar">
      <circle cx="{W - 28}" cy="28" r="12" fill="#000" fill-opacity=".18" stroke="{CREAM}" stroke-opacity=".45"/>
      <path d="M{W - 32} 32 l8 -8 M{W - 30} 24 h6 v6" fill="none" stroke="{CREAM}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    </g>
    {frame(W, H, 14, CREAM, ".2")}
  </g>
</svg>
"""


# ═════════════════════════════════════════════════════════════════════════════
# 6. CAMP — NIGHT
# ═════════════════════════════════════════════════════════════════════════════
def camp():
    rnd = random.Random(2247)
    W, H, HZ = 1000, 340, 254

    M1 = ridge(rnd, -20, W + 20, 214, 10, [(120, 74, 220), (430, 96, 240), (760, 60, 200), (930, 88, 220)], iters=7)
    M2 = ridge(rnd, -20, W + 20, 238, 6, [(280, 40, 240), (640, 30, 220)], iters=6)
    M3 = ridge(rnd, -20, W + 20, HZ + 1, 2, [], iters=4)
    t2 = treeline(rnd, M2, 8, 18, 5, sink=3)
    t3 = treeline(rnd, M3, 14, 40, 7, sink=3, hscale=lambda x: .45 if 150 < x < 280 else 1)
    snow = snowcap(rnd, M1, 150, (5, 16))

    stars = []
    for _ in range(190):
        x, y = rnd.uniform(0, W), rnd.uniform(0, HZ - 40) ** 1.0
        r = rnd.choice([.4, .5, .6, .7, .8, 1.0, 1.3])
        if rnd.random() < .4:
            d = rnd.uniform(2.5, 6)
            stars.append(f'<circle class="tw" cx="{n(x)}" cy="{n(y)}" r="{r}" style="animation-duration:{d:.1f}s;animation-delay:-{rnd.uniform(0, d):.1f}s"/>')
        else:
            stars.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill-opacity="{rnd.uniform(.3, .9):.2f}"/>')
    # milky way: a dense diagonal band of fine stars
    for _ in range(220):
        t = rnd.uniform(0, 1)
        x = -40 + t * 1100
        y = 96 + (x - 520) * -.2126 + rnd.gauss(0, 20)
        if 0 < y < HZ - 30:
            stars.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{rnd.choice([.3, .4, .5])}" fill-opacity="{rnd.uniform(.25, .7):.2f}"/>')
    stars = "".join(stars)

    def curtain(base, amp, h, phase, k):
        top = [(x, base - h + amp * .6 * math.sin(x / 140 + phase + k)) for x in range(-40, W + 80, 40)]
        bot = [(x, base + amp * math.sin(x / 110 + phase * 1.3 + k * .8)) for x in range(-40, W + 80, 40)]
        return smooth(top)[0:] + " L" + " L".join(P(x, y) for x, y in reversed(bot)) + "Z"

    auroras = []
    for i, (base, amp, h, ph, gid, dur) in enumerate([(128, 22, 80, 0, "a1", 14), (104, 18, 62, 2, "a2", 18), (150, 14, 46, 4, "a3", 11)]):
        frames = [curtain(base, amp, h, ph, k) for k in (0, 1.6, 3.1, 0)]
        auroras.append(f'<path fill="url(#{gid})" d="{frames[0]}"><animate attributeName="d" dur="{dur}s" repeatCount="indefinite" '
                       f'values="{";".join(frames)}" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1"/></path>')
    auroras = "".join(auroras)

    # campfire and tent on the far-left shore
    FX, FY = 214, HZ + 8
    flames = []
    for dx, h, w, col, dur in [(-3, 18, 7, EMBER, .7), (2, 24, 8, "#FFB257", .55), (0, 14, 5, "#FFE6A8", .45)]:
        a = f"M{FX + dx - w} {FY} Q{FX + dx - w * .6} {FY - h * .5} {FX + dx} {FY - h} Q{FX + dx + w * .6} {FY - h * .5} {FX + dx + w} {FY}Z"
        b = f"M{FX + dx - w} {FY} Q{FX + dx - w * .9} {FY - h * .6} {FX + dx + 3} {FY - h * 1.15} Q{FX + dx + w * .3} {FY - h * .4} {FX + dx + w} {FY}Z"
        c = f"M{FX + dx - w} {FY} Q{FX + dx - w * .2} {FY - h * .4} {FX + dx - 3} {FY - h * .9} Q{FX + dx + w} {FY - h * .55} {FX + dx + w} {FY}Z"
        flames.append(f'<path fill="{col}" d="{a}"><animate attributeName="d" dur="{dur}s" repeatCount="indefinite" values="{a};{b};{c};{a}"/></path>')
    flames = "".join(flames)
    sparks = "".join(
        f'<circle class="spark" cx="{n(FX + rnd.uniform(-4, 4))}" cy="{FY - 12}" r="{n(rnd.uniform(.6, 1.3))}" '
        f'style="animation-duration:{rnd.uniform(1.8, 3.4):.1f}s;animation-delay:-{rnd.uniform(0, 3.4):.1f}s;--dx:{rnd.uniform(-14, 14):.0f}px"/>'
        for _ in range(16))
    flies = motes(rnd, 14, 300, 980, HZ - 50, HZ + 60, "#D8FF8A", 1.3, cls="fly")
    fire_glints = "".join(
        f'<rect class="glint" x="{n(FX - w / 2 + rnd.uniform(-3, 3))}" y="{n(HZ + 8 + i * 5.5)}" width="{n(w)}" height="1.4" rx=".7" '
        f'style="animation-delay:-{rnd.uniform(0, 2):.2f}s"/>'
        for i, w in enumerate([22, 18, 26, 14, 16, 10, 12, 6, 8, 5]))

    fg = "".join(f'<path d="{fir(rnd, x, b, h, .3)}"/>' for x, b, h in [(-24, H + 20, 300), (40, H + 20, 210), (968, H + 20, 260), (1020, H + 20, 330), (912, H + 20, 150)])
    shore = smooth([(-20, HZ + 2), (120, HZ + 6), (260, HZ + 3), (400, HZ + 2)]) + f" L400 {HZ} L-20 {HZ}Z"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="I am Aditya Padmarajan. A camp at an alpine lake under the aurora.">
  <title>I am Aditya Padmarajan</title>
  <defs>
    <linearGradient id="nsky" x1="0" y1="0" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#03060F"/>
      <stop offset=".55" stop-color="#0A1631"/>
      <stop offset="1"   stop-color="#173A4E"/>
    </linearGradient>
    <radialGradient id="milky" cx="50%" cy="50%" r="50%">
      <stop offset="0"   stop-color="#C9C2FF" stop-opacity=".2"/>
      <stop offset=".55" stop-color="#9F96E8" stop-opacity=".08"/>
      <stop offset="1"   stop-color="#9F96E8" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="a1" x1="0" y1="40" x2="0" y2="160" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="{LILAC}" stop-opacity="0"/>
      <stop offset=".45" stop-color="#58E0C0" stop-opacity=".22"/>
      <stop offset="1"   stop-color="{AURORA}" stop-opacity=".62"/>
    </linearGradient>
    <linearGradient id="a2" x1="0" y1="30" x2="0" y2="130" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="{LILAC}" stop-opacity="0"/>
      <stop offset=".6"  stop-color="{LILAC}" stop-opacity=".22"/>
      <stop offset="1"   stop-color="#7CF7D0" stop-opacity=".45"/>
    </linearGradient>
    <linearGradient id="a3" x1="0" y1="100" x2="0" y2="170" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="{AURORA}" stop-opacity="0"/>
      <stop offset="1"   stop-color="#B6FFE0" stop-opacity=".5"/>
    </linearGradient>
    <filter id="soft" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="5"/></filter>
    <linearGradient id="mt1" x1="0" y1="120" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#14263D"/><stop offset="1" stop-color="#0E1C2E"/></linearGradient>
    <linearGradient id="nlake" x1="0" y1="{HZ}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#173A4E"/>
      <stop offset="1"   stop-color="#050B14"/>
    </linearGradient>
    <radialGradient id="fireglow" cx="{FX}" cy="{FY - 6}" r="150" gradientUnits="userSpaceOnUse">
      <stop offset="0"   stop-color="#FFB25A" stop-opacity=".55"/>
      <stop offset=".35" stop-color="#F2794A" stop-opacity=".18"/>
      <stop offset="1"   stop-color="#F2794A" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="tent" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFC27A"/><stop offset="1" stop-color="#C9632F"/>
    </linearGradient>
    <linearGradient id="shoot" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/>
    </linearGradient>
    {ripple_mask("nrm", H, W, HZ, 4, 2.8)}
    <clipPath id="nlc"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>
    <clipPath id="nf"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    .tw {{ animation:tw ease-in-out infinite; }}
    @keyframes tw {{ 0%,100% {{ opacity:.2; }} 50% {{ opacity:1; }} }}
    .shoot {{ animation:shoot 11s ease-in infinite; }}
    @keyframes shoot {{ 0%,86% {{ transform:translate(0,0); opacity:0; }} 87% {{ opacity:1; }} 94%,100% {{ transform:translate(-260px,120px); opacity:0; }} }}
    .spark {{ fill:#FFC679; animation:spark ease-out infinite; }}
    @keyframes spark {{ from {{ transform:translate(0,0); opacity:1; }} to {{ transform:translate(var(--dx),-70px); opacity:0; }} }}
    .glow {{ animation:flick 1.8s ease-in-out infinite; }}
    @keyframes flick {{ 0%,100% {{ opacity:.85; }} 30% {{ opacity:1; }} 55% {{ opacity:.7; }} 75% {{ opacity:.95; }} }}
    .glint {{ fill:#FFB866; animation:glint 1.6s ease-in-out infinite; }}
    @keyframes glint {{ 0%,100% {{ opacity:.15; }} 50% {{ opacity:.85; }} }}
    .fly {{ animation:fly ease-in-out infinite; }}
    @keyframes fly {{ 0%,100% {{ transform:translate(0,0); opacity:0; }} 25% {{ opacity:.95; }} 50% {{ transform:translate(14px,-10px); opacity:.2; }} 75% {{ transform:translate(-8px,-18px); opacity:.9; }} }}
    .t  {{ font-family:{SERIF}; font-size:38px; fill:{CREAM}; letter-spacing:-.3px; }}
    .m  {{ font-family:{MONO}; font-size:10.5px; letter-spacing:2.8px; fill:#9FD8C4; fill-opacity:.75; }}
    .up {{ font-family:{MONO}; font-size:10.5px; letter-spacing:2.8px; fill:{GOLD}; }}
    .cue {{ animation:cue 2.4s ease-in-out infinite; }}
    @keyframes cue {{ 0%,100% {{ transform:translateY(2px); opacity:.5; }} 50% {{ transform:translateY(-3px); opacity:1; }} }}
    {reduced(".tw,.shoot,.spark,.glow,.glint,.fly,.cue,pattern", ".shoot,.spark,.fly { opacity:0; }")}
  </style>
  <g clip-path="url(#nf)">
    <g id="night">
      <rect width="{W}" height="{HZ + 2}" fill="url(#nsky)"/>
      <ellipse cx="520" cy="96" rx="620" ry="62" fill="url(#milky)" transform="rotate(-12 520 96)"/>
      <g fill="#FFFFFF">{stars}</g>
      <g filter="url(#soft)">{auroras}</g>
      <path d="{fill_under(M1, HZ + 30)}" fill="url(#mt1)"/>
      <path d="{line_of(M1)}" fill="none" stroke="{AURORA}" stroke-opacity=".22" stroke-width="1.2"/>
      <path d="{snow}" fill="#CFE9F0" fill-opacity=".35"/>
      <path d="{fill_under(M2, HZ + 30)}" fill="#0A1626"/><path d="{t2}" fill="#0A1626"/>
      <path d="{fill_under(M3, HZ + 30)}" fill="#060D16"/><path d="{t3}" fill="#060D16"/>
    </g>

    <!-- a shooting star, now and then -->
    <g class="shoot"><path d="M760 40 l120 -55" stroke="url(#shoot)" stroke-width="1.4" transform="rotate(180 820 12)"/></g>
    <g class="shoot" style="animation-duration:17s;animation-delay:-6s"><path d="M380 30 l90 -40" stroke="url(#shoot)" stroke-width="1.1" transform="rotate(180 425 10)"/></g>

    <!-- lake -->
    <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#nlake)"/>
    <g clip-path="url(#nlc)" mask="url(#nrm)" opacity=".5">
      <use xlink:href="#night" href="#night" transform="matrix(1 0 0 -1 0 {2 * HZ})"/>
    </g>
    <g>{fire_glints}</g>

    <!-- camp -->
    <path d="{shore}" fill="#060D16"/>
    <rect class="glow" width="{W}" height="{H}" fill="url(#fireglow)"/>
    <g transform="translate(150 {HZ + 8})">
      <path d="M-26 0 L0 -36 L26 0Z" fill="url(#tent)" class="glow"/>
      <path d="M0 -36 L-4 0 h8z" fill="#7A2E14" fill-opacity=".8"/>
      <path d="M-26 0 L0 -36 L26 0" fill="none" stroke="#2A140A" stroke-width="1.4" stroke-linejoin="round"/>
      <path d="M0 -36 l-4 -5 M0 -36 l4 -5" stroke="#2A140A"/>
    </g>
    <path d="M{FX - 10} {FY + 1} l20 -5 M{FX - 10} {FY - 4} l20 5" stroke="#3A1E10" stroke-width="3" stroke-linecap="round"/>
    <g>{flames}</g>
    {sparks}
    {flies}
    <g fill="#03070C">{fg}</g>

    <!-- sign-off -->
    <text class="m" x="560" y="74" text-anchor="middle"></text>
    <text class="t" x="{W / 2}" y="80" text-anchor="middle">I am <tspan font-style="italic" fill="#B9FBE0">Aditya Padmarajan</tspan>.</text>

    <text class="m" x="96" y="{H - 22}" fill-opacity=".45"></text>

    {frame(W, H, 18, AURORA, ".18")}
  </g>
</svg>
"""


# ═════════════════════════════════════════════════════════════════════════════
# NIGHT EDITION — one clear night at an alpine lake, told in four panels
#
#   night-hero      aurora storm over the lake, a fire, someone watching it
#   night-notes     field notes by firelight, each one a star in a constellation
#   night-card-*    three ways to reach me: summit, forest, lantern on the lake
#   night-footer    the fire, still going
#
# Shared: one sky gradient, one star palette, one aurora, one frame. Every
# panel ends in the same black treeline so they read as one continuous scene.
# ═════════════════════════════════════════════════════════════════════════════
MINT   = "#B9FBE0"
FROST  = "#DDEBFF"
SKY_STOPS = [(0, "#01030A"), (.45, "#060E26"), (.8, "#0D2240"), (1, "#173A55")]
STAR_COLS = ["#FFFFFF"] * 7 + ["#CFE3FF", "#FFE9C7", "#E2DAFF"]


def sky_grad(gid, y0, y1):
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in SKY_STOPS)
    return f'<linearGradient id="{gid}" x1="0" y1="{y0}" x2="0" y2="{y1}" gradientUnits="userSpaceOnUse">{stops}</linearGradient>'


def dots(points):
    """Many tiny stars as a single path of circles — far smaller than <circle> soup."""
    return "".join(f"M{n(x - r)} {n(y)}a{n(r)} {n(r)} 0 1 0 {n(2 * r)} 0a{n(r)} {n(r)} 0 1 0 {n(-2 * r)} 0" for x, y, r in points)


def starfield(rnd, W, y0, y1, count, tw=.35, avoid=None):
    out, still = [], {.3: [], .55: [], .85: []}
    for _ in range(count):
        x, y = rnd.uniform(0, W), y0 + (y1 - y0) * rnd.random() ** 1.25
        if avoid and avoid(x, y) and rnd.random() < .7:
            continue
        r = rnd.choice([.35, .45, .55, .65, .8, .95, 1.15])
        if rnd.random() < tw:
            d = rnd.uniform(2.5, 7.5)
            out.append(f'<circle class="tw" cx="{n(x)}" cy="{n(y)}" r="{r}" fill="{rnd.choice(STAR_COLS)}" '
                       f'style="animation-duration:{d:.1f}s;animation-delay:-{rnd.uniform(0, d):.1f}s"/>')
        else:
            still[rnd.choice([.3, .55, .85])].append((x, y, r))
    out += [f'<path fill="#fff" fill-opacity="{o}" d="{dots(p)}"/>' for o, p in still.items() if p]
    return "".join(out)


def bright_star(x, y, s, col, d, delay):
    return (f'<g transform="translate({n(x)} {n(y)}) scale({s})"><g class="tw" style="animation-duration:{d}s;animation-delay:-{delay}s">'
            f'<circle r="7" fill="url(#bstar)"/>'
            f'<path d="M-11 0H11M0 -11V11" stroke="{col}" stroke-width=".45" stroke-opacity=".75"/>'
            f'<path d="M-4 -4L4 4M-4 4L4 -4" stroke="{col}" stroke-width=".35" stroke-opacity=".4"/>'
            f'<circle r="1.25" fill="#fff"/></g></g>')


def aurora(rnd, x0, x1, base, hgt, step, grad, glow=True):
    """A curtain: hundreds of vertical rays standing on a folding lower edge.
    The lower edge is sharp and bright, the rays fade upward into violet,
    which is how the real thing looks from the ground."""
    groups, x = [[], [], [], []], x0
    while x < x1:
        b, h = base(x), max(18, hgt(x) * rnd.uniform(.72, 1.18))
        w = step * rnd.uniform(1.1, 2.3)
        groups[rnd.randrange(4)].append(
            f'<rect x="{n(x)}" y="{n(b - h)}" width="{n(w)}" height="{n(h + 2)}" fill-opacity="{rnd.uniform(.22, .8):.2f}"/>')
        x += step * rnd.uniform(.7, 1.3)
    rays = "".join(f'<g class="rp" style="animation-duration:{rnd.uniform(2.6, 6.5):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s">{"".join(g)}</g>'
                   for g in groups)
    xs = list(range(int(x0), int(x1) + 12, 12))
    edge = smooth([(x, base(x) + 1) for x in xs])
    out = ""
    if glow:
        body = smooth([(x, base(x) - hgt(x) * .75) for x in xs]) + " L" + " L".join(P(x, base(x) + 6) for x in reversed(xs)) + "Z"
        out += f'<path d="{body}" fill="url(#{grad})" opacity=".55" filter="url(#ablur)"/>'
    out += f'<g fill="url(#{grad})" filter="url(#rsoft)">{rays}</g>'
    out += f'<path d="{edge}" fill="none" stroke="#D9FFEF" stroke-opacity=".38" stroke-width="1.1"/>'
    out += f'<path d="{edge}" fill="none" stroke="{AURORA}" stroke-opacity=".3" stroke-width="5" filter="url(#ablur2)"/>'
    return out


def aurora_defs():
    return f"""<linearGradient id="ray1" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0"   stop-color="#E4FFF4" stop-opacity=".95"/>
      <stop offset=".05" stop-color="#7CFFC8" stop-opacity=".85"/>
      <stop offset=".32" stop-color="#34D6A0" stop-opacity=".38"/>
      <stop offset=".68" stop-color="#7C6BFF" stop-opacity=".16"/>
      <stop offset="1"   stop-color="#C26BFF" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="ray2" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0"   stop-color="#B8FFE6" stop-opacity=".7"/>
      <stop offset=".1"  stop-color="#4FE3B8" stop-opacity=".5"/>
      <stop offset=".5"  stop-color="#B07CFF" stop-opacity=".22"/>
      <stop offset="1"   stop-color="#FF7FD0" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="asw" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1000" y2="0">
      <stop offset="0" stop-color="#bdbdbd"/><stop offset=".38" stop-color="#bdbdbd"/>
      <stop offset=".5" stop-color="#fff"/>
      <stop offset=".62" stop-color="#bdbdbd"/><stop offset="1" stop-color="#bdbdbd"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-1000 0;1000 0" dur="11s" repeatCount="indefinite"/>
    </linearGradient>
    <mask id="am" maskUnits="userSpaceOnUse" x="-200" y="-200" width="1400" height="900"><rect x="-200" y="-200" width="1400" height="900" fill="url(#asw)"/></mask>
    <filter id="ablur" x="-10%" y="-30%" width="120%" height="160%"><feGaussianBlur stdDeviation="9"/></filter>
    <filter id="rsoft" x="-2%" y="-2%" width="104%" height="104%"><feGaussianBlur stdDeviation="1.6 0"/></filter>
    <filter id="ablur2" x="-10%" y="-100%" width="120%" height="300%"><feGaussianBlur stdDeviation="3"/></filter>
    <radialGradient id="bstar"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".3" stop-color="#CFE3FF" stop-opacity=".15"/><stop offset="1" stop-color="#CFE3FF" stop-opacity="0"/></radialGradient>"""


def campfire(rnd, FX, FY, s=1.0, sparks=18):
    out = []
    out.append(f'<ellipse class="glow" cx="{n(FX)}" cy="{n(FY)}" rx="{n(15 * s)}" ry="{n(3.2 * s)}" fill="{EMBER}" fill-opacity=".85"/>')
    out.append(f'<path d="M{n(FX - 15 * s)} {n(FY + 1)} l{n(30 * s)} {n(-6 * s)} M{n(FX - 15 * s)} {n(FY - 5 * s)} l{n(30 * s)} {n(6 * s)}" '
               f'stroke="#2A1408" stroke-width="{n(3.8 * s)}" stroke-linecap="round"/>')
    for dx, h, w, col, dur in [(-5, 22, 8, EMBER, .72), (3, 31, 9, "#FFB257", .56), (-1, 21, 6, "#FFE6A8", .46), (1, 11, 3.5, "#FFFBEA", .38)]:
        dx, h, w = dx * s, h * s, w * s
        X, Y = FX + dx, FY - 2 * s
        a = f"M{n(X - w)} {n(Y)} Q{n(X - w * .6)} {n(Y - h * .5)} {n(X)} {n(Y - h)} Q{n(X + w * .6)} {n(Y - h * .5)} {n(X + w)} {n(Y)}Z"
        b = f"M{n(X - w)} {n(Y)} Q{n(X - w * .9)} {n(Y - h * .6)} {n(X + 3 * s)} {n(Y - h * 1.15)} Q{n(X + w * .3)} {n(Y - h * .4)} {n(X + w)} {n(Y)}Z"
        c = f"M{n(X - w)} {n(Y)} Q{n(X - w * .2)} {n(Y - h * .4)} {n(X - 3 * s)} {n(Y - h * .9)} Q{n(X + w)} {n(Y - h * .55)} {n(X + w)} {n(Y)}Z"
        out.append(f'<path fill="{col}" d="{a}"><animate attributeName="d" dur="{dur}s" repeatCount="indefinite" values="{a};{b};{c};{a}"/></path>')
    for _ in range(sparks):
        d = rnd.uniform(1.8, 3.6)
        out.append(f'<circle class="sp{rnd.choice("abc")}" cx="{n(FX + rnd.uniform(-5, 5) * s)}" cy="{n(FY - 14 * s)}" r="{n(rnd.uniform(.6, 1.4) * s)}" '
                   f'style="animation-duration:{d:.1f}s;animation-delay:-{rnd.uniform(0, d):.1f}s"/>')
    for i in range(3):
        out.append(f'<path class="smoke" d="M{n(FX)} {n(FY - 34 * s)} q{n(-7 * s)} {n(-14 * s)} 0 {n(-28 * s)} q{n(7 * s)} {n(-14 * s)} 0 {n(-28 * s)}" '
                   f'fill="none" stroke="#B4BFD0" stroke-opacity=".07" stroke-width="{n(8 * s)}" stroke-linecap="round" filter="url(#ablur2)" '
                   f'style="animation-delay:-{i * 2.2:.1f}s"/>')
    return "".join(out)


def night_css(extra=""):
    return f"""
    .tw {{ animation:tw ease-in-out infinite; }}
    @keyframes tw {{ 0%,100% {{ opacity:.22; }} 50% {{ opacity:1; }} }}
    .rp {{ animation:rp ease-in-out infinite; }}
    @keyframes rp {{ 0%,100% {{ opacity:.5; }} 35% {{ opacity:1; }} 65% {{ opacity:.68; }} }}
    .sway {{ transform-box:fill-box; transform-origin:50% 100%; animation:sway ease-in-out infinite alternate; }}
    @keyframes sway {{ from {{ transform:translateX(-16px) skewX(-3deg); }} to {{ transform:translateX(16px) skewX(3deg); }} }}
    .grow {{ transform-box:fill-box; transform-origin:50% 100%; animation:grow 5.5s {EASE} both; }}
    @keyframes grow {{ from {{ opacity:0; transform:scaleY(.25); }} to {{ opacity:1; transform:none; }} }}
    .in {{ animation:rise 2.4s {EASE} both; }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(14px); }} to {{ opacity:1; transform:none; }} }}
    .fade {{ animation:fade 3.5s ease-out both; }}
    @keyframes fade {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
    .glow {{ animation:flick 1.8s ease-in-out infinite; }}
    @keyframes flick {{ 0%,100% {{ opacity:.85; }} 30% {{ opacity:1; }} 55% {{ opacity:.7; }} 75% {{ opacity:.95; }} }}
    .spa,.spb,.spc {{ fill:#FFC679; animation:ease-out infinite; }}
    .spa {{ animation-name:spa; }} .spb {{ animation-name:spb; }} .spc {{ animation-name:spc; }}
    @keyframes spa {{ from {{ transform:translate(0,0); opacity:1; }} to {{ transform:translate(-14px,-80px); opacity:0; }} }}
    @keyframes spb {{ from {{ transform:translate(0,0); opacity:1; }} to {{ transform:translate(4px,-95px); opacity:0; }} }}
    @keyframes spc {{ from {{ transform:translate(0,0); opacity:1; }} to {{ transform:translate(18px,-70px); opacity:0; }} }}
    .smoke {{ transform-box:fill-box; transform-origin:50% 100%; animation:smoke 6.6s ease-out infinite; }}
    @keyframes smoke {{ 0% {{ opacity:0; transform:translate(0,0) scale(.6); }} 25% {{ opacity:1; }} 100% {{ opacity:0; transform:translate(22px,-60px) scale(1.7); }} }}
    .gl {{ animation:gl ease-in-out infinite; }}
    @keyframes gl {{ 0%,100% {{ opacity:.12; }} 50% {{ opacity:.9; }} }}
    .fly {{ animation:fly ease-in-out infinite; }}
    @keyframes fly {{ 0%,100% {{ transform:translate(0,0); opacity:0; }} 25% {{ opacity:.95; }} 50% {{ transform:translate(14px,-10px); opacity:.15; }} 75% {{ transform:translate(-8px,-18px); opacity:.9; }} }}
    .mist {{ animation:mist ease-in-out infinite alternate; }}
    @keyframes mist {{ from {{ transform:translateX(-50px); }} to {{ transform:translateX(50px); }} }}
    .shoot {{ animation:shoot 13s ease-in infinite; }}
    @keyframes shoot {{ 0%,88% {{ transform:translate(0,0); opacity:0; }} 89% {{ opacity:1; }} 95%,100% {{ transform:translate(-300px,130px); opacity:0; }} }}
    .k  {{ font-family:{MONO}; font-size:10.5px; letter-spacing:3.2px; fill:{MINT}; fill-opacity:.7; }}
    {extra}
    {reduced(".tw,.rp,.sway,.grow,.in,.fade,.glow,.spa,.spb,.spc,.smoke,.gl,.fly,.mist,.shoot,.sat,.cue,.draw,.ign,.bob,.ar,.breathe,.hair,.steam,pattern",
             ".spa,.spb,.spc,.fly,.shoot,.sat,.smoke { opacity:0; } .draw { stroke-dashoffset:0 !important; }")}"""


def edge_trees(rnd, W, H, y, hmin, hmax, gap, fill="#02050A"):
    rid = ridge(rnd, -20, W + 20, y, 3, [], iters=6)
    return f'<path d="{fill_under(rid, H + 2)}" fill="{fill}"/><path d="{treeline(rnd, rid, hmin, hmax, gap, sink=4)}" fill="{fill}"/>'


# ─── hero ────────────────────────────────────────────────────────────────────
def night_hero():
    rnd = random.Random(4711)
    W, H, HZ = 1000, 540, 372

    in_text = lambda x, y: 150 < x < 850 and 50 < y < 195
    stars = starfield(rnd, W, 0, HZ - 30, 300, avoid=in_text)

    # milky way, rising left to right behind everything
    slope, c0 = -.27, 262
    my = lambda x: c0 + slope * x
    band = [(x, my(x) + rnd.gauss(0, 22), rnd.choice([.3, .35, .45, .55])) for x in (rnd.uniform(-20, W + 20) for _ in range(900))]
    band = [p for p in band if 0 < p[1] < HZ - 40]
    milky = "".join(f'<path fill="#fff" fill-opacity="{o}" d="{dots(band[i::3])}"/>' for i, o in enumerate([.25, .4, .6]))
    lane = smooth([(x, my(x) + 5 + 7 * math.sin(x / 70)) for x in range(-20, W + 40, 40)])
    ang = math.degrees(math.atan(slope))

    brights = "".join(bright_star(x, y, s, c, d, dl) for x, y, s, c, d, dl in [
        (64, 52, 1.1, FROST, 4.2, 1), (236, 26, .8, "#FFE9C7", 5.5, 3), (118, 228, .7, FROST, 3.6, 2),
        (930, 214, .9, "#E2DAFF", 4.8, 0), (744, 26, .75, FROST, 6, 4), (40, 300, .6, "#FFE9C7", 3.4, 1.5)])

    # three curtains: a high violet one, the main storm, a low bright fold
    c2 = aurora(rnd, -40, W + 40, lambda x: 196 + 18 * math.sin(x / 190 + 2.2) + 7 * math.sin(x / 71),
                lambda x: 70 + 60 * math.sin(x / 230 + 1) ** 2, 4.2, "ray2")
    c1 = aurora(rnd, -40, W + 40, lambda x: 238 + 24 * math.sin(x / 160 + .6) + 9 * math.sin(x / 57 + 1.3),
                lambda x: 80 + 100 * math.sin(x / 210 + 2) ** 2, 3, "ray1")
    c3 = aurora(rnd, 480, W + 40, lambda x: 268 + 14 * math.sin(x / 90 + .4),
                lambda x: 40 + 40 * math.sin(x / 120) ** 2, 3, "ray1")
    curtains = "".join(
        f'<g class="grow" style="animation-delay:{dl}s"><g class="sway" mask="url(#am)" opacity="{op}" style="animation-duration:{dur}s">{c}</g></g>'
        for c, op, dur, dl in [(c2, .6, 21, .4), (c1, 1, 16, 0), (c3, .85, 12, .9)])

    # mountains
    peaks = [(150, 74, 230), (460, 100, 260), (780, 66, 210), (950, 82, 200)]
    M1 = ridge(rnd, -20, W + 20, 322, 10, peaks, iters=7)
    snow = snowcap(rnd, M1, 250, (5, 16))
    M2 = ridge(rnd, -20, W + 20, 344, 6, [(300, 46, 240), (690, 38, 230)], iters=6)
    M3 = ridge(rnd, -20, W + 20, HZ + 1, 2, [], iters=4)
    t2 = treeline(rnd, M2, 8, 20, 5, sink=3)
    t3 = treeline(rnd, M3, 14, 40, 6, sink=3)

    # the bank in front: camp, fire, someone on a log, an upturned canoe
    bank = [(-20, 414), (60, 411), (150, 414), (240, 419), (320, 426), (390, 440), (440, 462), (478, 496), (500, 545)]
    bank_d = smooth(bank) + f" L-20 {H + 5}Z"
    TX, FX, PX = 132, 224, 266
    FY = yat(bank, FX) + 1
    TY, PY = yat(bank, TX) + 1, yat(bank, PX) + 1
    fire = campfire(rnd, FX, FY, 1.05)
    tufts = "".join(f'<path d="M{n(x)} {n(yat(bank, x) + 1)} l{n(rnd.uniform(-3, 3))} {n(-rnd.uniform(4, 9))}" />'
                    for x in (rnd.uniform(20, 470) for _ in range(70)) if abs(x - FX) > 20)
    cy = yat(bank, 368)
    canoe = (f'<path d="M330 {n(cy - 2)} C350 {n(cy - 15)} 392 {n(cy - 13)} 412 {n(cy + 4)} L408 {n(cy + 7)} '
             f'C388 {n(cy - 3)} 352 {n(cy - 4)} 333 {n(cy + 2)}Z" fill="#160C08"/>'
             f'<path d="M330 {n(cy - 2)} C350 {n(cy - 15)} 392 {n(cy - 13)} 412 {n(cy + 4)}" fill="none" stroke="#FF9D5C" stroke-opacity=".45" stroke-width="1.2"/>')
    person = f"""<g transform="translate({PX} {n(PY)}) scale(1.12)">
      <!-- log -->
      <rect x="-17" y="-8.5" width="36" height="8.5" rx="4.2" fill="#1A0E08"/>
      <ellipse cx="-16" cy="-4.2" rx="2.2" ry="4" fill="#3A1E10"/>
      <path d="M-15 -8.3 h30" stroke="#FF9D5C" stroke-opacity=".35" stroke-width=".7"/>
      <!-- legs, knees drawn up -->
      <path d="M0 -9 L4 -12.5 C9 -15.5 13 -20.5 15.8 -19.4 C17.8 -18.6 18 -16.4 17.4 -14.2 L18 -2.2 L21.4 -1.6 C22.6 -1.1 22.4 0 21.2 0 L13.8 0 L14 -12.2 C10.4 -10.6 6 -8.6 2 -7.4Z" fill="url(#skin)"/>
      <g class="breathe">
        <!-- hoodie, leaning back a touch -->
        <path d="M-4.4 -9 C-6.6 -16 -6.8 -25 -3.6 -31 C-1.4 -33.4 3 -33.8 5.2 -31.6 C6.8 -27 7.4 -22 6.8 -17 L7.2 -12 L0 -8.6Z" fill="url(#skin)"/>
        <path d="M-3.6 -31 C-5.6 -32.2 -5.4 -35.6 -2.6 -35.6 C-1.6 -34 -.2 -33.4 1 -33.2Z" fill="#120A08"/>
        <!-- arm resting on the knee, mug in hand -->
        <path d="M-.6 -28.6 C1.4 -24 4.4 -20.4 9.4 -19.8 C12.4 -19.8 15 -21.6 16.8 -23.4" fill="none" stroke="url(#skin)" stroke-width="3.6" stroke-linecap="round"/>
        <circle cx="17.2" cy="-23.6" r="1.6" fill="#2A1610"/>
        <rect x="16.2" y="-28.2" width="4" height="4.6" rx=".8" fill="#5A3020"/>
        <path d="M20.2 -27.2 q2 .4 0 2.6" fill="none" stroke="#5A3020" stroke-width=".8"/>
        <path d="M16.4 -28.2 h3.6" stroke="#FFB27A" stroke-opacity=".5" stroke-width=".5"/>
        <path class="steam" d="M17.6 -29.5 q-1.4 -2.4 0 -4.6 q1.4 -2.2 0 -4.4" fill="none" stroke="#E8EEF6" stroke-opacity=".35" stroke-width=".6" stroke-linecap="round"/>
        <path class="steam" style="animation-delay:-1.6s" d="M19 -29.5 q1.2 -2.2 0 -4.2 q-1.2 -2 0 -4" fill="none" stroke="#E8EEF6" stroke-opacity=".3" stroke-width=".5" stroke-linecap="round"/>
        <!-- head, tilted up toward the aurora -->
        <g transform="rotate(-16 2 -34)">
          <path d="M.6 -33 L.8 -35.2 C-2.4 -36.4 -3 -42 -1 -45 C1 -48.2 6 -48.6 7.6 -45.2 L8 -43.6 L9.6 -41.2 L8.3 -40.6 L8.7 -39.4 L8.1 -38.7 L8.3 -37.6 C7.1 -36.2 5.2 -36 4.2 -35.6 L4.2 -33Z" fill="url(#skin)"/>
          <path d="M8 -43.6 L9.6 -41.2 L8.3 -40.6 L8.7 -39.4 L8.1 -38.7 L8.3 -37.6" fill="none" stroke="#FFB27A" stroke-opacity=".18" stroke-width=".4"/>
          <path d="M6.6 -42.6 q.8 .5 1.4 .2" fill="none" stroke="#05070C" stroke-width=".5" stroke-linecap="round"/>
          <ellipse cx="1.9" cy="-40.6" rx=".95" ry="1.45" fill="#3A1E14"/>
          <g class="hair">
            <path d="M-3.1 -40.6 C-4.2 -45.2 -2 -49.8 3.2 -49.8 C6.8 -49.8 8.9 -47.6 8.6 -44.8 C7.3 -46.1 5.8 -45.9 4.3 -46.7 C3.6 -45 2 -44.2 .9 -43.2 C.6 -41.4 -.4 -39.4 -1.7 -37.8 C-2.6 -38.4 -3.1 -39.6 -3.1 -40.6Z" fill="#0B0605"/>
            <path d="M-1.2 -48 q2.4 -2.6 6 -2 q2.8 .6 3.6 2.6 M-3 -43 q-1.2 -1 -.8 -3" fill="none" stroke="#0B0605" stroke-width="1.1" stroke-linecap="round"/>
          </g>
          <path d="M-3.1 -40.6 C-4.2 -45.2 -2 -49.8 3.2 -49.8" fill="none" stroke="#FF9D5C" stroke-opacity=".6" stroke-width=".55"/>
        </g>
        <!-- firelight along the back -->
        <path d="M-4.4 -9 C-6.6 -16 -6.8 -25 -3.6 -31" fill="none" stroke="#FF9D5C" stroke-opacity=".6" stroke-width=".6"/>
      </g>
    </g>"""
    tent = f"""<g transform="translate({TX} {n(TY)})">
      <path d="M-40 0 L0 -54 L40 0Z" fill="url(#tent)" class="glow"/>
      <path d="M0 -54 L-7 0 h14z" fill="#6E2810" fill-opacity=".85"/>
      <ellipse cx="0" cy="-10" rx="5" ry="8" fill="#FFE8B0" fill-opacity=".55" filter="url(#ablur2)"/>
      <path d="M-40 0 L0 -54 L40 0" fill="none" stroke="#2A140A" stroke-width="1.6" stroke-linejoin="round"/>
      <path d="M0 -54 l-5 -6 M0 -54 l5 -6" stroke="#2A140A" stroke-width="1.2"/>
      <path d="M-20 -27 L-52 2 M20 -27 L52 2" stroke="#FFCF94" stroke-opacity=".25" stroke-width=".6"/>
    </g>"""
    fg = "".join(f'<path d="{fir(rnd, x, H + 20, h, .32)}"/>' for x, h in [(-30, 470), (40, 320), (930, 250), (978, 410), (1032, 500), (884, 150)])
    rocks = "M760 545 C770 520 800 512 826 522 C846 506 880 508 902 524 C930 516 960 520 990 534 L1010 545Z"
    flies = motes(rnd, 26, 300, 900, HZ - 40, H - 30, "#E4FF9A", 1.4, cls="fly")

    # water: fire glints along the bank, a column of moonlight
    fire_gl = "".join(
        f'<rect class="gl" x="{n(rnd.uniform(380, 470) + i * 6)}" y="{n(HZ + 22 + i * 7)}" width="{n(rnd.uniform(10, 30))}" height="1.4" rx=".7" fill="#FFB866" '
        f'style="animation-duration:{rnd.uniform(1.2, 2.4):.1f}s;animation-delay:-{rnd.uniform(0, 2):.1f}s"/>' for i in range(9))
    MX, MYY = 892, 66
    moon_gl = "".join(
        f'<rect class="gl" x="{n(MX - w / 2 + rnd.uniform(-4, 4))}" y="{n(HZ + 4 + i * 5)}" width="{n(w)}" height="1.3" rx=".6" fill="{FROST}" '
        f'style="animation-duration:{rnd.uniform(1.6, 3.2):.1f}s;animation-delay:-{rnd.uniform(0, 3):.1f}s"/>'
        for i, w in enumerate([24, 16, 26, 12, 18, 10, 14, 7, 10, 5, 8, 4, 6, 3]))
    mist = "".join(f'<ellipse class="mist" cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="url(#mistg)" style="animation-duration:{d}s;animation-delay:-{dl}s"/>'
                   for x, y, rx, ry, d, dl in [(230, HZ - 6, 260, 14, 34, 0), (640, HZ - 2, 320, 12, 41, 12), (880, HZ + 8, 220, 10, 29, 6), (500, HZ + 14, 280, 8, 37, 20)])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="I am Aditya Padmarajan. Software developer at STEMCELL Technologies in Vancouver, BC. An aurora over an alpine lake, a campfire, and someone watching it.">
  <title>I am Aditya Padmarajan</title>
  <defs>
    {sky_grad("hsky", 0, HZ)}
    {aurora_defs()}
    <radialGradient id="milk" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#D8D0FF" stop-opacity=".22"/><stop offset=".5" stop-color="#9F96E8" stop-opacity=".08"/><stop offset="1" stop-color="#9F96E8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="milk2" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#FFF0DC" stop-opacity=".16"/><stop offset="1" stop-color="#FFF0DC" stop-opacity="0"/>
    </radialGradient>
    <filter id="lane" x="-5%" y="-50%" width="110%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>
    <radialGradient id="halo"><stop offset="0" stop-color="#FFF3DC" stop-opacity=".35"/><stop offset=".25" stop-color="#DDEBFF" stop-opacity=".1"/><stop offset="1" stop-color="#DDEBFF" stop-opacity="0"/></radialGradient>
    <mask id="moonm"><circle r="14" fill="#fff"/><circle cx="6.5" cy="-4" r="12.5" fill="#000"/></mask>
    <linearGradient id="mt1" x1="0" y1="210" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#1A2D48"/><stop offset="1" stop-color="#0C1729"/></linearGradient>
    <linearGradient id="snowg" x1="0" y1="210" x2="0" y2="262" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#E9F7FF" stop-opacity=".7"/><stop offset="1" stop-color="#9FE8D0" stop-opacity=".25"/></linearGradient>
    <radialGradient id="mistg"><stop offset="0" stop-color="#CFE8F5" stop-opacity=".13"/><stop offset="1" stop-color="#CFE8F5" stop-opacity="0"/></radialGradient>
    <linearGradient id="lake" x1="0" y1="{HZ}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#0E2638" stop-opacity=".05"/><stop offset=".5" stop-color="#06111D" stop-opacity=".5"/><stop offset="1" stop-color="#02060C" stop-opacity=".95"/>
    </linearGradient>
    {ripple_mask("rm", H, W, HZ, 4, 2.6, "#5a5a5a")}
    <clipPath id="lc"><rect y="{HZ}" width="{W}" height="{H - HZ}"/></clipPath>
    <radialGradient id="fireg" cx="{FX}" cy="{n(FY - 8)}" r="260" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#FFB25A" stop-opacity=".5"/><stop offset=".3" stop-color="#F2794A" stop-opacity=".16"/><stop offset="1" stop-color="#F2794A" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="rim" cx="{FX}" cy="{n(FY)}" r="200" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#FFB25A" stop-opacity=".9"/><stop offset="1" stop-color="#FFB25A" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="tent" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFCB85"/><stop offset="1" stop-color="#C9632F"/></linearGradient>
    <linearGradient id="skin" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4A2414"/><stop offset=".45" stop-color="#140A08"/><stop offset="1" stop-color="#05070C"/></linearGradient>
    <linearGradient id="shootg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>
    <radialGradient id="scrim" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#01030A" stop-opacity=".62"/><stop offset=".6" stop-color="#01030A" stop-opacity=".3"/><stop offset="1" stop-color="#01030A" stop-opacity="0"/></radialGradient>
    <radialGradient id="vig" cx="50%" cy="45%" r="75%"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".6"/></radialGradient>
    <linearGradient id="nameg" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1000" y2="0">
      <stop offset="0" stop-color="{MINT}"/><stop offset=".45" stop-color="{MINT}"/><stop offset=".5" stop-color="#FFFFFF"/><stop offset=".55" stop-color="{MINT}"/><stop offset="1" stop-color="{MINT}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-1000 0;-1000 0;1000 0" keyTimes="0;.45;1" dur="8s" begin="2.5s" repeatCount="indefinite"/>
    </linearGradient>
    <filter id="tglow" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="7"/></filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  </defs>
  <style>{night_css(f'''
    .t {{ font-family:{SERIF}; font-size:58px; fill:{CREAM}; letter-spacing:-.6px; }}
    .s {{ font-family:{MONO}; font-size:11.5px; letter-spacing:4.2px; fill:{CREAM}; fill-opacity:.62; }}
    .sat {{ animation:sat 75s linear infinite; }}
    .breathe {{ transform-box:fill-box; transform-origin:50% 100%; animation:breathe 5.5s ease-in-out infinite; }}
    @keyframes breathe {{ 0%,100% {{ transform:scale(1,1); }} 50% {{ transform:scale(1.008,1.018); }} }}
    .hair {{ transform-box:fill-box; transform-origin:80% 80%; animation:hair 7s ease-in-out infinite alternate; }}
    @keyframes hair {{ from {{ transform:rotate(-1.5deg); }} to {{ transform:rotate(1.5deg); }} }}
    .steam {{ transform-box:fill-box; transform-origin:50% 100%; animation:steam 3.2s ease-out infinite; }}
    @keyframes steam {{ 0% {{ opacity:0; transform:translateY(1px) scale(.8); }} 30% {{ opacity:1; }} 100% {{ opacity:0; transform:translateY(-5px) scale(1.2); }} }}
    @keyframes sat {{ 0% {{ transform:translate(0,0); opacity:0; }} 4% {{ opacity:.85; }} 55% {{ transform:translate(760px,120px); opacity:.85; }} 56%,100% {{ transform:translate(760px,120px); opacity:0; }} }}''')}
  </style>
  <g clip-path="url(#frame)">
    <g id="sky">
      <rect width="{W}" height="{HZ + 2}" fill="url(#hsky)"/>
      <g class="fade">
        <ellipse cx="500" cy="{n(my(500))}" rx="680" ry="78" fill="url(#milk)" transform="rotate({ang:.1f} 500 {n(my(500))})"/>
        <ellipse cx="420" cy="{n(my(420))}" rx="420" ry="26" fill="url(#milk2)" transform="rotate({ang:.1f} 420 {n(my(420))})"/>
        {milky}
        <path d="{lane}" fill="none" stroke="#01030A" stroke-opacity=".5" stroke-width="12" filter="url(#lane)"/>
        {stars}
        {brights}
      </g>
      <g transform="translate({MX} {MYY})">
        <circle r="110" fill="url(#halo)"/>
        <circle r="14" fill="#FFF3DC" fill-opacity=".07"/>
        <circle r="14" fill="#FFF5E4" mask="url(#moonm)"/>
      </g>
      {curtains}
      <path d="{fill_under(M1, HZ + 30)}" fill="url(#mt1)"/>
      <path d="{snow}" fill="url(#snowg)"/>
      <path d="{line_of(M1)}" fill="none" stroke="{AURORA}" stroke-opacity=".3" stroke-width="1.1"/>
      <path d="{fill_under(M2, HZ + 30)}" fill="#0A1526"/><path d="{t2}" fill="#0A1526"/>
      {mist}
      <path d="{fill_under(M3, HZ + 30)}" fill="#050B14"/><path d="{t3}" fill="#050B14"/>
    </g>

    <g class="shoot"><path d="M760 40 l130 -58" stroke="url(#shootg)" stroke-width="1.4" transform="rotate(180 825 11)"/></g>
    <g class="shoot" style="animation-duration:19s;animation-delay:-7s"><path d="M330 34 l96 -42" stroke="url(#shootg)" stroke-width="1.1" transform="rotate(180 378 13)"/></g>
    <circle class="sat" cx="60" cy="24" r=".9" fill="#fff"/>

    <!-- the lake holds all of it, broken by ripples -->
    <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="#04101B"/>
    <g clip-path="url(#lc)" mask="url(#rm)" opacity=".8">
      <use xlink:href="#sky" href="#sky" transform="matrix(1 0 0 -1 0 {2 * HZ})"/>
    </g>
    <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#lake)"/>
    <rect y="{HZ}" width="{W}" height="1" fill="#BFF5E2" fill-opacity=".18"/>
    <g>{moon_gl}</g>
    <g>{fire_gl}</g>

    <!-- camp -->
    <rect class="glow" width="{W}" height="{H}" fill="url(#fireg)"/>
    <path d="{bank_d}" fill="#03070D"/>
    <path d="{smooth(bank)}" fill="none" stroke="url(#rim)" stroke-width="1.6"/>
    <g stroke="#0B0705" stroke-width="1.1" stroke-linecap="round">{tufts}</g>
    {canoe}
    {tent}
    {fire}
    {person}
    {flies}
    <path d="{rocks}" fill="#02050A"/>
    <g fill="#010307">{fg}</g>

    <!-- name -->
    <ellipse cx="500" cy="134" rx="400" ry="92" fill="url(#scrim)"/>
    <g class="in" style="animation-delay:.3s"><text class="k" x="500" y="86" text-anchor="middle">22:47  ·  49.28° N  123.12° W  ·  KP 6, CLEAR SKIES</text></g>
    <g class="in" style="animation-delay:.9s">
      <text class="t" x="500" y="146" text-anchor="middle" fill="{AURORA}" style="fill:{AURORA};fill-opacity:.35" filter="url(#tglow)">I am <tspan font-style="italic">Aditya Padmarajan</tspan>.</text>
      <text class="t" x="500" y="146" text-anchor="middle">I am <tspan font-style="italic" fill="url(#nameg)" style="fill:url(#nameg)">Aditya Padmarajan</tspan>.</text>
    </g>
    <g class="in" style="animation-delay:1.6s"><text class="s" x="500" y="182" text-anchor="middle">SOFTWARE ENGINEER ·  VANCOUVER, BC</text></g>

    <rect width="{W}" height="{H}" fill="url(#vig)"/>
    {frame(W, H, 20, AURORA, ".22")}
  </g>
</svg>
"""


# ─── field notes as a constellation ─────────────────────────────────────────
def night_notes():
    rnd = random.Random(2251)
    W, H = 1000, 470
    CX, CY = 772, 214

    rows = [("NOW",     "Software Developer at STEMCELL Technologies"),
            ("STUDIED", "B.Sc. Computer Science, University of Victoria"),
            ("BASED",   "Vancouver, British Columbia"),
            ("BUILT",   "SpideyIRL — 3rd place, QNX track, Hack the North 2026"),
            ("BUILT",   "Pulse — hackathon winner, Web Summit 2026")]
    # star for each row (offset from chart centre), and its label
    stars = [((8, -96), "STEMCELL", "end"), ((-128, 62), "UVIC", "start"), ((-58, -8), "YVR", "end"),
             ((84, -18), "HTN ’26", "start"), ((132, 70), "PULSE ’26", "start")]
    extra = [(38, 42), (-28, 92)]
    pos = [(CX + dx, CY + dy) for (dx, dy), _, _ in stars] + [(CX + dx, CY + dy) for dx, dy in extra]
    # the asterism: a peak with a lake below it
    edges = [(1, 2), (2, 0), (0, 3), (3, 4), (3, 5), (5, 6), (6, 2)]
    T0, DT = .9, .55
    order = [1, 2, 0, 3, 4]               # the order stars light: where it started → now
    when = {r: T0 + i * DT for i, r in enumerate(order)}
    when[5], when[6] = when[3] + .2, when[4] + .25

    lines = []
    for a, b in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        L = math.hypot(x2 - x1, y2 - y1)
        lines.append(f'<path class="draw" d="M{n(x1)} {n(y1)} L{n(x2)} {n(y2)}" stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}" '
                     f'style="animation-delay:{max(when[a], when[b]) - .3:.2f}s"/>')
    starsvg = []
    for i, (x, y) in enumerate(pos):
        big = i < 5
        starsvg.append(f'<g class="ign" style="animation-delay:{when[i]:.2f}s"><g transform="translate({n(x)} {n(y)})">'
                       f'<circle r="{14 if big else 8}" fill="url(#bstar)"/>'
                       + (f'<path d="M-9 0H9M0 -9V9" stroke="{FROST}" stroke-width=".5" stroke-opacity=".8"/>' if big else "")
                       + f'<circle r="{2.4 if i == 0 else 1.8 if big else 1.2}" fill="{GOLD if i == 0 else "#fff"}"/></g></g>')
        if big:
            _, lab, anc = stars[i]
            dx = -12 if anc == "end" else 12
            starsvg.append(f'<g class="ign" style="animation-delay:{when[i] + .2:.2f}s"><text class="lab" x="{n(x + dx)}" y="{n(y - 8)}" text-anchor="{anc}">{lab}</text></g>')

    rings = "".join(f'<circle cx="{CX}" cy="{CY}" r="{r}" stroke-dasharray="{da}"/>' for r, da in [(60, "2 5"), (115, "2 5"), (170, "none")])
    spokes = "".join(f'<path d="M{n(CX + 60 * math.cos(math.radians(a)))} {n(CY + 60 * math.sin(math.radians(a)))} L{n(CX + 170 * math.cos(math.radians(a)))} {n(CY + 170 * math.sin(math.radians(a)))}"/>'
                     for a in range(0, 360, 30))
    ticks = "".join(f'<path d="M{n(CX + 170 * math.cos(math.radians(a)))} {n(CY + 170 * math.sin(math.radians(a)))} '
                    f'L{n(CX + (163 if a % 15 else 158) * math.cos(math.radians(a)))} {n(CY + (163 if a % 15 else 158) * math.sin(math.radians(a)))}"/>'
                    for a in range(0, 360, 5))
    cards = "".join(f'<text class="cd" x="{n(CX + 182 * math.cos(math.radians(a)))}" y="{n(CY + 182 * math.sin(math.radians(a)) + 3.5)}" text-anchor="middle">{c}</text>'
                    for a, c in [(-90, "N"), (0, "E"), (90, "S"), (180, "W")])

    row_svg = []
    for i, (k, v) in enumerate(rows):
        y = 176 + i * 50
        star_i = i  # row i ↔ star i
        d = when[star_i]
        row_svg.append(f'<g class="in" style="animation-delay:{d - .1:.2f}s">'
                       f'<path d="M62 {y - 4} l1.6 -4.4 l1.6 4.4 l4.4 1.6 l-4.4 1.6 l-1.6 4.4 l-1.6 -4.4 l-4.4 -1.6z" fill="{GOLD if i == 0 else FROST}"/>'
                       f'<text class="lk" x="84" y="{y}">{k}</text>'
                       f'<text class="lv" x="84" y="{y + 22}">{v}</text></g>')

    sky = starfield(rnd, W, 0, H - 60, 220, avoid=lambda x, y: x < 540 and y > 60)
    wisp = aurora(rnd, 380, W + 40, lambda x: 40 + 14 * math.sin(x / 120), lambda x: 30 + 30 * math.sin(x / 150) ** 2, 4, "ray2", glow=False)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Field notes. Now: Software Developer at STEMCELL Technologies. Studied: B.Sc. Computer Science, University of Victoria. Based in Vancouver, British Columbia. Built SpideyIRL, 3rd place QNX track at Hack the North 2026, and Pulse, hackathon winner at Web Summit 2026.">
  <title>Field notes — Aditya Padmarajan</title>
  <defs>
    <linearGradient id="nsk" x1="0" y1="0" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#040A1C"/><stop offset=".7" stop-color="#071228"/><stop offset="1" stop-color="#0C1F38"/>
    </linearGradient>
    {aurora_defs()}
    <radialGradient id="chart" cx="{CX}" cy="{CY}" r="190" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#6CF5BE" stop-opacity=".08"/><stop offset="1" stop-color="#6CF5BE" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".5"/></linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  </defs>
  <style>{night_css(f'''
    .h  {{ font-family:{SERIF}; font-size:38px; fill:{CREAM}; letter-spacing:-.4px; }}
    .lk {{ font-family:{MONO}; font-size:10px; letter-spacing:3px; fill:{GOLD}; fill-opacity:.85; }}
    .lv {{ font-family:{SERIF}; font-size:19.5px; fill:{CREAM}; fill-opacity:.94; }}
    .lab {{ font-family:{MONO}; font-size:9.5px; letter-spacing:2.2px; fill:{MINT}; fill-opacity:.8; }}
    .cd {{ font-family:{MONO}; font-size:10px; letter-spacing:1px; fill:{FROST}; fill-opacity:.35; }}
    .cap {{ font-family:{MONO}; font-size:9.5px; letter-spacing:3px; fill:{FROST}; fill-opacity:.4; }}
    .draw {{ animation:draw 1.4s {EASE} both; }}
    @keyframes draw {{ to {{ stroke-dashoffset:0; }} }}
    .ign {{ animation:ign 1.6s {EASE} both; }}
    @keyframes ign {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
    .rot {{ transform-origin:{CX}px {CY}px; animation:rot 240s linear infinite; }}
    @keyframes rot {{ to {{ transform:rotate(360deg); }} }}''')}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#nsk)"/>
    <g opacity=".45" mask="url(#am)">{wisp}</g>
    {sky}

    <circle cx="{CX}" cy="{CY}" r="190" fill="url(#chart)"/>
    <g class="rot" fill="none" stroke="{FROST}" stroke-opacity=".13" stroke-width=".8">{rings}{spokes}{ticks}</g>
    {cards}
    <g fill="none" stroke="{MINT}" stroke-opacity=".55" stroke-width="1" stroke-linecap="round">{''.join(lines)}</g>
    {''.join(starsvg)}

    <g class="in" style="animation-delay:.2s"><text class="k" x="58" y="78">FIELD NOTES  ·  22:51  ·  BY FIRELIGHT</text></g>
    <g class="in" style="animation-delay:.45s"><text class="h" x="56" y="126">Written in the <tspan font-style="italic" fill="{MINT}">stars</tspan></text></g>
    {''.join(row_svg)}

    {edge_trees(rnd, W, H, H - 8, 12, 40, 7)}
    <rect y="{H - 80}" width="{W}" height="80" fill="url(#fade)"/>
    {frame(W, H, 20, AURORA, ".22")}
  </g>
</svg>
"""


# ─── link cards ──────────────────────────────────────────────────────────────
def night_card(kind, label, target, num, idx):
    rnd = random.Random(900 + idx)
    W, H = 330, 150
    p = f"c{idx}"
    sky = starfield(rnd, W, 0, H - 30, 60, tw=.4)
    if kind == "summit":
        accent = GOLD
        peak = f"M130 {H} L212 66 L232 80 L262 38 L292 70 L310 60 L350 {H}Z"
        cap = "M262 38 L250 58 L257 55 L263 63 L271 54 L280 61 L292 70 Z"
        scene = f"""
    <g transform="translate(306 26)"><circle r="60" fill="url(#{p}h)"/><circle r="10" fill="#FFF3DC" fill-opacity=".07"/><circle r="10" fill="#FFF5E4" mask="url(#{p}m)"/></g>
    <path d="M90 {H} L176 92 L204 104 L236 84 L290 110 L350 96 L350 {H}Z" fill="#14233A"/>
    <path d="{peak}" fill="#0E1A2E"/>
    <path d="{cap}" fill="#E9F7FF" fill-opacity=".65"/>
    <path d="M262 38 v-14" stroke="{CREAM}" stroke-width=".9"/>
    <path fill="{EMBER}"><animate attributeName="d" dur="1.3s" repeatCount="indefinite"
      values="M262 24 q5 1 10 0 q-1 3 0 6 q-5 1 -10 0z;M262 24 q5 -2 10 1 q-1 3 0 6 q-5 -2 -10 -1z;M262 24 q5 1 10 0 q-1 3 0 6 q-5 1 -10 0z"/></path>"""
        defs = (f'<radialGradient id="{p}h"><stop offset="0" stop-color="#FFE9C7" stop-opacity=".35"/><stop offset="1" stop-color="#FFE9C7" stop-opacity="0"/></radialGradient>'
                f'<mask id="{p}m"><circle r="10" fill="#fff"/><circle cx="4.5" cy="-3" r="9" fill="#000"/></mask>')
    elif kind == "forest":
        accent = AURORA
        cur = aurora(rnd, 120, W + 20, lambda x: 92 + 10 * math.sin(x / 40), lambda x: 40 + 30 * math.sin(x / 60) ** 2, 2.6, "ray1", glow=False)
        back = "".join(f'<path d="{fir(rnd, x, H + 4, h, .34)}"/>' for x, h in [(170, 60), (196, 76), (222, 66), (250, 86), (278, 70), (306, 92), (334, 68)])
        front = "".join(f'<path d="{fir(rnd, x, H + 4, h, .34)}"/>' for x, h in [(186, 96), (232, 122), (290, 136), (322, 108)])
        scene = f"""
    <g class="sway" mask="url(#am)" style="animation-duration:11s">{cur}</g>
    <g fill="#0C1C26">{back}</g>
    <g fill="#03080D">{front}</g>
    {motes(rnd, 14, 160, 330, 60, 140, "#E4FF9A", 1.3, cls="fly")}"""
        defs = aurora_defs()
    else:  # lantern on the lake
        accent = "#FFB866"
        HZ = 104
        gl = "".join(f'<rect class="gl" x="{n(268 - w / 2 + rnd.uniform(-3, 3))}" y="{n(HZ + 12 + i * 4.2)}" width="{n(w)}" height="1.3" rx=".6" fill="#FFB866" '
                     f'style="animation-duration:{rnd.uniform(1.2, 2.4):.1f}s;animation-delay:-{rnd.uniform(0, 2):.1f}s"/>'
                     for i, w in enumerate([22, 16, 26, 12, 18, 8, 12, 5]))
        rid = ridge(rnd, 100, W + 20, HZ, 2, [(220, 18, 80), (300, 26, 90)], iters=5)
        scene = f"""
    <path d="{fill_under(rid, HZ + 1)}" fill="#0B1626"/><path d="{treeline(rnd, rid, 5, 14, 5, sink=2)}" fill="#0B1626"/>
    <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="#050E19"/>
    <rect y="{HZ}" width="{W}" height=".8" fill="{MINT}" fill-opacity=".15"/>
    <circle cx="268" cy="{HZ - 4}" r="70" fill="url(#{p}g)" class="glow"/>
    {gl}
    <g class="bob">
      <path d="M254 {HZ + 3} h28 l-4 6 h-20z" fill="#1A0E08"/>
      <path d="M268 {HZ + 3} v-14" stroke="#2A140A" stroke-width="1.2"/>
      <rect x="262" y="{HZ - 22}" width="12" height="13" rx="3" fill="#FFD08A" class="glow"/>
      <path d="M261 {HZ - 22} h14 M262 {HZ - 9} h12" stroke="#2A140A" stroke-width="1.4"/>
    </g>"""
        defs = f'<radialGradient id="{p}g"><stop offset="0" stop-color="#FFB25A" stop-opacity=".55"/><stop offset=".35" stop-color="#F2794A" stop-opacity=".15"/><stop offset="1" stop-color="#F2794A" stop-opacity="0"/></radialGradient>'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{label} — {target}">
  <title>{label} — {target}</title>
  <defs>
    {sky_grad(p + "s", 0, H)}
    <radialGradient id="bstar"><stop offset="0" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    {defs}
    <linearGradient id="{p}sc" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#01030A" stop-opacity=".9"/><stop offset=".45" stop-color="#01030A" stop-opacity=".55"/><stop offset=".72" stop-color="#01030A" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="{p}c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>{night_css(f'''
    .lb {{ font-family:{SERIF}; font-size:31px; fill:{CREAM}; letter-spacing:-.3px; }}
    .tx {{ font-family:{MONO}; font-size:11px; letter-spacing:.3px; fill:{CREAM}; fill-opacity:.62; }}
    .tg {{ font-family:{MONO}; font-size:9.5px; letter-spacing:3px; fill:{accent}; }}
    .ar {{ animation:ar 2.6s ease-in-out infinite; }}
    @keyframes ar {{ 0%,100% {{ transform:translate(0,0); }} 50% {{ transform:translate(3px,0); }} }}
    .bob {{ transform-box:fill-box; transform-origin:50% 100%; animation:bob 4.5s ease-in-out infinite; }}
    @keyframes bob {{ 0%,100% {{ transform:translateY(0) rotate(-2.5deg); }} 50% {{ transform:translateY(2px) rotate(2.5deg); }} }}''')}
  </style>
  <g clip-path="url(#{p}c)">
    <rect width="{W}" height="{H}" fill="url(#{p}s)"/>
    {sky}
    {scene}
    <rect width="{W}" height="{H}" fill="url(#{p}sc)"/>
    <text class="tg" x="24" y="36">{num}</text>
    <text class="lb" x="22" y="84">{label}</text>
    <g class="ar"><text class="tx" x="24" y="112">{target}  →</text></g>
    <rect x="24" y="126" width="26" height="1.5" rx=".75" fill="{accent}" fill-opacity=".7"/>
    {frame(W, H, 16, accent, ".28")}
  </g>
</svg>
"""


# ─── footer ──────────────────────────────────────────────────────────────────
def night_footer():
    rnd = random.Random(2359)
    W, H, HZ = 1000, 230, 168
    stars = starfield(rnd, W, 0, HZ - 20, 150, avoid=lambda x, y: 250 < x < 750 and 30 < y < 120)
    wisp = aurora(rnd, -40, W + 40, lambda x: 130 + 12 * math.sin(x / 140 + 1), lambda x: 40 + 40 * math.sin(x / 180) ** 2, 4, "ray1", glow=False)
    rid = ridge(rnd, -20, W + 20, HZ - 4, 4, [(160, 40, 200), (820, 34, 220)], iters=6)
    trees = treeline(rnd, rid, 6, 18, 5, sink=2)
    spit = smooth([(410, HZ + 6), (450, HZ + 1), (500, HZ - 1), (550, HZ + 1), (590, HZ + 6)]) + "Z"
    FX, FY = 500, HZ
    fire = campfire(rnd, FX, FY, .8, sparks=14)
    gl = "".join(f'<rect class="gl" x="{n(FX - w / 2 + rnd.uniform(-4, 4))}" y="{n(HZ + 8 + i * 4.5)}" width="{n(w)}" height="1.3" rx=".6" fill="#FFB866" '
                 f'style="animation-duration:{rnd.uniform(1.2, 2.4):.1f}s;animation-delay:-{rnd.uniform(0, 2):.1f}s"/>'
                 for i, w in enumerate([40, 30, 46, 22, 30, 14, 20, 8, 12, 5, 6, 3]))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="The fire's still going. Pull up a log. Back to the top.">
  <title>The fire's still going</title>
  <defs>
    {sky_grad("fsk", 0, HZ)}
    {aurora_defs()}
    <radialGradient id="fg" cx="{FX}" cy="{FY - 6}" r="240" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#FFB25A" stop-opacity=".42"/><stop offset=".3" stop-color="#F2794A" stop-opacity=".12"/><stop offset="1" stop-color="#F2794A" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  </defs>
  <style>{night_css(f'''
    .t {{ font-family:{SERIF}; font-size:28px; fill:{CREAM}; letter-spacing:-.3px; }}
    .cue {{ animation:cue 2.4s ease-in-out infinite; }}
    @keyframes cue {{ 0%,100% {{ transform:translateY(2px); opacity:.5; }} 50% {{ transform:translateY(-3px); opacity:1; }} }}''')}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{HZ + 2}" fill="url(#fsk)"/>
    {stars}
    <g opacity=".5" mask="url(#am)">{wisp}</g>
    <path d="{fill_under(rid, HZ + 2)}" fill="#060D18"/><path d="{trees}" fill="#060D18"/>
    <rect y="{HZ}" width="{W}" height="{H - HZ}" fill="#030810"/>
    <rect y="{HZ}" width="{W}" height="1" fill="{MINT}" fill-opacity=".15"/>
    <rect class="glow" width="{W}" height="{H}" fill="url(#fg)"/>
    {gl}
    <path d="{spit}" fill="#02050A"/>
    {fire}

    <text class="t" x="500" y="66" text-anchor="middle">The fire’s still going — <tspan font-style="italic" fill="{MINT}">pull up a log</tspan>.</text>
    <text class="k" x="500" y="98" text-anchor="middle"></text>
    {frame(W, H, 20, AURORA, ".22")}
  </g>
</svg>
"""


if __name__ == "__main__":
    print("Generating assets...")
    write("night-hero.svg", night_hero())
    write("night-notes.svg", night_notes())
    for i, (fn, kind, label, target, num) in enumerate([
        ("night-card-portfolio", "summit",  "Portfolio", "adityapadmarajan.com",        "01  ·  THE SUMMIT"),
        ("night-card-linkedin",  "forest",  "LinkedIn",  "in/aditya-padmarajan",        "02  ·  THE TREELINE"),
        ("night-card-email",     "lantern", "Email",     "aditya.padmarajan@gmail.com", "03  ·  A LIGHT ON THE LAKE"),
    ]):
        write(f"{fn}.svg", night_card(kind, label, target, num, i))
    write("night-footer.svg", night_footer())
    write("banner.svg", banner())
    write("chapter-forest.svg", chapter_forest())
    write("identity.svg", identity())
    write("chapter-river.svg", chapter_river())
    for i, (fn, kind, label, target, trail, dist) in enumerate([
        ("btn-portfolio", "summit", "Portfolio", "adityapadmarajan.com",        "TRAIL 01", "SUMMIT"),
        ("btn-linkedin",  "forest", "LinkedIn",  "in/aditya-padmarajan",        "TRAIL 02", "BASECAMP"),
        ("btn-email",     "river",  "Email",     "aditya.padmarajan@gmail.com", "TRAIL 03", "DOWNSTREAM"),
    ]):
        write(f"{fn}.svg", card(kind, label, target, trail, dist, i))
    write("camp.svg", camp())
    print("Done.")
