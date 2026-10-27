#!/usr/bin/env python3
"""
Renders data/contributions.json to an animated SVG contribution heatmap
with cascading CSS keyframes pop & flash animation.
"""
import os
import json
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

def render():
    with open(IN_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    days = metrics["days"]
    total = metrics["total_contributions"]
    cur_streak = metrics["current_streak"]
    long_streak = metrics["longest_streak"]
    best_day = metrics["best_day"]
    rng = metrics["range"]

    BG_START = "#0a0e14"
    BG_END = "#0d1420"
    FRAME_STROKE = "#1f6feb"
    TEXT_MUTED = "#7d8590"
    ACCENT_CYAN = "#22d3ee"
    ACCENT_GREEN = "#39d353"
    ACCENT_GOLD = "#f2cc60"

    PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

    CELL = 12
    GAP = 3
    STEP = CELL + GAP
    PAD = 24
    LEFT_LABEL_W = 32
    TOP_LABEL_H = 22
    TITLEBAR_H = 36
    RAD = 2.5

    first_date = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first_date.weekday() + 1) % 7
    grid = []
    col = [None] * lead_pad

    for d in days:
        dt = datetime.date.fromisoformat(d["date"])
        weekday = (dt.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], min(4, d["level"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)

    NW = len(grid)
    art_w = NW * STEP
    art_h = 7 * STEP

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 76
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD

    MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_labels = []
    seen_months = set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is not None:
                dt = datetime.date.fromisoformat(cell[0])
                key = (dt.year, dt.month)
                if key not in seen_months and dt.day <= 7:
                    seen_months.add(key)
                    month_labels.append((ci, MONTHS[dt.month - 1]))
                break

    REVEAL_DUR = 3.2
    max_order = (NW - 1) + 6 * 0.45

    css = f"""
    text.lbl {{ fill: {TEXT_MUTED}; font-size: 10px; font-weight: 500; }}
    text.title {{ fill: {TEXT_MUTED}; font-size: 12px; font-family: ui-monospace, Menlo, Consolas, monospace; }}
    text.stat-big {{ fill: {ACCENT_GREEN}; font-size: 14px; font-weight: 700; }}
    text.stat-sub {{ fill: {TEXT_MUTED}; font-size: 12px; }}
    
    .c {{
      transform-box: fill-box;
      transform-origin: center;
      opacity: 0;
      animation: pop 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both;
    }}
    .g {{
      animation: pop 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both, flash 0.65s ease-out both;
    }}
    
    @keyframes pop {{
      0%   {{ opacity: 0; transform: scale(0.2); }}
      65%  {{ opacity: 1; transform: scale(1.15); }}
      100% {{ opacity: 1; transform: scale(1); }}
    }}
    
    @keyframes flash {{
      0%   {{ filter: brightness(2.6); }}
      50%  {{ filter: brightness(2.6); }}
      100% {{ filter: brightness(1); }}
    }}
    
    @media (prefers-reduced-motion: reduce) {{
      .c, .g {{ opacity: 1 !important; transform: none !important; animation: none !important; }}
    }}
    """.strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, -apple-system, monospace">',
        f'<style>{css}</style>',
        '<defs>',
        f'<linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0%" stop-color="{BG_START}"/>',
        f'<stop offset="100%" stop-color="{BG_END}"/>',
        f'</linearGradient>',
        '</defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#bgGrad)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w - 1}" height="{canvas_h - 1}" rx="12" '
        f'fill="none" stroke="{FRAME_STROKE}" stroke-width="1" stroke-opacity="0.45"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME_STROKE}" stroke-opacity="0.3"/>',
        f'<circle cx="{PAD}" cy="{TITLEBAR_H / 2}" r="5" fill="#ff5f56"/>',
        f'<circle cx="{PAD + 16}" cy="{TITLEBAR_H / 2}" r="5" fill="#ffbd2e"/>',
        f'<circle cx="{PAD + 32}" cy="{TITLEBAR_H / 2}" r="5" fill="#27c93f"/>',
        f'<text class="title" x="{canvas_w / 2}" y="{TITLEBAR_H / 2 + 4}" text-anchor="middle">'
        f'ankush@github: ~/activity --contributions --stream</text>'
    ]

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    for ci, label in month_labels:
        x = grid_left + ci * STEP
        parts.append(f'<text class="lbl" x="{x}" y="{TITLEBAR_H + 15}">{label}</text>')

    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.78
        parts.append(f'<text class="lbl" x="{PAD}" y="{y:.1f}">{wname}</text>')

    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            delay = round(((ci + ri * 0.45) / max_order) * REVEAL_DUR, 3)
            cls = "c g" if lvl >= 1 else "c"
            plural = "s" if count != 1 else ""
            parts.append(
                f'<rect class="{cls}" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="{RAD}" '
                f'fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{date_s}: {count} contribution{plural}</title>'
                f'</rect>'
            )

    leg_y = grid_top + art_h + 8
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 68)
    parts.append(f'<text class="lbl" x="{leg_x}" y="{leg_y + CELL * 0.8:.1f}" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for lvl, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL - 1}" height="{CELL - 1}" rx="{RAD}" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text class="lbl" x="{lx + 4}" y="{leg_y + CELL * 0.8:.1f}">More</text>')

    sep_y = leg_y + CELL + 12
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME_STROKE}" stroke-opacity="0.2"/>')

    ly = sep_y + 22
    parts.append(
        f'<text x="{PAD}" y="{ly}">'
        f'<tspan class="stat-big">{total:,}</tspan>'
        f'<tspan class="stat-sub"> contributions in the last year</tspan>'
        f'</text>'
    )
    parts.append(
        f'<text class="stat-sub" x="{canvas_w - PAD}" y="{ly}" text-anchor="end">'
        f'{rng["start"]} &#8594; {rng["end"]}'
        f'</text>'
    )

    ly += 22
    parts.append(
        f'<text x="{PAD}" y="{ly}" class="stat-sub">'
        f'current streak <tspan fill="{ACCENT_CYAN}" font-weight="700">{cur_streak} days</tspan>'
        f'<tspan fill="{TEXT_MUTED}">   &#183;   longest </tspan>'
        f'<tspan fill="{ACCENT_CYAN}" font-weight="700">{long_streak} days</tspan>'
        f'</text>'
    )
    parts.append(
        f'<text class="stat-sub" x="{canvas_w - PAD}" y="{ly}" text-anchor="end">'
        f'best day <tspan fill="{ACCENT_GOLD}" font-weight="700">{best_day["count"]} commits</tspan> on {best_day["date"]}'
        f'</text>'
    )

    parts.append("</svg>")
    svg_content = "\n".join(parts)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Rendered {OUT_PATH} ({len(svg_content)} bytes)")

if __name__ == "__main__":
    render()
