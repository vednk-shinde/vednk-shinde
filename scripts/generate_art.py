#!/usr/bin/env python3
"""Generate the animated decorative SVGs for the profile README.

GitHub strips scripts and styles from README markdown, but SVGs embedded as
<img> keep their own CSS/SMIL animations, so all motion lives in these files.

Usage: python scripts/generate_art.py assets
"""
import os
import random
import sys

BG = "#0d1117"
BG_DEEP = "#010409"
TEXT = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#F7931A"   # bitcoin orange
GOLD = "#FFD166"
RAIN = "#58a6ff"
PINK = "#ff6b9d"
MONO = "'Fira Code','JetBrains Mono','SFMono-Regular',Consolas,monospace"
SANS = "'Segoe UI',Ubuntu,'Helvetica Neue',sans-serif"

REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def rain(rng, width, height, count, floor_y):
    """Three parallax layers of slanted raindrops."""
    layers = [  # (share, length range, speed range s, opacity, stroke width)
        (0.45, (8, 14), (1.4, 2.0), 0.22, 1.0),
        (0.35, (14, 22), (0.9, 1.3), 0.40, 1.3),
        (0.20, (22, 34), (0.6, 0.85), 0.65, 1.8),
    ]
    drift = -40  # horizontal drift over one fall = wind
    fall = floor_y + 60
    out = []
    for share, (lmin, lmax), (smin, smax), opacity, sw in layers:
        for _ in range(int(count * share)):
            x = rng.uniform(0, width + 60)
            length = rng.uniform(lmin, lmax)
            dx = drift * length / fall
            dur = rng.uniform(smin, smax)
            delay = -rng.uniform(0, dur)
            out.append(
                f'<line class="drop" x1="{x:.1f}" y1="0" x2="{x + dx:.1f}" y2="{length:.1f}" '
                f'stroke="url(#dropGrad)" stroke-width="{sw}" stroke-linecap="round" opacity="{opacity}" '
                f'style="animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s"/>'
            )
    return "\n".join(out), drift, fall


def ripples(rng, width, floor_y, count):
    out = []
    for _ in range(count):
        x = rng.uniform(20, width - 20)
        dur = rng.uniform(1.2, 2.2)
        delay = -rng.uniform(0, dur * 3)
        out.append(
            f'<ellipse class="ripple" cx="{x:.1f}" cy="{floor_y + rng.uniform(0, 14):.1f}" rx="16" ry="3.2" '
            f'fill="none" stroke="{RAIN}" stroke-width="1" '
            f'style="animation-duration:{dur:.2f}s;animation-delay:{delay:.2f}s"/>'
        )
    return "\n".join(out)


def pixel_v(x0, y0, cell):
    """The block-letter V, lit up row by row, with a dim 3D shadow layer."""
    rows = 12
    cells = set()
    for r in range(rows):
        for c in (r, r + 1, 22 - r, 23 - r):
            cells.add((r, c))
    shadow, blocks = [], []
    for r, c in sorted(cells):
        x, y = x0 + c * cell, y0 + r * cell
        s = cell - 2
        shadow.append(f'<rect x="{x + 4}" y="{y + 4}" width="{s}" height="{s}" rx="2" fill="{ACCENT}" opacity="0.18"/>')
        delay = 0.25 + r * 0.09 + (c % 3) * 0.02
        blocks.append(
            f'<rect class="blk" x="{x}" y="{y}" width="{s}" height="{s}" rx="2" fill="url(#vGrad)" '
            f'style="animation-delay:{delay:.2f}s"/>'
        )
    return "\n".join(shadow), "\n".join(blocks)


def hero(rng):
    W, H, floor_y = 1000, 330, 300
    drops, drift, fall = rain(rng, W, H, 150, floor_y)
    shadow, blocks = pixel_v(70, 64, 13)
    subtitle = "&gt; Backend &amp; Distributed Systems Engineer"
    stars = "\n".join(
        f'<circle class="star" cx="{rng.uniform(0, W):.0f}" cy="{rng.uniform(0, floor_y - 40):.0f}" '
        f'r="{rng.uniform(0.6, 1.4):.1f}" fill="#ffffff" style="animation-delay:{-rng.uniform(0, 4):.1f}s;'
        f'animation-duration:{rng.uniform(2.5, 5):.1f}s"/>'
        for _ in range(40))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Vedank Shinde - Backend and Distributed Systems Engineer">
<defs>
  <radialGradient id="sky" cx="50%" cy="0%" r="100%">
    <stop offset="0%" stop-color="#161b22"/><stop offset="100%" stop-color="{BG_DEEP}"/>
  </radialGradient>
  <linearGradient id="dropGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{RAIN}" stop-opacity="0"/><stop offset="100%" stop-color="#cde6ff"/>
  </linearGradient>
  <linearGradient id="vGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{GOLD}"/><stop offset="55%" stop-color="{ACCENT}"/><stop offset="100%" stop-color="{PINK}"/>
  </linearGradient>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">
    <stop offset="0%" stop-color="{TEXT}"/><stop offset="40%" stop-color="{TEXT}"/>
    <stop offset="50%" stop-color="{GOLD}"/><stop offset="60%" stop-color="{TEXT}"/><stop offset="100%" stop-color="{TEXT}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-700 0;900 0" dur="4s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="sweep" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="120" y2="0">
    <stop offset="0%" stop-color="#fff" stop-opacity="0"/><stop offset="50%" stop-color="#fff" stop-opacity="0.55"/><stop offset="100%" stop-color="#fff" stop-opacity="0"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-200 0;600 0" dur="3.5s" begin="1.8s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{RAIN}" stop-opacity="0"/><stop offset="50%" stop-color="{RAIN}" stop-opacity="0.5"/><stop offset="100%" stop-color="{RAIN}" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="typeClip">
    <rect x="440" y="150" height="40" width="0">
      <animate attributeName="width" values="0;470;470;0" keyTimes="0;0.45;0.85;1" dur="9s" begin="1s" repeatCount="indefinite"/>
    </rect>
  </clipPath>
  <mask id="vMask"><g fill="#fff">{blocks.replace('class="blk"', '').replace('fill="url(#vGrad)"', '')}</g></mask>
</defs>
<style>
  .drop {{ animation: fall linear infinite; }}
  @keyframes fall {{ from {{ transform: translate(0, -60px); }} to {{ transform: translate({drift}px, {fall}px); }} }}
  .ripple {{ transform-box: fill-box; transform-origin: center; animation: ripple ease-out infinite; opacity: 0; }}
  @keyframes ripple {{ 0% {{ transform: scale(0.1); opacity: 0.9; }} 100% {{ transform: scale(1.6); opacity: 0; }} }}
  .blk {{ opacity: 0; animation: lightUp 0.5s ease-out forwards; }}
  @keyframes lightUp {{ 0% {{ opacity: 0; }} 60% {{ opacity: 1; fill: #fff; }} 100% {{ opacity: 1; }} }}
  .vglow {{ animation: pulse 3s ease-in-out 1.6s infinite; opacity: 0; }}
  @keyframes pulse {{ 0%,100% {{ opacity: 0.25; }} 50% {{ opacity: 0.8; }} }}
  .star {{ animation: twinkle ease-in-out infinite; }}
  @keyframes twinkle {{ 0%,100% {{ opacity: 0.1; }} 50% {{ opacity: 0.8; }} }}
  .fade {{ opacity: 0; animation: fadeIn 1s ease-out forwards; }}
  @keyframes fadeIn {{ to {{ opacity: 1; }} }}
  .cursor {{ animation: blink 1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  .live {{ animation: blink 1.4s ease-in-out infinite; }}
  .scan {{ animation: scan 6s linear infinite; }}
  @keyframes scan {{ from {{ transform: translateY(-20px); }} to {{ transform: translateY({H}px); }} }}
  {REDUCED_MOTION}
</style>

<rect width="{W}" height="{H}" rx="14" fill="url(#sky)"/>
{stars}
<g>{drops}</g>

<!-- reflective floor + splashes -->
<rect x="0" y="{floor_y}" width="{W}" height="1.2" fill="url(#floor)"/>
<g>{ripples(rng, W, floor_y, 22)}</g>

<!-- the V -->
<g class="vglow" filter="url(#glow)" opacity="0.4">{blocks.replace('class="blk"', '').replace(' style="', ' data-s="')}</g>
{shadow}
{blocks}
<rect x="70" y="64" width="312" height="156" fill="url(#sweep)" mask="url(#vMask)"/>

<!-- name + subtitle -->
<text x="440" y="118" font-family="{SANS}" font-size="52" font-weight="800" letter-spacing="2" fill="url(#shine)" class="fade" style="animation-delay:0.6s">VEDANK SHINDE</text>
<g clip-path="url(#typeClip)">
  <text x="442" y="176" font-family="{MONO}" font-size="19" fill="{ACCENT}">{subtitle}</text>
</g>
<rect class="cursor" x="442" y="160" width="10" height="20" fill="{ACCENT}" opacity="0.9">
  <animate attributeName="x" values="442;905;905;442" keyTimes="0;0.45;0.85;1" dur="9s" begin="1s" repeatCount="indefinite"/>
</rect>
<text x="442" y="214" font-family="{MONO}" font-size="14" fill="{MUTED}" class="fade" style="animation-delay:1.4s">Java · Spring Boot · Kafka · Go · Kubernetes · Cloud-native</text>

<!-- status bar -->
<g class="fade" style="animation-delay:2s" font-family="{MONO}" font-size="12">
  <circle class="live" cx="448" cy="258" r="4" fill="#3fb950"/>
  <text x="460" y="262" fill="#3fb950">online</text>
  <text x="520" y="262" fill="{MUTED}">│  uptime 100%  │  build passing  │  shipping event-driven systems</text>
</g>

<!-- CRT scanline -->
<rect class="scan" x="0" y="0" width="{W}" height="18" fill="#ffffff" opacity="0.025"/>
</svg>
"""


def divider():
    W, H = 1000, 16
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="divider">
<defs>
  <linearGradient id="base" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0"/><stop offset="50%" stop-color="{ACCENT}" stop-opacity="0.35"/><stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="spark"><stop offset="0%" stop-color="#fff"/><stop offset="35%" stop-color="{GOLD}"/><stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>
</defs>
<style>
  .p {{ animation: run 3.2s cubic-bezier(.45,.05,.55,.95) infinite; }}
  .p2 {{ animation: run 3.2s cubic-bezier(.45,.05,.55,.95) 1.6s infinite; opacity: .6; }}
  @keyframes run {{ from {{ transform: translateX(-80px); }} to {{ transform: translateX({W + 80}px); }} }}
  {REDUCED_MOTION}
</style>
<rect x="0" y="7.5" width="{W}" height="1" fill="url(#base)"/>
<ellipse class="p" cx="0" cy="8" rx="60" ry="6" fill="url(#spark)"/>
<ellipse class="p2" cx="0" cy="8" rx="40" ry="4" fill="url(#spark)"/>
</svg>
"""


def wave_path(width, height, amp, wavelength, phase, base):
    pts = []
    x = -wavelength
    import math
    while x <= width * 2 + wavelength:
        y = base + amp * math.sin((x / wavelength) * 2 * math.pi + phase)
        pts.append(f"{x:.0f},{y:.1f}")
        x += 10
    return f"M{pts[0]} L" + " ".join(pts[1:]) + f" L{width * 2 + wavelength},{height} L{-wavelength},{height} Z"


def footer():
    W, H = 1000, 170
    waves = [
        (ACCENT, 0.18, 10, 250, 0.0, 95, 14),
        (PINK, 0.14, 12, 330, 1.3, 105, 10),
        (GOLD, 0.16, 8, 200, 2.1, 115, 7),
    ]
    paths = []
    for color, op, amp, wl, ph, base, dur in waves:
        # Path spans two screen widths; sliding it by exactly one wavelength-multiple of W loops seamlessly.
        shift = (W // wl + 1) * wl
        paths.append(
            f'<path d="{wave_path(W, H, amp, wl, ph, base)}" fill="{color}" opacity="{op}">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;-{shift} 0" dur="{dur}s" repeatCount="indefinite"/></path>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Thanks for stopping by">
<style>
  .t {{ animation: breathe 4s ease-in-out infinite; }}
  @keyframes breathe {{ 0%,100% {{ opacity: .75; }} 50% {{ opacity: 1; }} }}
  {REDUCED_MOTION}
</style>
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{BG_DEEP}"/>
{''.join(paths)}
</g>
<text class="t" x="{W / 2}" y="58" text-anchor="middle" font-family="{SANS}" font-size="22" font-weight="700" fill="{TEXT}">Thanks for stopping by ✦</text>
<text x="{W / 2}" y="84" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">let's build something reliable together</text>
</svg>
"""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "assets"
    os.makedirs(out, exist_ok=True)
    rng = random.Random(42)  # deterministic: regenerating doesn't churn the files
    for name, svg in (("hero.svg", hero(rng)), ("divider.svg", divider()), ("footer.svg", footer())):
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {os.path.join(out, name)} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
