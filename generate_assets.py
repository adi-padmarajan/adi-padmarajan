#!/usr/bin/env python3
"""
Generates the animated SVG assets for adi-padmarajan's profile README.
Palette grounded in Blade Runner 2049: amber primary, ice-cyan secondary,
bone text on near-black panels.

Run:  python3 generate_assets.py
Out:  assets/*.svg
"""

import os
import random

random.seed(2049)

OUT = "assets"
os.makedirs(OUT, exist_ok=True)

# ── design tokens ────────────────────────────────────────────────────────────
VOID   = "#07090C"   # deepest background
PANEL  = "#0B0F14"   # panel fill
LINE   = "#1C2530"   # hairline / border
ASH    = "#5A6672"   # muted text
BONE   = "#E8E3D9"   # primary text
AMBER  = "#FF8A3D"   # primary accent
ICE    = "#22D3EE"   # secondary accent
RUST   = "#C2410C"   # deep amber shadow

MONO = "ui-monospace,'SF Mono','JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace"


def write(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {path}  ({len(content):,} bytes)")


# ── 1. HERO BANNER ───────────────────────────────────────────────────────────
def banner():
    W, H = 1200, 360

    # Blade Runner rain: thin diagonal streaks, staggered
    rain = []
    for i in range(70):
        x = random.randint(-60, W + 60)
        ln = random.randint(18, 46)
        dur = round(random.uniform(0.9, 2.1), 2)
        delay = round(random.uniform(0, 2.1), 2)
        op = round(random.uniform(0.10, 0.34), 2)
        rain.append(
            f'<line class="rain" x1="{x}" y1="-{ln}" x2="{x-9}" y2="0" '
            f'stroke-opacity="{op}" style="animation-duration:{dur}s;animation-delay:-{delay}s"/>'
        )
    rain = "\n    ".join(rain)

    # Perspective horizon grid: verticals converging on a vanishing point
    vp_x, vp_y = W / 2, 236
    verts = []
    for i in range(-14, 15):
        x_end = vp_x + i * 96
        verts.append(f'<line x1="{vp_x}" y1="{vp_y}" x2="{x_end:.0f}" y2="{H}" />')
    verts = "\n      ".join(verts)

    horz = []
    for i, y in enumerate([242, 252, 266, 286, 312, 344]):
        horz.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke-opacity="{0.30 - i*0.04:.2f}" />')
    horz = "\n      ".join(horz)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Aditya Padmarajan — Software Developer">
  <title>Aditya Padmarajan — Software Developer</title>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{VOID}"/>
      <stop offset="58%"  stop-color="#0C1016"/>
      <stop offset="100%" stop-color="#160D07"/>
    </linearGradient>
    <radialGradient id="sun" cx="50%" cy="66%" r="46%">
      <stop offset="0%"   stop-color="{AMBER}" stop-opacity="0.40"/>
      <stop offset="45%"  stop-color="{RUST}"  stop-opacity="0.14"/>
      <stop offset="100%" stop-color="{RUST}"  stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="gridfade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#fff" stop-opacity="0"/>
      <stop offset="30%"  stop-color="#fff" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <mask id="gridmask"><rect x="0" y="230" width="{W}" height="130" fill="url(#gridfade)"/></mask>
    <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{ICE}" stop-opacity="0"/>
      <stop offset="50%"  stop-color="{ICE}" stop-opacity="0.13"/>
      <stop offset="100%" stop-color="{ICE}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.4" fill="#000" fill-opacity="0.30"/>
    </pattern>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="7" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="frame"><rect x="0" y="0" width="{W}" height="{H}" rx="3"/></clipPath>
  </defs>

  <style>
    .rain {{ stroke:{ICE}; stroke-width:1.1; animation-name:fall; animation-timing-function:linear; animation-iteration-count:infinite; }}
    @keyframes fall {{ from {{ transform:translateY(0); }} to {{ transform:translateY(420px); }} }}

    .grid {{ stroke:{AMBER}; stroke-width:0.8; stroke-opacity:0.26; }}
    .gridh {{ stroke:{AMBER}; stroke-width:0.8; animation:creep 5.5s linear infinite; }}
    @keyframes creep {{ from {{ transform:translateY(0); }} to {{ transform:translateY(26px); }} }}

    .name  {{ font-family:{MONO}; font-size:60px; font-weight:700; letter-spacing:7px; }}
    .g1 {{ fill:{ICE};   animation:gl1 6.5s steps(1) infinite; }}
    .g2 {{ fill:#FF2E88; animation:gl2 6.5s steps(1) infinite; }}
    @keyframes gl1 {{
      0%,6%,100% {{ opacity:0; transform:translate(0,0); }}
      7%  {{ opacity:.85; transform:translate(-4px,1px); }}
      9%  {{ opacity:0; }}
      41% {{ opacity:.7;  transform:translate(3px,-2px); }}
      43% {{ opacity:0; }}
    }}
    @keyframes gl2 {{
      0%,6%,100% {{ opacity:0; transform:translate(0,0); }}
      7.5%{{ opacity:.7;  transform:translate(4px,-1px); }}
      9.5%{{ opacity:0; }}
      41.5%{{opacity:.6;  transform:translate(-3px,2px); }}
      43.5%{{opacity:0; }}
    }}
    .slice {{ animation:slice 6.5s steps(1) infinite; }}
    @keyframes slice {{
      0%,7%,100% {{ transform:translateX(0); }}
      7.5% {{ transform:translateX(13px); }}
      8.5% {{ transform:translateX(-7px); }}
      9.5% {{ transform:translateX(0); }}
      42%  {{ transform:translateX(-9px); }}
      43%  {{ transform:translateX(0); }}
    }}

    .eyebrow {{ font-family:{MONO}; font-size:13px; letter-spacing:5.5px; fill:{AMBER}; fill-opacity:.9; }}
    .sub     {{ font-family:{MONO}; font-size:15.5px; letter-spacing:1.2px; fill:{ASH}; }}
    .subhi   {{ fill:{BONE}; }}
    .meta    {{ font-family:{MONO}; font-size:11px; letter-spacing:2.4px; fill:{ASH}; fill-opacity:.75; }}

    .cursor {{ fill:{AMBER}; animation:blink 1.05s steps(1) infinite; }}
    @keyframes blink {{ 0%,50% {{opacity:1}} 51%,100% {{opacity:0}} }}

    .sweepbar {{ animation:sweep 7s cubic-bezier(.4,0,.6,1) infinite; }}
    @keyframes sweep {{ 0% {{transform:translateY(-90px)}} 100% {{transform:translateY(400px)}} }}

    .hud {{ stroke:{AMBER}; stroke-width:1.4; fill:none; stroke-opacity:.55; }}
    .pulse {{ animation:pulse 3.2s ease-in-out infinite; }}
    @keyframes pulse {{ 0%,100% {{opacity:.35}} 50% {{opacity:1}} }}

    @media (prefers-reduced-motion: reduce) {{
      .rain,.gridh,.g1,.g2,.slice,.cursor,.sweepbar,.pulse {{ animation:none; }}
      .g1,.g2 {{ opacity:0; }}
    }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <rect width="{W}" height="{H}" fill="url(#sun)"/>

    <!-- horizon grid -->
    <g mask="url(#gridmask)">
      <g class="grid">
      {verts}
      </g>
      <g class="gridh">
      {horz}
      </g>
    </g>

    <!-- rain -->
    <g>
    {rain}
    </g>

    <!-- name block -->
    <g class="slice">
      <text class="eyebrow" x="{W/2:.0f}" y="116" text-anchor="middle">SOFTWARE DEVELOPER</text>
      <g filter="url(#glow)">
        <text class="name g1" x="{W/2:.0f}" y="182" text-anchor="middle">ADITYA<tspan> PADMARAJAN</tspan></text>
        <text class="name g2" x="{W/2:.0f}" y="182" text-anchor="middle">ADITYA<tspan> PADMARAJAN</tspan></text>
        <text class="name" x="{W/2:.0f}" y="182" text-anchor="middle" fill="{BONE}">ADITYA<tspan fill="{AMBER}"> PADMARAJAN</tspan></text>
      </g>
    </g>

    <text class="sub" x="{W/2:.0f}" y="217" text-anchor="middle">
      <tspan fill="{AMBER}">&#8250;</tspan>
      <tspan class="subhi" dx="10">STEMCELL Technologies</tspan>
      <tspan dx="10">&#8212;</tspan>
      <tspan dx="10">CS @ UVic</tspan>
      <tspan dx="10">&#8212;</tspan>
      <tspan dx="10">Vancouver, BC</tspan>
      <tspan class="cursor" dx="10">&#9646;</tspan>
    </text>

    <!-- HUD corner brackets -->
    <g class="hud">
      <path d="M18 44 L18 18 L44 18"/>
      <path d="M{W-44} 18 L{W-18} 18 L{W-18} 44"/>
      <path d="M18 {H-44} L18 {H-18} L44 {H-18}"/>
      <path d="M{W-44} {H-18} L{W-18} {H-18} L{W-18} {H-44}"/>
    </g>
    <circle class="pulse" cx="{W-60}" cy="{H-42}" r="3.5" fill="{ICE}"/>
    <text class="meta" x="{W-78}" y="{H-38}" text-anchor="end">SYS.ONLINE &#183; 49.28&#176;N 123.12&#176;W</text>
    <g transform="translate(62,{H-46})" stroke="{AMBER}" stroke-opacity=".7" fill="none" stroke-width="1.2">
      <path d="M7 12 C7 5 7 2 7 0 C7 2 7 5 7 12"/>
      <path d="M7 12 C2 8 0 5 0.5 2 C3 3 6 7 7 12"/>
      <path d="M7 12 C12 8 14 5 13.5 2 C11 3 8 7 7 12"/>
      <path d="M0 12 h14"/>
    </g>
    <text class="meta" x="86" y="{H-38}">SOLITUDE IN SILENCE</text>

    <!-- overlays -->
    <rect class="sweepbar" width="{W}" height="90" fill="url(#sweep)"/>
    <rect width="{W}" height="{H}" fill="url(#scan)"/>
    <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="3" fill="none" stroke="{AMBER}" stroke-opacity="0.30"/>
  </g>
</svg>
"""


# ── 2. SECTION HEADERS ───────────────────────────────────────────────────────
def header(cmd, note, idx):
    W, H = 1000, 60
    ticks = "".join(
        f'<rect x="{600 + i*11}" y="{26 + (i % 3) * 3}" width="2" height="{10 - (i % 3)*3}" fill="{AMBER}" fill-opacity="{0.18 + (i%4)*0.12:.2f}"/>'
        for i in range(16)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{cmd}">
  <title>{cmd}</title>
  <defs>
    <linearGradient id="p{idx}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#101720"/>
      <stop offset="70%"  stop-color="{PANEL}"/>
      <stop offset="100%" stop-color="{VOID}"/>
    </linearGradient>
    <linearGradient id="r{idx}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{AMBER}" stop-opacity=".9"/>
      <stop offset="100%" stop-color="{AMBER}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    .c{idx} {{ font-family:{MONO}; font-size:19px; font-weight:700; letter-spacing:1.6px; fill:{BONE}; }}
    .n{idx} {{ font-family:{MONO}; font-size:11px; letter-spacing:3px; fill:{ASH}; }}
    .k{idx} {{ fill:{AMBER}; }}
    .cur{idx} {{ fill:{ICE}; animation:bl{idx} 1.05s steps(1) infinite; }}
    @keyframes bl{idx} {{ 0%,50% {{opacity:1}} 51%,100% {{opacity:0}} }}
    @media (prefers-reduced-motion: reduce) {{ .cur{idx} {{ animation:none; }} }}
  </style>
  <rect width="{W}" height="{H}" rx="2" fill="url(#p{idx})"/>
  <rect x="0" y="0" width="3" height="{H}" fill="{AMBER}"/>
  <rect x="0" y="{H-1}" width="{W}" height="1" fill="url(#r{idx})"/>
  <text class="c{idx}" x="26" y="37"><tspan class="k{idx}">&#8250;</tspan><tspan dx="12">{cmd}</tspan><tspan class="cur{idx}" dx="6">&#9646;</tspan></text>
  <text class="n{idx}" x="{W-30}" y="36" text-anchor="end">{note}</text>
  {ticks}
</svg>
"""


# ── 3. DIVIDER ───────────────────────────────────────────────────────────────
def divider():
    W, H = 1000, 22
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="presentation">
  <defs>
    <linearGradient id="dl" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{AMBER}" stop-opacity="0"/>
      <stop offset="18%"  stop-color="{AMBER}" stop-opacity=".55"/>
      <stop offset="82%"  stop-color="{ICE}"   stop-opacity=".55"/>
      <stop offset="100%" stop-color="{ICE}"   stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    .pkt {{ animation:run 4.5s linear infinite; }}
    .pkt2 {{ animation:run 4.5s linear infinite; animation-delay:-2.25s; }}
    @keyframes run {{ from {{ transform:translateX(-40px); }} to {{ transform:translateX({W+40}px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .pkt,.pkt2 {{ animation:none; opacity:.4 }} }}
  </style>
  <line x1="0" y1="11" x2="{W}" y2="11" stroke="url(#dl)" stroke-width="1.2"/>
  <g class="pkt"><rect x="0" y="9" width="34" height="3" rx="1.5" fill="{AMBER}" fill-opacity=".85"/></g>
  <g class="pkt2"><rect x="0" y="9" width="18" height="3" rx="1.5" fill="{ICE}" fill-opacity=".7"/></g>
  <rect x="{W/2-1:.0f}" y="6" width="2" height="10" fill="{AMBER}" fill-opacity=".5"/>
</svg>
"""


# ── 4. STACK HUD ─────────────────────────────────────────────────────────────
def stack():
    groups = [
        ("LANGUAGES", [
            ("TypeScript", "#3178C6"), ("JavaScript", "#F7DF1E"), ("Python", "#3776AB"),
            ("Java", "#E8E3D9"), ("C", "#A8B9CC"), ("SQL", "#4169E1"),
        ]),
        ("FRAMEWORKS", [
            ("React", "#61DAFB"), ("Next.js", "#E8E3D9"), ("Node.js", "#5FA04E"),
            ("Tailwind", "#06B6D4"), ("FastAPI", "#009688"), ("Supabase", "#3FCF8E"),
        ]),
        ("DATA / ML", [
            ("pandas", "#E8E3D9"), ("NumPy", "#4DABCF"), ("scikit-learn", "#F7931E"),
            ("Jupyter", "#F37626"), ("Gemini", "#8E75B2"),
        ]),
        ("TOOLING", [
            ("Git", "#F05032"), ("Docker", "#2496ED"), ("Vercel", "#E8E3D9"),
            ("Figma", "#F24E1E"), ("Linux", "#FCC624"), ("Postgres", "#4169E1"),
        ]),
    ]

    W = 1000
    PAD_X, ROW_H, CHIP_H = 30, 30, 26
    y = 54
    body = []

    for gi, (label, items) in enumerate(groups):
        body.append(f'<text class="lbl" x="{PAD_X}" y="{y}">{label}</text>')
        body.append(f'<line x1="{PAD_X}" y1="{y+8}" x2="{W-PAD_X}" y2="{y+8}" stroke="{LINE}" stroke-width="1"/>')
        y += 24
        x = PAD_X
        for name, colour in items:
            w = int(len(name) * 7.4) + 34
            if x + w > W - PAD_X:
                x = PAD_X
                y += CHIP_H + 8
            body.append(
                f'<g><rect x="{x}" y="{y}" width="{w}" height="{CHIP_H}" rx="3" fill="#0F151C" stroke="{LINE}"/>'
                f'<circle cx="{x+14}" cy="{y+CHIP_H/2:.0f}" r="3.2" fill="{colour}"/>'
                f'<text class="chip" x="{x+25}" y="{y+17}">{name}</text></g>'
            )
            x += w + 7
        y += CHIP_H + 26

    H = y + 6
    body = "\n  ".join(body)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Technical stack">
  <title>Technical stack</title>
  <style>
    .lbl  {{ font-family:{MONO}; font-size:11px; font-weight:700; letter-spacing:3.4px; fill:{AMBER}; }}
    .chip {{ font-family:{MONO}; font-size:12.5px; fill:{BONE}; fill-opacity:.88; }}
    .hd   {{ font-family:{MONO}; font-size:11px; letter-spacing:2.6px; fill:{ASH}; }}
  </style>
  <rect width="{W}" height="{H}" rx="3" fill="{PANEL}" stroke="{LINE}"/>
  <rect x="0" y="0" width="3" height="{H}" fill="{ICE}" fill-opacity=".55"/>
  <text class="hd" x="{W-30}" y="26" text-anchor="end">stack.manifest</text>
  {body}
</svg>
"""


# ── 5. LINK CARDS ────────────────────────────────────────────────────────────
# Drawn on the same 18x18 grid, wireframe stroke — no filled brand marks, so the
# trio stays in the same visual language as the banner and the identity panel.
ICONS = {
    "globe": '<circle cx="9" cy="9" r="8"/><ellipse cx="9" cy="9" rx="3.6" ry="8"/><path d="M1.4 6h15.2M1.4 12h15.2"/>',
    "link":  '<path d="M7 11a4 4 0 0 0 5.7 0l2.6-2.6a4 4 0 1 0-5.7-5.7L8.2 4"/><path d="M11 7a4 4 0 0 0-5.7 0L2.7 9.6a4 4 0 1 0 5.7 5.7L9.8 14"/>',
    "mail":  '<rect x="1" y="3" width="16" height="12" rx="1.5"/><path d="M1.6 4.2 9 10l7.4-5.8"/>',
}


def card(label, target, icon, channel, primary, idx):
    """One console channel. Every card is the same 340x104 so the row tiles."""
    W, H = 340, 104
    i = 30 + idx

    box_x, box_y, box = 20, 34, 36          # icon well
    tx = box_x + box + 18                   # text column

    border_op = ".58" if primary else ".30"
    tint_op   = ".07" if primary else ".03"

    streaks = []
    for _ in range(7):
        rx, rl = random.randint(0, W), random.randint(10, 26)
        streaks.append(
            f'<line class="rn{i}" x1="{rx}" y1="-{rl}" x2="{rx-5}" y2="0" '
            f'stroke-opacity="{random.uniform(.06,.16):.2f}" '
            f'style="animation-duration:{random.uniform(1.2,2.6):.2f}s;'
            f'animation-delay:-{random.uniform(0,2.6):.2f}s"/>'
        )
    rain = "\n    ".join(streaks)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{label} — {target}">
  <title>{label} &#8212; {target}</title>
  <defs>
    <linearGradient id="bg{i}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="#0D131A"/>
      <stop offset="64%"  stop-color="{PANEL}"/>
      <stop offset="100%" stop-color="{VOID}"/>
    </linearGradient>
    <linearGradient id="rule{i}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{AMBER}" stop-opacity=".85"/>
      <stop offset="100%" stop-color="{AMBER}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="swp{i}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{ICE}" stop-opacity="0"/>
      <stop offset="50%"  stop-color="{ICE}" stop-opacity=".10"/>
      <stop offset="100%" stop-color="{ICE}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="sc{i}" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.4" fill="#000" fill-opacity="0.26"/>
    </pattern>
    <clipPath id="fr{i}"><rect width="{W}" height="{H}" rx="3"/></clipPath>
  </defs>
  <style>
    .lb{i} {{ font-family:{MONO}; font-size:15px; font-weight:700; letter-spacing:2.6px; fill:{BONE}; }}
    .tg{i} {{ font-family:{MONO}; font-size:10.5px; letter-spacing:.9px; fill:{ASH}; }}
    .ch{i} {{ font-family:{MONO}; font-size:9.5px; letter-spacing:2.4px; fill:{ASH}; fill-opacity:.8; }}
    .ar{i} {{ font-family:{MONO}; font-size:19px; font-weight:700; fill:{AMBER}; animation:ar{i} 2.6s ease-in-out infinite; }}
    @keyframes ar{i} {{ 0%,100% {{transform:translateX(0);opacity:.55}} 50% {{transform:translateX(4px);opacity:1}} }}
    .dt{i} {{ animation:dt{i} 2.4s ease-in-out infinite; }}
    @keyframes dt{i} {{ 0%,100% {{opacity:.25}} 50% {{opacity:1}} }}
    .rn{i} {{ stroke:{ICE}; stroke-width:1; animation-name:fl{i}; animation-timing-function:linear; animation-iteration-count:infinite; }}
    @keyframes fl{i} {{ from {{transform:translateY(0)}} to {{transform:translateY({H+30}px)}} }}
    .sw{i} {{ animation:sw{i} 9s ease-in-out infinite; animation-delay:-{idx*3}s; }}
    @keyframes sw{i} {{ 0%,100% {{transform:translateY(-60px)}} 50% {{transform:translateY({H}px)}} }}
    .bar{i} {{ animation:bar{i} 5s ease-in-out infinite; animation-delay:-{idx}s; }}
    @keyframes bar{i} {{ 0%,100% {{opacity:.35}} 50% {{opacity:.95}} }}
    @media (prefers-reduced-motion: reduce) {{
      .ar{i},.dt{i},.rn{i},.sw{i},.bar{i} {{ animation:none; }}
      .rn{i} {{ opacity:.16 }}
    }}
  </style>

  <g clip-path="url(#fr{i})">
    <rect width="{W}" height="{H}" fill="url(#bg{i})"/>
    <rect width="{W}" height="{H}" fill="{AMBER}" fill-opacity="{tint_op}"/>
    {rain}

    <!-- accent rail + bottom rule -->
    <rect class="bar{i}" x="0" y="0" width="3" height="{H}" fill="{AMBER}"/>
    <rect x="0" y="{H-1}" width="{W}" height="1" fill="url(#rule{i})"/>

    <!-- channel tag -->
    <text class="ch{i}" x="{W-32}" y="26" text-anchor="end">{channel}</text>
    <circle class="dt{i}" cx="{W-20}" cy="22" r="3.2" fill="{AMBER}"/>

    <!-- icon well -->
    <rect x="{box_x}" y="{box_y}" width="{box}" height="{box}" rx="3"
          fill="{VOID}" stroke="{AMBER}" stroke-opacity="{border_op}"/>
    <g transform="translate({box_x + box/2 - 9:.0f},{box_y + box/2 - 9:.0f})"
       stroke="{ICE}" stroke-width="1.3" fill="none" stroke-linecap="round">{ICONS[icon]}</g>

    <!-- label + target -->
    <text class="lb{i}" x="{tx}" y="{box_y+16}">{label}</text>
    <text class="tg{i}" x="{tx}" y="{box_y+34}">{target}</text>

    <!-- enter arrow -->
    <text class="ar{i}" x="{W-22}" y="{H/2+13:.0f}" text-anchor="end">&#8250;</text>

    <!-- hud corners -->
    <g fill="none" stroke="{AMBER}" stroke-opacity=".45" stroke-width="1.2">
      <path d="M10 22 L10 12 L20 12"/>
      <path d="M{W-20} {H-12} L{W-10} {H-12} L{W-10} {H-22}"/>
    </g>

    <!-- overlays -->
    <rect class="sw{i}" width="{W}" height="60" fill="url(#swp{i})"/>
    <rect width="{W}" height="{H}" fill="url(#sc{i})"/>
    <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="3" fill="none"
          stroke="{AMBER}" stroke-opacity="{border_op}"/>
  </g>
</svg>
"""

# ── 6. IDENTITY DOSSIER ──────────────────────────────────────────────────────
def identity():
    """The whoami block as an ESPER-style case file instead of a plain code fence."""
    STR = "#FFB27A"   # string literal — warm amber-bone

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
        ("note", "&#47;&#47; baseline &#8212; cells interlinked within cells interlinked"),
    ]

    code, ln = [], 1
    for i, row in enumerate(rows):
        y = y0 + i * LEAD
        code.append(f'<text class="gut" x="{X0}" y="{y}">{ln:02d}</text>')
        ln += 1
        t = f'<text class="cd" xml:space="preserve" y="{y}">'
        if row[0] == "open":
            t += f'<tspan class="kw" x="64">const</tspan><tspan class="vr"> aditya</tspan><tspan class="op"> = {{</tspan>'
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
    code.append(f'<rect class="car" x="64" y="{y0 + 5*LEAD - 11}" width="8.4" height="14"/>')
    code = "\n  ".join(code)

    H = y0 + (len(rows) - 1) * LEAD + 56
    cx, cy = 716, (BAR + H) / 2 - 8

    # iris spokes
    spokes = "".join(
        f'<line x1="0" y1="-15" x2="0" y2="-31" transform="rotate({i*22.5})"/>' for i in range(16)
    )

    # right-hand readout rows
    reads = [("A-SYS", 0.93), ("DEV.LOOP", 0.78), ("SIGNAL", 0.61)]
    ro = []
    for i, (lbl, frac) in enumerate(reads):
        ry = cy - 26 + i * 26
        ro.append(f'<text class="rd" x="800" y="{ry}">{lbl}</text>')
        ro.append(f'<rect x="884" y="{ry-8}" width="86" height="6" rx="1" fill="{VOID}" stroke="{LINE}"/>')
        ro.append(f'<rect x="885" y="{ry-7}" width="{84*frac:.0f}" height="4" fill="{AMBER}" fill-opacity="{0.85 - i*0.18:.2f}"/>')
    ro = "\n  ".join(ro)

    # rain over the panel, faint
    streaks = []
    for _ in range(26):
        rx, rl = random.randint(0, W), random.randint(14, 34)
        streaks.append(
            f'<line class="rn" x1="{rx}" y1="-{rl}" x2="{rx-6}" y2="0" '
            f'stroke-opacity="{random.uniform(.06,.18):.2f}" '
            f'style="animation-duration:{random.uniform(1.1,2.4):.2f}s;'
            f'animation-delay:-{random.uniform(0,2.4):.2f}s"/>'
        )
    rain = "\n    ".join(streaks)

    alt = ("Aditya Padmarajan — Software Developer at STEMCELL Technologies; "
           "B.Sc. Computer Science, University of Victoria; based in Vancouver, British Columbia")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{alt}">
  <title>{alt}</title>
  <defs>
    <linearGradient id="ipnl" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="#0D131A"/>
      <stop offset="62%"  stop-color="{PANEL}"/>
      <stop offset="100%" stop-color="{VOID}"/>
    </linearGradient>
    <linearGradient id="ibar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#131B24"/>
      <stop offset="100%" stop-color="{PANEL}"/>
    </linearGradient>
    <radialGradient id="iris" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{RUST}" stop-opacity=".55"/>
      <stop offset="58%"  stop-color="{AMBER}" stop-opacity=".22"/>
      <stop offset="100%" stop-color="{VOID}"  stop-opacity=".9"/>
    </radialGradient>
    <linearGradient id="isweep" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{ICE}" stop-opacity="0"/>
      <stop offset="50%"  stop-color="{ICE}" stop-opacity=".10"/>
      <stop offset="100%" stop-color="{ICE}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="iscan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1.4" fill="#000" fill-opacity="0.26"/>
    </pattern>
    <clipPath id="ipupil"><circle cx="{cx}" cy="{cy}" r="33"/></clipPath>
    <clipPath id="iframe"><rect x="0" y="0" width="{W}" height="{H}" rx="3"/></clipPath>
    <filter id="iglow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .cd {{ font-family:{MONO}; font-size:14px; letter-spacing:.2px; }}
    .gut{{ font-family:{MONO}; font-size:11px; fill:{ASH}; fill-opacity:.55; }}
    .kw {{ fill:#FF5FA2; }}
    .vr {{ fill:{BONE}; }}
    .ky {{ fill:{ICE}; }}
    .st {{ fill:{STR}; }}
    .op {{ fill:{ASH}; }}
    .cm {{ fill:{ASH}; fill-opacity:.68; font-style:italic; }}
    .tab{{ font-family:{MONO}; font-size:12px; font-weight:700; letter-spacing:2.2px; fill:{BONE}; fill-opacity:.9; }}
    .meta{{font-family:{MONO}; font-size:10.5px; letter-spacing:2.4px; fill:{ASH}; }}
    .rd {{ font-family:{MONO}; font-size:10.5px; letter-spacing:2.2px; fill:{ASH}; }}
    .vk {{ font-family:{MONO}; font-size:10px; letter-spacing:3px; fill:{AMBER}; fill-opacity:.85; }}
    .car{{ fill:{ICE}; fill-opacity:.75; animation:icar 1.05s steps(1) infinite; }}
    @keyframes icar {{ 0%,50% {{opacity:1}} 51%,100% {{opacity:0}} }}
    .rn {{ stroke:{ICE}; stroke-width:1; animation-name:ifall; animation-timing-function:linear; animation-iteration-count:infinite; }}
    @keyframes ifall {{ from {{transform:translateY(0)}} to {{transform:translateY({H+40}px)}} }}
    .swp{{ animation:iswp 7s ease-in-out infinite; }}
    @keyframes iswp {{ 0%,100% {{transform:translateY(-70px)}} 50% {{transform:translateY({H}px)}} }}
    .dash{{ transform-origin:{cx}px {cy}px; animation:ispin 14s linear infinite; }}
    @keyframes ispin {{ to {{transform:rotate(360deg)}} }}
    .spk {{ transform-origin:{cx}px {cy}px; animation:ispin2 26s linear infinite; }}
    @keyframes ispin2 {{ to {{transform:rotate(-360deg)}} }}
    .iscan{{ animation:iris-scan 3.4s ease-in-out infinite; }}
    @keyframes iris-scan {{ 0%,100% {{transform:translateY(-34px)}} 50% {{transform:translateY(34px)}} }}
    .dot {{ animation:ipulse 2.2s ease-in-out infinite; }}
    @keyframes ipulse {{ 0%,100% {{opacity:.25}} 50% {{opacity:1}} }}
    @media (prefers-reduced-motion: reduce) {{
      .car,.rn,.swp,.dash,.spk,.iscan,.dot {{ animation:none; }}
      .rn {{ opacity:.18 }}
    }}
  </style>

  <g clip-path="url(#iframe)">
    <rect width="{W}" height="{H}" fill="url(#ipnl)"/>
    {rain}

    <!-- title bar -->
    <rect width="{W}" height="{BAR}" fill="url(#ibar)"/>
    <rect x="0" y="{BAR-1}" width="{W}" height="1" fill="{LINE}"/>
    <circle cx="26" cy="{BAR/2:.0f}" r="3.6" fill="{AMBER}" class="dot"/>
    <text class="tab" x="42" y="{BAR/2+4:.0f}">IDENTITY.TS</text>
    <text class="meta" x="{W-30}" y="{BAR/2+4:.0f}" text-anchor="end">FILE 2049&#183;ADI&#183;01 &#183; CLEARANCE PUBLIC</text>

    <!-- code -->
    <rect x="0" y="{BAR}" width="3" height="{H-BAR}" fill="{AMBER}"/>
    {code}

    <!-- divider -->
    <line x1="630" y1="{BAR+22}" x2="630" y2="{H-22}" stroke="{LINE}" stroke-width="1"/>

    <!-- v-k iris -->
    <g class="dash" fill="none" stroke="{AMBER}" stroke-opacity=".45" stroke-width="1.1">
      <circle cx="{cx}" cy="{cy}" r="52" stroke-dasharray="3 9"/>
    </g>
    <circle cx="{cx}" cy="{cy}" r="44" fill="none" stroke="{AMBER}" stroke-opacity=".22" stroke-width="1"/>
    <circle cx="{cx}" cy="{cy}" r="33" fill="url(#iris)"/>
    <g class="spk" stroke="{AMBER}" stroke-opacity=".30" stroke-width="1" transform-origin="{cx} {cy}">
      <g transform="translate({cx},{cy})">{spokes}</g>
    </g>
    <g clip-path="url(#ipupil)">
      <rect class="iscan" x="{cx-33}" y="{cy-1.5}" width="66" height="3" fill="{ICE}" fill-opacity=".55"/>
    </g>
    <circle cx="{cx}" cy="{cy}" r="12.5" fill="{VOID}" stroke="{ICE}" stroke-opacity=".5"/>
    <circle cx="{cx-4}" cy="{cy-4}" r="2.6" fill="{ICE}" fill-opacity=".9" filter="url(#iglow)"/>
    <text class="vk" x="{cx}" y="{cy+70}" text-anchor="middle">V&#8722;K BASELINE</text>

    <!-- readouts -->
    {ro}
    <text class="meta" x="800" y="{cy+70}">STATUS &#183; INTERLINKED</text>

    <!-- footer -->
    <text class="meta" x="64" y="{H-16}">49.28&#176;N 123.12&#176;W &#183; VANCOUVER SECTOR</text>
    <text class="meta" x="{W-30}" y="{H-16}" text-anchor="end">&#9646;&#9646;&#9646;&#9646;&#9646;&#9646;&#9646;&#9647;&#9647; STABLE</text>

    <!-- hud corners -->
    <g fill="none" stroke="{AMBER}" stroke-opacity=".55" stroke-width="1.2">
      <path d="M14 {BAR+16} L14 {BAR+6} L24 {BAR+6}"/>
      <path d="M{W-24} {BAR+6} L{W-14} {BAR+6} L{W-14} {BAR+16}"/>
      <path d="M14 {H-16} L14 {H-6} L24 {H-6}"/>
      <path d="M{W-24} {H-6} L{W-14} {H-6} L{W-14} {H-16}"/>
    </g>

    <!-- overlays -->
    <rect class="swp" width="{W}" height="70" fill="url(#isweep)"/>
    <rect width="{W}" height="{H}" fill="url(#iscan)"/>
    <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="3" fill="none" stroke="{AMBER}" stroke-opacity=".30"/>
  </g>
</svg>
"""


if __name__ == "__main__":
    print("Generating assets...")
    write("banner.svg", banner())
    write("divider.svg", divider())
    write("stack.svg", stack())
    write("identity.svg", identity())
    for i, (cmd, note) in enumerate([
        ("whoami",   "IDENTITY"),
        ("trophies", "36-HOUR BUILDS"),
        ("stack",    "TOOLING MANIFEST"),
        ("signals",  "TELEMETRY"),
        ("now",      "CURRENT STATE"),
    ]):
        write(f"hdr-{cmd}.svg", header(cmd, note, i))
    for j, (fn, label, target, icon, chan, primary) in enumerate([
        ("btn-portfolio", "PORTFOLIO", "adityapadmarajan.com",        "globe", "CH.01", True),
        ("btn-linkedin",  "LINKEDIN",  "in/aditya-padmarajan",        "link",  "CH.02", False),
        ("btn-email",     "EMAIL",     "aditya.padmarajan@gmail.com", "mail",  "CH.03", False),
    ]):
        write(f"{fn}.svg", card(label, target, icon, chan, primary, j))
    print("Done.")
