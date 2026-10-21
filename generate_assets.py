#!/usr/bin/env python3
"""
Generates the animated SVG assets for adi-padmarajan's profile README.
Concept: the README is a dive. Reading top to bottom you descend through the
water column (surface, twilight, midnight, abyss) to the floor of the
Challenger Deep. Abyssal navy throughout; bioluminescent cyan and violet are
the only light sources.

Run:  python3 generate_assets.py
Out:  assets/*.svg
"""

import math
import os
import random

random.seed(10935)   # Challenger Deep, in metres

OUT = "assets"
os.makedirs(OUT, exist_ok=True)

# ── design tokens ────────────────────────────────────────────────────────────
ABYSS = "#01040B"   # deepest background
DEEP  = "#030B1C"   # panel base
PANEL = "#061229"   # panel fill
LINE  = "#132A4F"   # hairline / border
MUTE  = "#5873A0"   # muted text
FOAM  = "#DCEBFF"   # primary text
BIO   = "#38E1FF"   # bioluminescent cyan, primary accent
TIDE  = "#3B82F6"   # electric blue
VOLT  = "#8B6CFF"   # violet glow, secondary accent
SURF  = "#0C3B6E"   # sunlit surface water

MONO = "ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace"


def write(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {path}  ({len(content):,} bytes)")


# ── shared particles ─────────────────────────────────────────────────────────
def snow(n, W, rmax=1.6, opmax=0.5):
    """Marine snow: slow-sinking specks, each on its own clock so the field never syncs."""
    out = []
    for _ in range(n):
        dur = random.uniform(9, 22)
        out.append(
            f'<circle class="snow" cx="{random.uniform(0, W):.0f}" cy="-4" r="{random.uniform(.4, rmax):.1f}" '
            f'fill-opacity="{random.uniform(.12, opmax):.2f}" '
            f'style="animation-duration:{dur:.1f}s;animation-delay:-{random.uniform(0, dur):.1f}s"/>'
        )
    return "\n    ".join(out)


def snow_css(H):
    return (f".snow {{ fill:{FOAM}; animation:sink linear infinite; }}\n"
            f"    @keyframes sink {{ from {{transform:translate(0,0)}} to {{transform:translate(-14px,{H + 10}px)}} }}")


def bubbles(n, x0, x1, y0, rmax=3.2):
    out = []
    for _ in range(n):
        dur = random.uniform(4, 9)
        out.append(
            f'<circle class="bub" cx="{random.uniform(x0, x1):.0f}" cy="{y0}" r="{random.uniform(1, rmax):.1f}" '
            f'style="animation-duration:{dur:.1f}s;animation-delay:-{random.uniform(0, dur):.1f}s"/>'
        )
    return "\n    ".join(out)


def bubble_css(rise):
    return (f".bub {{ fill:none; stroke:{BIO}; stroke-width:1; stroke-opacity:.55; animation:rise ease-in infinite; }}\n"
            f"    @keyframes rise {{\n"
            f"      0%   {{ transform:translate(0,0); opacity:0; }}\n"
            f"      12%  {{ opacity:1; }}\n"
            f"      50%  {{ transform:translate(5px,-{rise / 2:.0f}px); }}\n"
            f"      88%  {{ opacity:.8; }}\n"
            f"      100% {{ transform:translate(-3px,-{rise}px); opacity:0; }}\n"
            f"    }}")


# ── jellyfish ────────────────────────────────────────────────────────────────
BELL = ("M-30 0 C-30 -34 30 -34 30 0 C24 4 18 -1 12 3 C6 -1 0 4 -6 1 "
        "C-12 -2 -18 4 -24 2 C-27 1 -29 1 -30 0Z")


def jelly(x, y, s, a, b, idx, delay):
    """Bell pulses (SMIL scale), tentacles undulate (SMIL path morph), whole body drifts (CSS)."""
    tents = []
    for k, tx in enumerate([-20, -10, 0, 10, 20]):
        L = 48 + (k % 2) * 18
        A = f"M{tx} 2 C{tx + 7} {L * .3:.0f} {tx - 7} {L * .6:.0f} {tx} {L}"
        B = f"M{tx} 2 C{tx - 7} {L * .3:.0f} {tx + 7} {L * .6:.0f} {tx + 3} {L}"
        tents.append(f'<path d="{A}"><animate attributeName="d" dur="{3 + k * .35:.2f}s" '
                     f'repeatCount="indefinite" values="{A};{B};{A}"/></path>')
    arms = []
    for tx in (-4, 4):
        A = f"M{tx} 2 C{tx + 12} 26 {tx - 12} 52 {tx} 84"
        B = f"M{tx} 2 C{tx - 12} 26 {tx + 12} 52 {tx + 4} 84"
        arms.append(f'<path d="{A}"><animate attributeName="d" dur="4.4s" '
                    f'repeatCount="indefinite" values="{A};{B};{A}"/></path>')
    tents, arms = "".join(tents), "".join(arms)

    return f"""<radialGradient id="jg{idx}" cx="50%" cy="25%" r="75%">
      <stop offset="0%"   stop-color="{a}" stop-opacity=".60"/>
      <stop offset="55%"  stop-color="{b}" stop-opacity=".22"/>
      <stop offset="100%" stop-color="{b}" stop-opacity="0"/>
    </radialGradient>""", f"""<g transform="translate({x},{y}) scale({s})">
      <g class="drift" style="animation-delay:-{delay}s">
        <g fill="none" stroke="{a}" stroke-width="1" stroke-opacity=".5" stroke-linecap="round">{tents}</g>
        <g fill="none" stroke="{b}" stroke-width="2.4" stroke-opacity=".45" stroke-linecap="round">{arms}</g>
        <g>
          <animateTransform attributeName="transform" type="scale" values="1 1;1.07 .88;1 1" dur="3.2s" repeatCount="indefinite"/>
          <path d="{BELL}" fill="url(#jg{idx})" stroke="{a}" stroke-opacity=".85" stroke-width="1.2" filter="url(#jglow)"/>
          <path d="M-21 -3 Q0 -25 21 -3" fill="none" stroke="{b}" stroke-opacity=".5"/>
          <path d="M-11 -2 Q0 -15 11 -2" fill="none" stroke="{a}" stroke-opacity=".35"/>
        </g>
      </g>
    </g>"""


# ── 1. HERO BANNER: THE SURFACE ──────────────────────────────────────────────
def banner():
    W, H = 1200, 400
    cx, cy = W / 2, 182          # name centre, also the sonar origin

    # god rays slanting down from the surface
    rays = []
    for x in (120, 290, 450, 620, 780, 930, 1070):
        w, sk = random.randint(26, 72), random.randint(60, 150)
        rays.append(
            f'<polygon class="ray" points="{x},0 {x + w},0 {x + w + sk},{H * .82:.0f} {x + sk - w * .5:.0f},{H * .82:.0f}" '
            f'style="animation-delay:-{random.uniform(0, 8):.1f}s"/>'
        )
    rays = "\n      ".join(rays)

    # surface chop: two sine bands that scroll at different speeds
    def wave(y, amp):
        return f"M-200 {y} " + " ".join(f"q25 {-amp} 50 0 t50 0" for _ in range(15)) + f" L{W + 300} -20 L-200 -20Z"

    # depth ruler that scrolls upward forever, so the whole banner reads as sinking
    ticks = "".join(
        f'<line x1="22" y1="{y}" x2="{40 if y % 60 == 0 else 30}" y2="{y}"/>'
        for y in range(-60, H + 61, 12)
    )

    jd, jb = zip(
        jelly(1046, 112, 1.15, BIO,  VOLT, 0, 0),
        jelly(178,  262, 0.62, VOLT, BIO,  1, 3.1),
        jelly(930,  300, 0.42, BIO,  TIDE, 2, 5.4),
    )
    jd, jb = "\n    ".join(jd), "\n    ".join(jb)

    rings = "\n    ".join(
        f'<circle class="ping" cx="{cx:.0f}" cy="{cy}" r="420" style="animation-delay:-{d}s"/>' for d in (0, 2, 4)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Aditya Padmarajan — Software Developer">
  <title>Aditya Padmarajan — Software Developer</title>
  <defs>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{SURF}"/>
      <stop offset="28%"  stop-color="#072248"/>
      <stop offset="62%"  stop-color="#03102A"/>
      <stop offset="100%" stop-color="{ABYSS}"/>
    </linearGradient>
    <linearGradient id="rayg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#9FD4FF" stop-opacity=".20"/>
      <stop offset="100%" stop-color="#9FD4FF" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="vignette" cx="50%" cy="42%" r="70%">
      <stop offset="55%"  stop-color="{ABYSS}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{ABYSS}" stop-opacity=".75"/>
    </radialGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{BIO}"  stop-opacity=".45"/>
      <stop offset="100%" stop-color="{VOLT}" stop-opacity=".25"/>
    </linearGradient>
    <filter id="jglow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="soft" x="-20%" y="-60%" width="140%" height="220%">
      <feGaussianBlur stdDeviation="12"/>
    </filter>
    <!-- refraction: the name wobbles like it is being read through moving water -->
    <filter id="refract" x="-5%" y="-40%" width="110%" height="180%">
      <feTurbulence type="fractalNoise" baseFrequency="0.006 0.03" numOctaves="1" seed="7" result="n">
        <animate attributeName="baseFrequency" dur="11s" repeatCount="indefinite"
                 values="0.006 0.03;0.008 0.042;0.006 0.03"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="4" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    {jd}
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="6"/></clipPath>
  </defs>

  <style>
    .ray {{ fill:url(#rayg); animation:shimmer 8s ease-in-out infinite; }}
    @keyframes shimmer {{ 0%,100% {{opacity:.35}} 50% {{opacity:1}} }}

    .w1 {{ fill:#2A78C2; fill-opacity:.22; animation:chop 7s linear infinite; }}
    .w2 {{ fill:#5AB0FF; fill-opacity:.12; animation:chop 4.5s linear infinite reverse; }}
    @keyframes chop {{ from {{transform:translateX(0)}} to {{transform:translateX(-100px)}} }}

    .ruler {{ stroke:{BIO}; stroke-opacity:.35; stroke-width:1; animation:descend 2.6s linear infinite; }}
    @keyframes descend {{ from {{transform:translateY(0)}} to {{transform:translateY(-60px)}} }}

    .ping {{ fill:none; stroke:{BIO}; stroke-width:1.2; vector-effect:non-scaling-stroke;
             transform-origin:{cx:.0f}px {cy}px; animation:ping 6s cubic-bezier(.2,.6,.4,1) infinite; }}
    @keyframes ping {{ 0% {{transform:scale(.05);opacity:.75}} 100% {{transform:scale(1);opacity:0}} }}

    .drift {{ animation:drift 9s ease-in-out infinite; }}
    @keyframes drift {{ 0%,100% {{transform:translate(0,0)}} 50% {{transform:translate(8px,-16px)}} }}

    {snow_css(H)}
    {bubble_css(H + 20)}

    .name  {{ font-family:{MONO}; font-size:60px; font-weight:700; letter-spacing:7px; }}
    .halo  {{ fill:{BIO}; animation:breathe 5s ease-in-out infinite; }}
    @keyframes breathe {{ 0%,100% {{opacity:.25}} 50% {{opacity:.6}} }}

    .eyebrow {{ font-family:{MONO}; font-size:13px; letter-spacing:5.5px; fill:{BIO}; fill-opacity:.9; }}
    .sub     {{ font-family:{MONO}; font-size:15.5px; letter-spacing:1.2px; fill:{MUTE}; }}
    .subhi   {{ fill:{FOAM}; }}
    .meta    {{ font-family:{MONO}; font-size:11px; letter-spacing:2.4px; fill:{MUTE}; }}
    .depth   {{ font-family:{MONO}; font-size:11px; letter-spacing:2px; fill:{BIO}; }}

    .cursor {{ fill:{BIO}; animation:blink 1.05s steps(1) infinite; }}
    @keyframes blink {{ 0%,50% {{opacity:1}} 51%,100% {{opacity:0}} }}
    .pulse {{ animation:pulse 2.4s ease-in-out infinite; }}
    @keyframes pulse {{ 0%,100% {{opacity:.3}} 50% {{opacity:1}} }}
    .sink {{ animation:sinkcue 2.2s ease-in-out infinite; }}
    @keyframes sinkcue {{ 0%,100% {{transform:translateY(0);opacity:.5}} 50% {{transform:translateY(5px);opacity:1}} }}

    @media (prefers-reduced-motion: reduce) {{
      .ray,.w1,.w2,.ruler,.ping,.drift,.snow,.bub,.halo,.cursor,.pulse,.sink {{ animation:none; }}
      .ping,.bub {{ opacity:0; }}
    }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#water)"/>

    <!-- light from above -->
    <g>
      {rays}
    </g>
    <path class="w1" d="{wave(16, 7)}"/>
    <path class="w2" d="{wave(10, 5)}"/>

    <!-- sonar pings radiating from the name -->
    {rings}

    <!-- life -->
    {jb}
    <g>
    {snow(110, W, rmax=1.8)}
    </g>
    <g>
    {bubbles(22, 40, W - 40, H + 6)}
    </g>

    <!-- depth ruler -->
    <g class="ruler">{ticks}</g>
    <path d="M44 {H / 2:.0f} l7 -5 v10z" fill="{BIO}"/>
    <text class="depth" x="56" y="{H / 2 + 4:.0f}">0000 m</text>
    <text class="meta" x="56" y="{H / 2 + 20:.0f}" font-size="9.5">SURFACE</text>

    <!-- name block -->
    <path d="M{cx - 190:.0f} 122 h70 M{cx + 120:.0f} 122 h70" stroke="{BIO}" stroke-opacity=".45"/>
    <text class="eyebrow" x="{cx:.0f}" y="126" text-anchor="middle">SOFTWARE DEVELOPER</text>
    <g filter="url(#refract)">
      <text class="name halo" x="{cx:.0f}" y="{cy}" text-anchor="middle" filter="url(#soft)">ADITYA PADMARAJAN</text>
      <text class="name" x="{cx:.0f}" y="{cy}" text-anchor="middle" fill="{FOAM}">ADITYA<tspan fill="{BIO}"> PADMARAJAN</tspan></text>
    </g>

    <text class="sub" x="{cx:.0f}" y="{cy + 40}" text-anchor="middle">
      <tspan fill="{BIO}">&#8250;</tspan>
      <tspan class="subhi" dx="10">STEMCELL Technologies</tspan>
      <tspan dx="10">&#8212;</tspan>
      <tspan dx="10">CS @ UVic</tspan>
      <tspan dx="10">&#8212;</tspan>
      <tspan dx="10">Vancouver, BC</tspan>
      <tspan class="cursor" dx="10">&#9646;</tspan>
    </text>

    <!-- descent cue -->
    <g class="sink">
      <text class="meta" x="{cx:.0f}" y="{H - 40}" text-anchor="middle" fill="{BIO}" fill-opacity=".85">BEGIN DESCENT</text>
      <path d="M{cx - 6:.0f} {H - 30} l6 6 l6 -6" fill="none" stroke="{BIO}" stroke-width="1.4"/>
    </g>

    <!-- telemetry -->
    <circle class="pulse" cx="{W - 46}" cy="{H - 34}" r="3.5" fill="{BIO}"/>
    <text class="meta" x="{W - 60}" y="{H - 30}" text-anchor="end">SONAR ACTIVE &#183; 49.28&#176;N 123.12&#176;W &#183; SALISH SEA</text>

    <!-- overlays -->
    <rect width="{W}" height="{H}" fill="url(#vignette)"/>
    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="none" stroke="url(#edge)"/>
  </g>
</svg>
"""


# ── 2. DEPTH ZONE MARKERS ────────────────────────────────────────────────────
def zone(depth, name, layer, reading, note, idx):
    """A thin strip between sections; each one darker than the last."""
    W, H = 1000, 84
    base = ["#071833", "#040E22", "#020815"][idx]
    lx0, lx1, ly = 400, 740, 44

    ticks = "".join(
        f'<line x1="{x}" y1="{ly - (5 if (x - lx0) % 68 == 0 else 2)}" x2="{x}" y2="{ly + (5 if (x - lx0) % 68 == 0 else 2)}"/>'
        for x in range(lx0, lx1 + 1, 17)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{depth} metres, {name}">
  <title>{depth} m &#183; {name}</title>
  <defs>
    <linearGradient id="zbg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{base}"/>
      <stop offset="100%" stop-color="{ABYSS}"/>
    </linearGradient>
    <linearGradient id="zrule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{BIO}"  stop-opacity="0"/>
      <stop offset="30%"  stop-color="{BIO}"  stop-opacity=".6"/>
      <stop offset="70%"  stop-color="{VOLT}" stop-opacity=".5"/>
      <stop offset="100%" stop-color="{VOLT}" stop-opacity="0"/>
    </linearGradient>
    <filter id="zglow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="zf"><rect width="{W}" height="{H}" rx="4"/></clipPath>
  </defs>
  <style>
    .d  {{ font-family:{MONO}; font-size:30px; font-weight:700; fill:{BIO}; }}
    .u  {{ font-size:14px; font-weight:400; fill:{MUTE}; }}
    .zn {{ font-family:{MONO}; font-size:14px; font-weight:700; letter-spacing:3.2px; fill:{FOAM}; }}
    .zl {{ font-family:{MONO}; font-size:10px; letter-spacing:2.6px; fill:{MUTE}; }}
    .rd {{ font-family:{MONO}; font-size:11.5px; letter-spacing:1.6px; fill:{FOAM}; fill-opacity:.8; }}
    .nt {{ font-family:{MONO}; font-size:11px; font-style:italic; fill:{MUTE}; }}
    .blip {{ animation:travel 4.8s cubic-bezier(.5,0,.5,1) infinite; }}
    @keyframes travel {{ 0% {{transform:translateX(0);opacity:0}} 10%,90% {{opacity:1}} 100% {{transform:translateX({lx1 - lx0}px);opacity:0}} }}
    .chev {{ animation:chev 2s ease-in-out infinite; }}
    @keyframes chev {{ 0%,100% {{transform:translateY(-2px);opacity:.35}} 50% {{transform:translateY(3px);opacity:1}} }}
    {snow_css(H)}
    @media (prefers-reduced-motion: reduce) {{ .blip,.chev,.snow {{ animation:none; }} }}
  </style>
  <g clip-path="url(#zf)">
    <rect width="{W}" height="{H}" fill="url(#zbg)"/>
    {snow(16, W, rmax=1.3, opmax=.35)}
    <rect width="{W}" height="1" fill="url(#zrule)"/>
    <rect y="{H - 1}" width="{W}" height="1" fill="url(#zrule)" opacity=".5"/>

    <g class="chev" fill="none" stroke="{BIO}" stroke-width="1.4">
      <path d="M24 34 l6 6 l6 -6"/><path d="M24 42 l6 6 l6 -6" stroke-opacity=".5"/>
    </g>
    <text class="d" x="50" y="{H / 2 + 11:.0f}">{depth}<tspan class="u" dx="6">m</tspan></text>

    <text class="zn" x="186" y="38">{name}</text>
    <text class="zl" x="186" y="57">{layer}</text>

    <line x1="{lx0}" y1="{ly}" x2="{lx1}" y2="{ly}" stroke="{LINE}" stroke-width="1"/>
    <g stroke="{MUTE}" stroke-opacity=".6">{ticks}</g>
    <g class="blip"><circle cx="{lx0}" cy="{ly}" r="3" fill="{BIO}" filter="url(#zglow)"/></g>

    <text class="rd" x="{W - 28}" y="38" text-anchor="end">{reading}</text>
    <text class="nt" x="{W - 28}" y="57" text-anchor="end">{note}</text>
  </g>
</svg>
"""


# ── 3. BEACON CARDS ──────────────────────────────────────────────────────────
# Drawn on the same 18x18 grid, wireframe stroke, no filled brand marks, so the
# trio stays in the same visual language as the rest of the dive.
ICONS = {
    "globe": '<circle cx="9" cy="9" r="8"/><ellipse cx="9" cy="9" rx="3.6" ry="8"/><path d="M1.4 6h15.2M1.4 12h15.2"/>',
    "link":  '<path d="M7 11a4 4 0 0 0 5.7 0l2.6-2.6a4 4 0 1 0-5.7-5.7L8.2 4"/><path d="M11 7a4 4 0 0 0-5.7 0L2.7 9.6a4 4 0 1 0 5.7 5.7L9.8 14"/>',
    "mail":  '<rect x="1" y="3" width="16" height="12" rx="1.5"/><path d="M1.6 4.2 9 10l7.4-5.8"/>',
}


def card(label, target, icon, channel, primary, idx):
    """One beacon. Every card is the same 340x104 so the row tiles."""
    W, H = 340, 104
    ix, iy = 38, 52                         # icon centre
    tx = 76                                 # text column

    border_op = ".60" if primary else ".32"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{label} — {target}">
  <title>{label} &#8212; {target}</title>
  <defs>
    <linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="#061A3A"/>
      <stop offset="100%" stop-color="{ABYSS}"/>
    </linearGradient>
    <radialGradient id="cwell" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{BIO}" stop-opacity=".28"/>
      <stop offset="100%" stop-color="{BIO}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="cedge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="{BIO}"  stop-opacity="{border_op}"/>
      <stop offset="100%" stop-color="{VOLT}" stop-opacity="{border_op}"/>
    </linearGradient>
    <clipPath id="cf"><rect width="{W}" height="{H}" rx="6"/></clipPath>
  </defs>
  <style>
    .lb {{ font-family:{MONO}; font-size:15px; font-weight:700; letter-spacing:2.6px; fill:{FOAM}; }}
    .tg {{ font-family:{MONO}; font-size:10.5px; letter-spacing:.9px; fill:{MUTE}; }}
    .ch {{ font-family:{MONO}; font-size:9.5px; letter-spacing:2.4px; fill:{MUTE}; }}
    .ar {{ font-family:{MONO}; font-size:19px; font-weight:700; fill:{BIO}; animation:ar 2.6s ease-in-out infinite; }}
    @keyframes ar {{ 0%,100% {{transform:translateX(0);opacity:.55}} 50% {{transform:translateX(4px);opacity:1}} }}
    .dt {{ animation:dt 2.4s ease-in-out infinite; }}
    @keyframes dt {{ 0%,100% {{opacity:.25}} 50% {{opacity:1}} }}
    .ring {{ fill:none; stroke:{BIO}; stroke-width:1; vector-effect:non-scaling-stroke;
             transform-origin:{ix}px {iy}px; animation:ring 3.6s ease-out infinite; }}
    @keyframes ring {{ 0% {{transform:scale(.55);opacity:.8}} 100% {{transform:scale(2.2);opacity:0}} }}
    {snow_css(H)}
    @media (prefers-reduced-motion: reduce) {{
      .ar,.dt,.ring,.snow {{ animation:none; }}
      .ring {{ opacity:0 }}
    }}
  </style>

  <g clip-path="url(#cf)">
    <rect width="{W}" height="{H}" fill="url(#cbg)"/>
    {snow(10, W, rmax=1.2, opmax=.35)}

    <!-- channel tag -->
    <text class="ch" x="{W - 32}" y="24" text-anchor="end">{channel}</text>
    <circle class="dt" cx="{W - 20}" cy="20" r="3.2" fill="{BIO}" style="animation-delay:-{idx * .8:.1f}s"/>

    <!-- beacon: icon with sonar rings going out from it -->
    <circle cx="{ix}" cy="{iy}" r="30" fill="url(#cwell)"/>
    <circle class="ring" cx="{ix}" cy="{iy}" r="20" style="animation-delay:-{idx * 1.2:.1f}s"/>
    <circle class="ring" cx="{ix}" cy="{iy}" r="20" style="animation-delay:-{idx * 1.2 + 1.8:.1f}s"/>
    <circle cx="{ix}" cy="{iy}" r="18" fill="{ABYSS}" stroke="{BIO}" stroke-opacity="{border_op}"/>
    <g transform="translate({ix - 9},{iy - 9})" stroke="{BIO}" stroke-width="1.3" fill="none" stroke-linecap="round">{ICONS[icon]}</g>

    <!-- label + target -->
    <text class="lb" x="{tx}" y="{iy - 2}">{label}</text>
    <text class="tg" x="{tx}" y="{iy + 16}">{target}</text>

    <!-- enter arrow -->
    <text class="ar" x="{W - 22}" y="{H / 2 + 13:.0f}" text-anchor="end">&#8250;</text>

    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="none" stroke="url(#cedge)"/>
  </g>
</svg>
"""


# ── 4. SONAR CONTACT DOSSIER ─────────────────────────────────────────────────
def identity():
    """The whoami block as a sonar contact report: code on the left, live scope on the right."""
    STR = "#9CC8FF"   # string literal, pale tide blue

    W = 1000
    BAR = 36              # title bar height
    X0, LEAD = 30, 25     # code gutter x, line height
    KEY_X, VAL_X = 82, 178
    y0 = BAR + 48

    rows = [
        ("open",),
        ("pair", "role:",      "Software Developer @ STEMCELL Technologies"),
        ("pair", "education:", "B.Sc. Computer Science, University of Victoria"),
        ("pair", "based_in:",  "Vancouver, British Columbia"),
        ("close",),
        ("blank",),
        ("note", "&#47;&#47; below 1000 m the only light is the light you make"),
    ]

    code, ln = [], 1
    for i, row in enumerate(rows):
        y = y0 + i * LEAD
        code.append(f'<text class="gut" x="{X0}" y="{y}">{ln:02d}</text>')
        ln += 1
        t = f'<text class="cd" xml:space="preserve" y="{y}">'
        if row[0] == "open":
            t += '<tspan class="kw" x="64">const</tspan><tspan class="vr"> aditya</tspan><tspan class="op"> = {</tspan>'
        elif row[0] == "pair":
            t += (f'<tspan class="ky" x="{KEY_X}">{row[1]}</tspan>'
                  f'<tspan class="op" x="{VAL_X}">&quot;</tspan>'
                  f'<tspan class="st">{row[2]}</tspan>'
                  f'<tspan class="op">&quot;,</tspan>')
        elif row[0] == "close":
            t += '<tspan class="op" x="64">};</tspan>'
        elif row[0] == "note":
            t += f'<tspan class="cm" x="64">{row[1]}</tspan>'
        else:
            t += '<tspan x="64"> </tspan>'
        code.append(t + "</text>")
    # caret parks on the blank line under the closing brace
    code.append(f'<rect class="car" x="64" y="{y0 + 5 * LEAD - 11}" width="8.4" height="14"/>')
    code = "\n  ".join(code)

    H = y0 + (len(rows) - 1) * LEAD + 56
    cx, cy, R = 735, (BAR + H) / 2 - 10, 60

    def pt(deg, r=R):
        a = math.radians(deg)
        return cx + r * math.sin(a), cy - r * math.cos(a)

    # sweep: leading edge points straight up at t=0 and turns clockwise; the
    # trail behind it is a fan of thin wedges fading out
    fan = []
    for k in range(10):
        a1, a2 = -(k + 1) * 5, -k * 5
        (x1, y1), (x2, y2) = pt(a1), pt(a2)
        fan.append(f'<path d="M{cx} {cy:.1f} L{x1:.1f} {y1:.1f} A{R} {R} 0 0 1 {x2:.1f} {y2:.1f}Z" '
                   f'fill-opacity="{.38 * (1 - k / 10):.2f}"/>')
    fan = "".join(fan)
    ex, ey = pt(0)

    # contact on the scope; its flash is timed to the moment the sweep crosses it
    bx, by = cx + 26, cy - 31
    hit = math.degrees(math.atan2(bx - cx, cy - by)) / 360 * 100

    rings = "".join(
        f'<circle cx="{cx}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{BIO}" stroke-opacity="{op}"/>'
        for r, op in ((R, .45), (R * 2 / 3, .2), (R / 3, .2))
    )

    reads = [("SIGNAL", 0.93), ("LUMEN", 0.68), ("PRESSURE", 0.21)]
    ro = []
    for i, (lbl, frac) in enumerate(reads):
        ry = cy - 22 + i * 26
        ro.append(f'<text class="rd" x="828" y="{ry:.0f}">{lbl}</text>')
        ro.append(f'<rect x="904" y="{ry - 8:.0f}" width="66" height="6" rx="3" fill="{ABYSS}" stroke="{LINE}"/>')
        ro.append(f'<rect x="905" y="{ry - 7:.0f}" width="{64 * frac:.0f}" height="4" rx="2" fill="url(#ibar2)"/>')
    ro = "\n  ".join(ro)

    alt = ("Aditya Padmarajan — Software Developer at STEMCELL Technologies; "
           "B.Sc. Computer Science, University of Victoria; based in Vancouver, British Columbia")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{alt}">
  <title>{alt}</title>
  <defs>
    <linearGradient id="ipnl" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="#061A3A"/>
      <stop offset="62%"  stop-color="{PANEL}"/>
      <stop offset="100%" stop-color="{ABYSS}"/>
    </linearGradient>
    <linearGradient id="ibar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#0A2248"/>
      <stop offset="100%" stop-color="{PANEL}"/>
    </linearGradient>
    <linearGradient id="ibar2" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{TIDE}"/>
      <stop offset="100%" stop-color="{BIO}"/>
    </linearGradient>
    <radialGradient id="iscope" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{TIDE}" stop-opacity=".16"/>
      <stop offset="100%" stop-color="{ABYSS}" stop-opacity=".9"/>
    </radialGradient>
    <linearGradient id="iedge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="{BIO}"  stop-opacity=".40"/>
      <stop offset="100%" stop-color="{VOLT}" stop-opacity=".25"/>
    </linearGradient>
    <clipPath id="iframe"><rect width="{W}" height="{H}" rx="6"/></clipPath>
    <filter id="iglow" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .cd {{ font-family:{MONO}; font-size:14px; letter-spacing:.2px; }}
    .gut{{ font-family:{MONO}; font-size:11px; fill:{MUTE}; fill-opacity:.55; }}
    .kw {{ fill:#B49BFF; }}
    .vr {{ fill:{FOAM}; }}
    .ky {{ fill:{BIO}; }}
    .st {{ fill:{STR}; }}
    .op {{ fill:{MUTE}; }}
    .cm {{ fill:{MUTE}; fill-opacity:.75; font-style:italic; }}
    .tab{{ font-family:{MONO}; font-size:12px; font-weight:700; letter-spacing:2.2px; fill:{FOAM}; fill-opacity:.9; }}
    .meta{{font-family:{MONO}; font-size:10.5px; letter-spacing:2.4px; fill:{MUTE}; }}
    .rd {{ font-family:{MONO}; font-size:10.5px; letter-spacing:2.2px; fill:{MUTE}; }}
    .vk {{ font-family:{MONO}; font-size:10px; letter-spacing:3px; fill:{BIO}; fill-opacity:.85; }}
    .car{{ fill:{BIO}; fill-opacity:.75; animation:icar 1.05s steps(1) infinite; }}
    @keyframes icar {{ 0%,50% {{opacity:1}} 51%,100% {{opacity:0}} }}
    .sweep {{ transform-origin:{cx}px {cy:.1f}px; animation:spin 4s linear infinite; }}
    @keyframes spin {{ to {{transform:rotate(360deg)}} }}
    .blip {{ animation:blip 4s linear infinite; }}
    @keyframes blip {{ 0%,{hit:.1f}% {{opacity:.2}} {hit + .8:.1f}% {{opacity:1}} 70%,100% {{opacity:.2}} }}
    .echo {{ fill:none; stroke:{BIO}; stroke-width:1; vector-effect:non-scaling-stroke;
             transform-origin:{bx}px {by:.1f}px; animation:echo 4s ease-out infinite; }}
    @keyframes echo {{
      0%,{hit:.1f}% {{transform:scale(.3);opacity:0}}
      {hit + .8:.1f}% {{transform:scale(.3);opacity:.9}}
      {hit + 30:.1f}%,100% {{transform:scale(2.4);opacity:0}}
    }}
    .dot {{ animation:ipulse 2.2s ease-in-out infinite; }}
    @keyframes ipulse {{ 0%,100% {{opacity:.25}} 50% {{opacity:1}} }}
    {snow_css(H)}
    @media (prefers-reduced-motion: reduce) {{
      .car,.sweep,.blip,.echo,.dot,.snow {{ animation:none; }}
      .echo {{ opacity:0 }}
    }}
  </style>

  <g clip-path="url(#iframe)">
    <rect width="{W}" height="{H}" fill="url(#ipnl)"/>
    {snow(34, W, rmax=1.4, opmax=.32)}

    <!-- title bar -->
    <rect width="{W}" height="{BAR}" fill="url(#ibar)"/>
    <rect x="0" y="{BAR - 1}" width="{W}" height="1" fill="{LINE}"/>
    <circle cx="26" cy="{BAR / 2:.0f}" r="3.6" fill="{BIO}" class="dot"/>
    <text class="tab" x="42" y="{BAR / 2 + 4:.0f}">IDENTITY.TS</text>
    <text class="meta" x="{W - 30}" y="{BAR / 2 + 4:.0f}" text-anchor="end">DIVE LOG 001 &#183; CONTACT ACQUIRED</text>

    <!-- code -->
    <rect x="0" y="{BAR}" width="3" height="{H - BAR}" fill="{BIO}" fill-opacity=".7"/>
    {code}

    <!-- divider -->
    <line x1="630" y1="{BAR + 22}" x2="630" y2="{H - 22}" stroke="{LINE}" stroke-width="1"/>

    <!-- sonar scope -->
    <circle cx="{cx}" cy="{cy:.1f}" r="{R}" fill="url(#iscope)"/>
    {rings}
    <path d="M{cx - R} {cy:.1f} h{2 * R} M{cx} {cy - R:.1f} v{2 * R}" stroke="{BIO}" stroke-opacity=".15"/>
    <g class="sweep">
      <g fill="{BIO}">{fan}</g>
      <line x1="{cx}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{BIO}" stroke-width="1.4"/>
    </g>
    <circle class="echo" cx="{bx}" cy="{by:.1f}" r="8"/>
    <circle class="blip" cx="{bx}" cy="{by:.1f}" r="3.2" fill="{BIO}" filter="url(#iglow)"/>
    <circle cx="{cx}" cy="{cy:.1f}" r="2" fill="{FOAM}"/>
    <text class="vk" x="{cx}" y="{cy + R + 22:.0f}" text-anchor="middle">CONTACT 01 &#183; 040&#176;</text>

    <!-- readouts -->
    <text class="vk" x="828" y="{cy - 46:.0f}" fill="{VOLT}">TELEMETRY</text>
    {ro}
    <text class="meta" x="828" y="{cy + R + 22:.0f}">IDENTIFIED</text>

    <!-- footer -->
    <text class="meta" x="64" y="{H - 16}">49.28&#176;N 123.12&#176;W &#183; SALISH SEA</text>
    <text class="meta" x="{W - 30}" y="{H - 16}" text-anchor="end">DEPTH 0200 m &#183; HOLDING</text>

    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="none" stroke="url(#iedge)"/>
  </g>
</svg>
"""


# ── 5. THE FLOOR ─────────────────────────────────────────────────────────────
def floor():
    """Bottom of the dive: an anglerfish, a vent, a few things watching you in the dark."""
    W, H = 1000, 240
    tx = 610   # text column centre

    # pairs of eyes that open, hold, and close at random
    eyes = []
    for x, y in [(70, 44), (488, 30), (930, 56), (820, 118), (150, 196), (980, 160), (420, 80)]:
        c = random.choice([BIO, VOLT])
        eyes.append(
            f'<g class="eye" style="animation-delay:-{random.uniform(0, 11):.1f}s">'
            f'<circle cx="{x}" cy="{y}" r="1.4" fill="{c}"/><circle cx="{x + 5}" cy="{y}" r="1.4" fill="{c}"/></g>'
        )
    eyes = "\n    ".join(eyes)

    # teeth along the upper and lower jaw lines
    upper = "".join(f"M{x} {128 - (x - 346) * 6 / 26:.1f} l1.5 3.5 l1.5 -3.5 " for x in (350, 355, 360, 365))
    lower = "".join(f"M{x} {128 + (x - 346) * 8 / 26:.1f} l1.5 -3.5 l1.5 3.5 " for x in (350, 355, 360, 365))

    seabed = ("M0 206 C120 188 220 202 340 194 C470 184 560 206 700 198 "
              f"C820 191 900 204 {W} 192 L{W} {H} L0 {H}Z")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="10,935 metres, Challenger Deep. You've reached the bottom. Click to resurface.">
  <title>10,935 m &#183; you've reached the bottom</title>
  <defs>
    <linearGradient id="fbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{DEEP}"/>
      <stop offset="100%" stop-color="{ABYSS}"/>
    </linearGradient>
    <radialGradient id="lure" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{BIO}" stop-opacity=".30"/>
      <stop offset="45%"  stop-color="{BIO}" stop-opacity=".08"/>
      <stop offset="100%" stop-color="{BIO}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="vent" cx="50%" cy="100%" r="80%">
      <stop offset="0%"   stop-color="{VOLT}" stop-opacity=".35"/>
      <stop offset="100%" stop-color="{VOLT}" stop-opacity="0"/>
    </radialGradient>
    <filter id="fglow" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="ff"><rect width="{W}" height="{H}" rx="6"/></clipPath>
  </defs>
  <style>
    .big {{ font-family:{MONO}; font-size:40px; font-weight:700; letter-spacing:4px; fill:{BIO}; }}
    .zn  {{ font-family:{MONO}; font-size:12px; font-weight:700; letter-spacing:4px; fill:{FOAM}; }}
    .nt  {{ font-family:{MONO}; font-size:12px; font-style:italic; fill:{MUTE}; }}
    .up  {{ font-family:{MONO}; font-size:10.5px; letter-spacing:3px; fill:{BIO}; }}
    .eye {{ animation:eye 11s ease-in-out infinite; }}
    @keyframes eye {{ 0%,62%,100% {{opacity:0}} 66%,80% {{opacity:.9}} 81% {{opacity:0}} 82%,86% {{opacity:.9}} }}
    .fish {{ animation:swim 10s ease-in-out infinite; }}
    @keyframes swim {{ 0%,100% {{transform:translate(0,0)}} 50% {{transform:translate(14px,-6px)}} }}
    .rod {{ transform-origin:322px 90px; animation:bob 3.6s ease-in-out infinite alternate; }}
    @keyframes bob {{ from {{transform:rotate(-4deg)}} to {{transform:rotate(5deg)}} }}
    .halo {{ animation:halo 3.6s ease-in-out infinite; }}
    @keyframes halo {{ 0%,100% {{opacity:.7}} 50% {{opacity:1}} }}
    .rise {{ animation:upcue 2.2s ease-in-out infinite; }}
    @keyframes upcue {{ 0%,100% {{transform:translateY(0);opacity:.55}} 50% {{transform:translateY(-4px);opacity:1}} }}
    {snow_css(H)}
    {bubble_css(150)}
    @media (prefers-reduced-motion: reduce) {{
      .eye,.fish,.rod,.halo,.rise,.snow,.bub {{ animation:none; }}
      .eye {{ opacity:.6 }} .bub {{ opacity:0 }}
    }}
  </style>

  <g clip-path="url(#ff)">
    <rect width="{W}" height="{H}" fill="url(#fbg)"/>
    {snow(40, W, rmax=1.3, opmax=.3)}
    {eyes}

    <!-- hydrothermal vent -->
    <ellipse cx="878" cy="190" rx="70" ry="60" fill="url(#vent)"/>
    {bubbles(9, 870, 886, 160, rmax=2.6)}
    <path d="M862 196 L870 160 L886 160 L896 194Z" fill="#050F24" stroke="{LINE}"/>

    <!-- seabed -->
    <path d="{seabed}" fill="#020815" stroke="{LINE}"/>

    <!-- anglerfish -->
    <g class="fish">
      <circle class="halo" cx="374" cy="66" r="90" fill="url(#lure)"/>
      <path d="M244 126 L212 102 C218 118 218 136 212 152Z" fill="#06132B" stroke="#1C3C6E"/>
      <path d="M244 126 C244 98 286 82 326 90 C350 96 366 110 372 122 L346 128 L372 136 C364 154 336 166 300 164 C266 162 244 150 244 126Z"
            fill="#06132B" stroke="#1C3C6E" stroke-width="1.2"/>
      <path d="M290 140 C300 150 300 158 286 160 C284 152 284 146 290 140Z" fill="#081A38" stroke="#1C3C6E"/>
      <path d="{upper}{lower}" fill="none" stroke="{FOAM}" stroke-opacity=".75" stroke-width=".9"/>
      <circle cx="338" cy="110" r="3.4" fill="{ABYSS}" stroke="{BIO}" stroke-opacity=".6"/>
      <circle cx="337" cy="109" r="1" fill="{FOAM}"/>
      <g class="rod">
        <path d="M322 90 C326 64 350 52 372 62" fill="none" stroke="#2A4F86" stroke-width="1.4"/>
        <circle cx="374" cy="66" r="4.5" fill="{BIO}" filter="url(#fglow)"/>
      </g>
    </g>

    <!-- sign-off -->
    <text class="big" x="{tx}" y="96" text-anchor="middle">10,935<tspan font-size="18" fill="{MUTE}" dx="8">m</tspan></text>
    <text class="zn" x="{tx}" y="122" text-anchor="middle">HADAL ZONE &#183; CHALLENGER DEEP</text>
    <text class="nt" x="{tx}" y="146" text-anchor="middle">you've reached the bottom. thanks for diving.</text>
    <g class="rise">
      <path d="M{tx - 6} 176 l6 -6 l6 6" fill="none" stroke="{BIO}" stroke-width="1.4"/>
      <text class="up" x="{tx}" y="192" text-anchor="middle">RESURFACE</text>
    </g>

    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="none" stroke="{LINE}"/>
  </g>
</svg>
"""


if __name__ == "__main__":
    print("Generating assets...")
    write("banner.svg", banner())
    write("identity.svg", identity())
    write("floor.svg", floor())
    for i, (fn, depth, name, layer, reading, note) in enumerate([
        ("zone-twilight", "200",   "TWILIGHT ZONE", "MESOPELAGIC",   "&#8776; 21 ATM &#183; LIGHT 1%",  "sunlight gives out here"),
        ("zone-abyss",    "4,000", "ABYSSAL ZONE",  "ABYSSOPELAGIC", "&#8776; 401 ATM &#183; 2&#176;C",  "send a signal, someone's listening"),
    ]):
        write(f"{fn}.svg", zone(depth, name, layer, reading, note, i))
    for j, (fn, label, target, icon, chan, primary) in enumerate([
        ("btn-portfolio", "PORTFOLIO", "adityapadmarajan.com",        "globe", "BEACON.01", True),
        ("btn-linkedin",  "LINKEDIN",  "in/aditya-padmarajan",        "link",  "BEACON.02", False),
        ("btn-email",     "EMAIL",     "aditya.padmarajan@gmail.com", "mail",  "BEACON.03", False),
    ]):
        write(f"{fn}.svg", card(label, target, icon, chan, primary, j))
    print("Done.")
