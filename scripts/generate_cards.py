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
    title = escape(f"{user.get('name') or login}'s GitHub Stats")
    lines = []
    for i, (label, value) in enumerate(rows):
        y = 62 + i * 22
        lines.append(
            f'<circle cx="32" cy="{y - 4}" r="3.5" fill="{ACCENT}"/>'
            f'<text x="46" y="{y}" fill="{TEXT}" font-size="13" font-family="{FONT}">{escape(label)}</text>'
            f'<text x="440" y="{y}" fill="{ACCENT}" font-size="13" font-weight="700" '
            f'font-family="{MONO}" text-anchor="end">{value:,}</text>'
        )
    height = 62 + len(rows) * 22
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="467" height="{height}" viewBox="0 0 467 {height}" role="img" aria-label="{title}">
<rect width="467" height="{height}" rx="6" fill="{BG}"/>
<text x="25" y="34" fill="{ACCENT}" font-size="18" font-weight="700" font-family="{FONT}">{title}</text>
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
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
<text x="{left}" y="32" fill="{TEXT}" font-size="16" font-weight="700" font-family="{MONO}">${escape(login.upper().replace('-', ''))}<tspan fill="{MUTED}" font-weight="400"> / CONTRIBUTIONS · 1D · {days}D range</tspan></text>
<text x="{left}" y="56" fill="{ACCENT}" font-size="22" font-weight="700" font-family="{MONO}">{total:,}<tspan fill="{delta_color}" font-size="14" dx="12">{change}</tspan></text>
<text x="{W - 24}" y="32" fill="{UP}" font-size="12" font-family="{MONO}" text-anchor="end">● LIVE</text>
{''.join(grid)}
<polygon points="{area}" fill="url(#fill)"/>
<polyline points="{line}" fill="none" stroke="{ACCENT}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)"/>
<line x1="{left}" y1="{ly:.1f}" x2="{left + pw}" y2="{ly:.1f}" stroke="{ACCENT}" stroke-opacity="0.5" stroke-dasharray="2 3"/>
<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4.5" fill="#ffffff" stroke="{ACCENT}" stroke-width="2"/>
<rect x="{left + pw + 2}" y="{ly - 10:.1f}" width="46" height="20" rx="3" fill="{ACCENT}"/>
<text x="{left + pw + 25}" y="{ly + 4:.1f}" fill="{BG}" font-size="12" font-weight="700" font-family="{MONO}" text-anchor="middle">{last}</text>
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
