#!/usr/bin/env python3
"""Render the profile's stats card and crypto-style contribution chart as SVGs.

Replaces the public github-readme-stats / github-readme-activity-graph
instances (both shut down) with self-generated images, refreshed daily by
.github/workflows/profile-cards.yml. Standard library only.

Usage: GITHUB_TOKEN=... python scripts/generate_cards.py <login> <out_dir>
"""
import json
import os
import sys
import urllib.request
from datetime import date
from html import escape

BG = "#0d1117"
GRID = "#21262d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
ACCENT = "#F7931A"  # Bitcoin orange
UP = "#3fb950"
DOWN = "#f85149"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch(login: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def stats_card(user: dict, login: str) -> str:
    cc = user["contributionsCollection"]
    stars = sum(r["stargazerCount"] for r in user["repositories"]["nodes"])
    rows = [
        ("Total Contributions (1y)", cc["contributionCalendar"]["totalContributions"]),
        ("Commits", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("Pull Requests", cc["totalPullRequestContributions"]),
        ("Issues", cc["totalIssueContributions"]),
        ("Code Reviews", cc["totalPullRequestReviewContributions"]),
        ("Public Repos", user["repositories"]["totalCount"]),
        ("Stars Earned", stars),
    ]
    title = "GitHub Stats"
    peak = max(max(v for _, v in rows), 1)
    lines = []
    for i, (label, value) in enumerate(rows):
        y = 64 + i * 24
        bar = max(4, 110 * value / peak)
        delay = 0.3 + i * 0.12
        lines.append(
            f'<g class="row" style="animation-delay:{delay:.2f}s">'
            f'<circle class="dot" cx="32" cy="{y - 4}" r="3.5" fill="{ACCENT}" style="animation-delay:{delay:.2f}s"/>'
            f'<text x="46" y="{y}" fill="{TEXT}" font-size="13" font-family="{FONT}">{escape(label)}</text>'
            f'<rect x="250" y="{y - 9}" width="110" height="6" rx="3" fill="#21262d"/>'
            f'<rect class="bar" x="250" y="{y - 9}" width="{bar:.1f}" height="6" rx="3" fill="url(#barGrad)" '
            f'style="animation-delay:{delay + 0.2:.2f}s"/>'
            f'<text x="440" y="{y}" fill="{ACCENT}" font-size="13" font-weight="700" '
            f'font-family="{MONO}" text-anchor="end">{value:,}</text></g>'
        )
    height = 64 + len(rows) * 24
    perimeter = 2 * (465 + height - 2)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="467" height="{height}" viewBox="0 0 467 {height}" role="img" aria-label="{escape(login)} GitHub stats">
<defs>
  <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#FFD166"/><stop offset="100%" stop-color="{ACCENT}"/></linearGradient>
</defs>
<style>
  .row {{ opacity: 0; animation: slideIn .6s ease-out forwards; }}
  @keyframes slideIn {{ from {{ opacity: 0; transform: translateX(-14px); }} to {{ opacity: 1; transform: none; }} }}
  .bar {{ transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: grow 1.1s cubic-bezier(.2,.8,.2,1) forwards; }}
  @keyframes grow {{ to {{ transform: scaleX(1); }} }}
  .dot {{ transform-box: fill-box; transform-origin: center; animation: beat 2.4s ease-in-out infinite; }}
  @keyframes beat {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.5); }} }}
  .border {{ animation: trace 6s linear infinite; }}
  @keyframes trace {{ to {{ stroke-dashoffset: -{perimeter}; }} }}
  .live {{ animation: blink 1.4s ease-in-out infinite; }}
  @keyframes blink {{ 50% {{ opacity: .15; }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; opacity: 1 !important; transform: none !important; }} }}
</style>
<rect width="467" height="{height}" rx="8" fill="{BG}"/>
<rect class="border" x="1" y="1" width="465" height="{height - 2}" rx="8" fill="none" stroke="{ACCENT}" stroke-width="1.5"
      stroke-dasharray="120 {perimeter - 120}" stroke-linecap="round" opacity="0.8"/>
<text x="25" y="34" fill="{ACCENT}" font-size="18" font-weight="700" font-family="{FONT}">{title}</text>
<circle class="live" cx="400" cy="29" r="4" fill="{UP}"/>
<text x="440" y="33" fill="{UP}" font-size="11" font-family="{MONO}" text-anchor="end">LIVE</text>
{''.join(lines)}
</svg>
"""


def activity_chart(user: dict, login: str, days: int = 60) -> str:
    all_days = [d for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]
                for d in w["contributionDays"]]
    series = all_days[-days:]
    counts = [d["contributionCount"] for d in series]

    W, H = 1000, 340
    left, right, top, bottom = 60, 110, 70, 50
    pw, ph = W - left - right, H - top - bottom
    peak = max(max(counts), 1)
    y_max = peak + max(1, round(peak * 0.15))

    def x(i):
        return left + pw * i / max(len(counts) - 1, 1)

    def y(v):
        return top + ph * (1 - v / y_max)

    pts = [(x(i), y(v)) for i, v in enumerate(counts)]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = f"{left},{top + ph} {line} {pts[-1][0]:.1f},{top + ph}"

    # "Price" change: last 7 days vs the 7 days before, like a weekly ticker delta.
    recent, prior = sum(counts[-7:]), sum(counts[-14:-7])
    if prior:
        pct = (recent - prior) / prior * 100
        change = f"{'▲' if pct >= 0 else '▼'} {pct:+.1f}% 7d"
    else:
        pct = 0 if recent == 0 else 100
        change = "▲ new activity 7d" if recent else "— flat 7d"
    delta_color = UP if pct >= 0 else DOWN

    grid = []
    steps = 4
    for s in range(steps + 1):
        v = y_max * s / steps
        gy = y(v)
        grid.append(f'<line x1="{left}" y1="{gy:.1f}" x2="{left + pw}" y2="{gy:.1f}" stroke="{GRID}" stroke-dasharray="3 4"/>'
                    f'<text x="{left + pw + 8}" y="{gy + 4:.1f}" fill="{MUTED}" font-size="11" font-family="{MONO}">{v:.0f}</text>')
    for i in range(0, len(series), 10):
        grid.append(f'<text x="{x(i):.1f}" y="{top + ph + 22}" fill="{MUTED}" font-size="11" '
                    f'font-family="{MONO}" text-anchor="middle">{date.fromisoformat(series[i]["date"]).strftime("%b %d")}</text>')

    lx, ly = pts[-1]
    last = counts[-1]
    total = sum(counts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution chart for {escape(login)}">
<defs>
  <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.45"/>
    <stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-5%" y="-20%" width="110%" height="140%">
    <feGaussianBlur stdDeviation="2.5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<style>
  .line {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 2.6s cubic-bezier(.4,0,.2,1) .3s forwards; }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  .area {{ opacity: 0; animation: show 1.2s ease-out 1.8s forwards; }}
  .late {{ opacity: 0; animation: show .6s ease-out 2.8s forwards; }}
  @keyframes show {{ to {{ opacity: 1; }} }}
  .ring {{ transform-box: fill-box; transform-origin: center; animation: ping 1.8s ease-out 2.9s infinite; opacity: 0; }}
  @keyframes ping {{ 0% {{ transform: scale(1); opacity: .9; }} 100% {{ transform: scale(4); opacity: 0; }} }}
  .live {{ animation: blink 1.4s ease-in-out infinite; }}
  @keyframes blink {{ 50% {{ opacity: .2; }} }}
  .scan {{ animation: scan 7s linear 3s infinite; opacity: 0; }}
  @keyframes scan {{ 0% {{ transform: translateX(0); opacity: 0; }} 5%,95% {{ opacity: .5; }} 100% {{ transform: translateX({pw}px); opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; opacity: 1 !important; stroke-dashoffset: 0 !important; }} }}
</style>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
<text x="{left}" y="32" fill="{TEXT}" font-size="16" font-weight="700" font-family="{MONO}">${escape(os.environ.get("TICKER") or login.upper().replace('-', ''))}<tspan fill="{MUTED}" font-weight="400"> / CONTRIBUTIONS · 1D · {days}D range</tspan></text>
<text x="{left}" y="56" fill="{ACCENT}" font-size="22" font-weight="700" font-family="{MONO}">{total:,}<tspan fill="{delta_color}" font-size="14" dx="12">{change}</tspan></text>
<text class="live" x="{W - 24}" y="32" fill="{UP}" font-size="12" font-family="{MONO}" text-anchor="end">● LIVE</text>
{''.join(grid)}
<polygon class="area" points="{area}" fill="url(#fill)"/>
<polyline class="line" pathLength="1" points="{line}" fill="none" stroke="{ACCENT}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)"/>
<line class="scan" x1="{left}" y1="{top}" x2="{left}" y2="{top + ph}" stroke="{ACCENT}" stroke-width="1" stroke-dasharray="2 3"/>
<g class="late">
  <line x1="{left}" y1="{ly:.1f}" x2="{left + pw}" y2="{ly:.1f}" stroke="{ACCENT}" stroke-opacity="0.5" stroke-dasharray="2 3"/>
  <circle class="ring" cx="{lx:.1f}" cy="{ly:.1f}" r="4.5" fill="none" stroke="{ACCENT}" stroke-width="2"/>
  <circle cx="{lx:.1f}" cy="{ly:.1f}" r="4.5" fill="#ffffff" stroke="{ACCENT}" stroke-width="2"/>
  <rect x="{left + pw + 2}" y="{ly - 10:.1f}" width="46" height="20" rx="3" fill="{ACCENT}"/>
  <text x="{left + pw + 25}" y="{ly + 4:.1f}" fill="{BG}" font-size="12" font-weight="700" font-family="{MONO}" text-anchor="middle">{last}</text>
</g>
</svg>
"""


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    login, out_dir = sys.argv[1], sys.argv[2]
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set")
    user = fetch(login, token)
    os.makedirs(out_dir, exist_ok=True)
    for name, svg in (("stats.svg", stats_card(user, login)), ("activity-graph.svg", activity_chart(user, login))):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {os.path.join(out_dir, name)}")


if __name__ == "__main__":
    main()
