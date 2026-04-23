#!/usr/bin/env python3
"""Generate benchmark visualizations from summary-derived run data.

The benchmark has small-N, partly qualitative data. This report keeps the data
inline and explicit rather than implying statistical precision.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent

RUNS = [
    {
        "run": "Codex / GPT-5.4",
        "tool": "Codex",
        "model": "GPT-5.4",
        "duration_min": 4.0,
        "fresh_tokens": 37_000,
        "peak_rss_mb": 69.9,
        "features": {
            "Pagination": 1,
            "Timeout": 0,
            "API header": 1,
            "Clean JSON": 1,
            "Separate tests": 1,
            "Live demo": 1,
        },
        "defect": "No timeout; silent 100-page cap.",
        "severity": {
            "Correctness": "Low",
            "Robustness": "Medium",
            "Output contract": "None",
            "Test quality": "None",
            "Verification": "None",
        },
    },
    {
        "run": "OMP / GPT-5.4",
        "tool": "OMP",
        "model": "GPT-5.4",
        "duration_min": 10.0,
        "fresh_tokens": 66_000,
        "peak_rss_mb": 305.0,
        "features": {
            "Pagination": 1,
            "Timeout": 1,
            "API header": 1,
            "Clean JSON": 0,
            "Separate tests": 1,
            "Live demo": 1,
        },
        "defect": "JSON emits full GitHub blob; over-structured.",
        "severity": {
            "Correctness": "None",
            "Robustness": "None",
            "Output contract": "Medium",
            "Test quality": "Low",
            "Verification": "None",
        },
    },
    {
        "run": "OpenCode / GPT-5.4",
        "tool": "OpenCode",
        "model": "GPT-5.4",
        "duration_min": 2.0,
        "fresh_tokens": 127_000,
        "peak_rss_mb": 462.0,
        "features": {
            "Pagination": 0,
            "Timeout": 0,
            "API header": 0,
            "Clean JSON": 1,
            "Separate tests": 1,
            "Live demo": 0.5,
        },
        "defect": "Missing pagination; wrong output on first run.",
        "severity": {
            "Correctness": "High",
            "Robustness": "Medium",
            "Output contract": "Medium",
            "Test quality": "Low",
            "Verification": "Medium",
        },
    },
    {
        "run": "Claude Code / GPT-5.4",
        "tool": "Claude Code",
        "model": "GPT-5.4",
        "duration_min": 2.0,
        "fresh_tokens": 106_000,
        "peak_rss_mb": 406.5,
        "features": {
            "Pagination": 0,
            "Timeout": 0,
            "API header": 0,
            "Clean JSON": 0,
            "Separate tests": 1,
            "Live demo": 1,
        },
        "defect": "Missing pagination; raw GitHub field names.",
        "severity": {
            "Correctness": "High",
            "Robustness": "Medium",
            "Output contract": "Medium",
            "Test quality": "Low",
            "Verification": "None",
        },
    },
    {
        "run": "OMP / Opus 4.6",
        "tool": "OMP",
        "model": "Opus 4.6",
        "duration_min": 2.3,
        "fresh_tokens": 40_478,
        "peak_rss_mb": 451.6,
        "features": {
            "Pagination": 1,
            "Timeout": 1,
            "API header": 0,
            "Clean JSON": 1,
            "Separate tests": 1,
            "Live demo": 1,
        },
        "defect": "No fetch/network unit tests; no deterministic tie-breaker.",
        "severity": {
            "Correctness": "Low",
            "Robustness": "None",
            "Output contract": "None",
            "Test quality": "Medium",
            "Verification": "None",
        },
    },
    {
        "run": "OpenCode / Opus 4.6",
        "tool": "OpenCode",
        "model": "Opus 4.6",
        "duration_min": 3.3,
        "fresh_tokens": 85_983,
        "peak_rss_mb": 347.4,
        "features": {
            "Pagination": 1,
            "Timeout": 0,
            "API header": 0,
            "Clean JSON": 1,
            "Separate tests": 1,
            "Live demo": 1,
        },
        "defect": "No timeout; weaker error-path coverage.",
        "severity": {
            "Correctness": "Low",
            "Robustness": "Medium",
            "Output contract": "None",
            "Test quality": "Medium",
            "Verification": "Low",
        },
    },
    {
        "run": "Claude Code / Opus 4.6",
        "tool": "Claude Code",
        "model": "Opus 4.6",
        "duration_min": 4.1,
        "fresh_tokens": 428_588,
        "peak_rss_mb": 319.0,
        "features": {
            "Pagination": 1,
            "Timeout": 0,
            "API header": 0,
            "Clean JSON": 0,
            "Separate tests": 0,
            "Live demo": 0,
        },
        "defect": "Tests embedded in production CLI file; no live verification.",
        "severity": {
            "Correctness": "High",
            "Robustness": "Medium",
            "Output contract": "High",
            "Test quality": "High",
            "Verification": "High",
        },
    },
]

FEATURES = ["Pagination", "Timeout", "API header", "Clean JSON", "Separate tests", "Live demo"]
SEVERITY_COLS = ["Correctness", "Robustness", "Output contract", "Test quality", "Verification"]
SEVERITY_SCORE = {"None": 0, "Low": 1, "Medium": 2, "High": 3}
SEVERITY_COLOR = {"None": "#e7f6ec", "Low": "#fff3bf", "Medium": "#ffd8a8", "High": "#ffa8a8"}
FEATURE_COLOR = {0: "#f1f3f5", 0.5: "#ffe8a3", 1: "#b7e4c7"}
MODEL_COLOR = {"GPT-5.4": "#2563eb", "Opus 4.6": "#7c3aed"}
TOOL_COLOR = {"Codex": "#16a34a", "OMP": "#dc2626", "OpenCode": "#f59e0b", "Claude Code": "#7c3aed"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def feature_label(value: float) -> str:
    if value == 1:
        return "Yes"
    if value == 0.5:
        return "Partial"
    return "No"


def quality_score(run: dict) -> float:
    return sum(run["features"].values()) / len(FEATURES) * 100


def token_k(n: int) -> str:
    return f"{n / 1000:.0f}K"


def heatmap() -> str:
    rows = []
    for run in sorted(RUNS, key=lambda r: (-quality_score(r), r["duration_min"])):
        cells = []
        for feature in FEATURES:
            value = run["features"][feature]
            cells.append(
                f'<td class="center" style="background:{FEATURE_COLOR[value]}">{feature_label(value)}</td>'
            )
        rows.append(
            f"<tr><th>{esc(run['run'])}</th>"
            + "".join(cells)
            + f"<td>{quality_score(run):.0f}</td><td>{esc(run['defect'])}</td></tr>"
        )
    return f"""
<section>
  <h2>Quality heatmap</h2>
  <p>Feature score counts yes=1, partial=0.5, no=0. It is a correctness checklist, not a statistical quality model.</p>
  <table>
    <thead><tr><th>Run</th>{''.join(f'<th>{esc(f)}</th>' for f in FEATURES)}<th>Score</th><th>Main defect</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>
"""


def slope_svg(metric: str, title: str, fmt) -> str:
    tools = ["OMP", "OpenCode", "Claude Code"]
    by_tool_model = {(r["tool"], r["model"]): r for r in RUNS}
    values = []
    if metric == "quality":
        for tool in tools:
            values.append(quality_score(by_tool_model[(tool, "GPT-5.4")]))
            values.append(quality_score(by_tool_model[(tool, "Opus 4.6")]))
    else:
        for tool in tools:
            values.append(by_tool_model[(tool, "GPT-5.4")][metric])
            values.append(by_tool_model[(tool, "Opus 4.6")][metric])
    min_v, max_v = min(values), max(values)
    if min_v == max_v:
        max_v = min_v + 1

    def y(v):
        return 280 - ((v - min_v) / (max_v - min_v)) * 220

    lines = [f'<text x="300" y="24" class="svg-title">{esc(title)}</text>',
             '<text x="110" y="52" class="axis-label">GPT-5.4</text>',
             '<text x="470" y="52" class="axis-label">Opus 4.6</text>',
             '<line x1="140" y1="60" x2="140" y2="295" class="axis"/>',
             '<line x1="500" y1="60" x2="500" y2="295" class="axis"/>']
    for tool in tools:
        gpt_run = by_tool_model[(tool, "GPT-5.4")]
        opus_run = by_tool_model[(tool, "Opus 4.6")]
        gpt = quality_score(gpt_run) if metric == "quality" else gpt_run[metric]
        opus = quality_score(opus_run) if metric == "quality" else opus_run[metric]
        y1, y2 = y(gpt), y(opus)
        color = TOOL_COLOR[tool]
        lines.append(f'<line x1="140" y1="{y1:.1f}" x2="500" y2="{y2:.1f}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<circle cx="140" cy="{y1:.1f}" r="5" fill="{color}"/>')
        lines.append(f'<circle cx="500" cy="{y2:.1f}" r="5" fill="{color}"/>')
        lines.append(f'<text x="12" y="{y1 + 4:.1f}" class="small-label">{esc(tool)} {esc(fmt(gpt))}</text>')
        lines.append(f'<text x="512" y="{y2 + 4:.1f}" class="small-label">{esc(fmt(opus))}</text>')
    return f'<svg viewBox="0 0 650 320" role="img" aria-label="{esc(title)}">{"".join(lines)}</svg>'


def model_shift() -> str:
    return f"""
<section>
  <h2>Model-shift slopegraphs</h2>
  <p>Codex is omitted here because Opus 4.6 did not run through the local proxy.</p>
  <div class="grid two">
    <div class="card">{slope_svg('fresh_tokens', 'Fresh tokens', token_k)}</div>
    <div class="card">{slope_svg('duration_min', 'Duration minutes', lambda v: f'{v:.1f}m')}</div>
    <div class="card wide">{slope_svg('quality', 'Feature quality score', lambda v: f'{v:.0f}/100')}</div>
  </div>
</section>
"""


def pareto_svg() -> str:
    width, height = 760, 460
    left, right, top, bottom = 90, 40, 45, 75
    x_min, x_max = 0, 10.5
    y_min, y_max = 0, 100

    def x(v):
        return left + ((v - x_min) / (x_max - x_min)) * (width - left - right)

    def y(v):
        return height - bottom - ((v - y_min) / (y_max - y_min)) * (height - top - bottom)

    max_tokens = max(r["fresh_tokens"] for r in RUNS)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Pareto chart: duration versus quality score">',
        '<text x="380" y="24" class="svg-title">Pareto view: faster + higher quality is better</text>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" class="axis"/>',
        f'<text x="360" y="430" class="axis-label">Duration, minutes lower is better</text>',
        f'<text x="18" y="210" class="axis-label rotate">Quality score higher is better</text>',
    ]
    for tick in [0, 2, 4, 6, 8, 10]:
        xx = x(tick)
        parts.append(f'<line x1="{xx:.1f}" y1="{height-bottom}" x2="{xx:.1f}" y2="{height-bottom+5}" class="axis"/>')
        parts.append(f'<text x="{xx:.1f}" y="{height-bottom+22}" class="tick">{tick}</text>')
    for tick in [0, 25, 50, 75, 100]:
        yy = y(tick)
        parts.append(f'<line x1="{left-5}" y1="{yy:.1f}" x2="{left}" y2="{yy:.1f}" class="axis"/>')
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" class="gridline"/>')
        parts.append(f'<text x="{left-12}" y="{yy+4:.1f}" class="tick right">{tick}</text>')

    for run in RUNS:
        score = quality_score(run)
        radius = 7 + (run["fresh_tokens"] / max_tokens) * 18
        xx, yy = x(run["duration_min"]), y(score)
        color = MODEL_COLOR[run["model"]]
        label = run["tool"].replace("Claude Code", "Claude") + " " + ("GPT" if run["model"] == "GPT-5.4" else "Opus")
        parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="{radius:.1f}" fill="{color}" fill-opacity="0.72"><title>{esc(run["run"])}: {score:.0f}/100, {run["duration_min"]:.1f}m, {token_k(run["fresh_tokens"])} fresh tokens</title></circle>')
        parts.append(f'<text x="{xx+radius+4:.1f}" y="{yy+4:.1f}" class="small-label">{esc(label)}</text>')
    parts.append('<text x="510" y="58" class="legend">Bubble size = fresh tokens</text>')
    parts.append('<circle cx="530" cy="82" r="10" fill="#2563eb" fill-opacity="0.72"/><text x="548" y="87" class="legend">GPT-5.4</text>')
    parts.append('<circle cx="530" cy="108" r="10" fill="#7c3aed" fill-opacity="0.72"/><text x="548" y="113" class="legend">Opus 4.6</text>')
    parts.append('</svg>')
    return "".join(parts)


def pareto() -> str:
    notes = []
    for r in sorted(RUNS, key=lambda r: (r["duration_min"], -quality_score(r))):
        notes.append(f'<li><strong>{esc(r["run"])}:</strong> {quality_score(r):.0f}/100, {r["duration_min"]:.1f}m, {token_k(r["fresh_tokens"])} fresh tokens.</li>')
    return f"""
<section>
  <h2>Pareto chart</h2>
  <p>Upper-left is preferred: shorter duration with higher feature quality. Bubble size shows fresh token cost.</p>
  <div class="card">{pareto_svg()}</div>
  <details><summary>Point values</summary><ul>{''.join(notes)}</ul></details>
</section>
"""


def defect_matrix() -> str:
    rows = []
    for run in RUNS:
        cells = []
        total = 0
        for col in SEVERITY_COLS:
            sev = run["severity"][col]
            total += SEVERITY_SCORE[sev]
            cells.append(f'<td class="center" style="background:{SEVERITY_COLOR[sev]}">{esc(sev)}</td>')
        rows.append(f'<tr><th>{esc(run["run"])}</th>{"".join(cells)}<td class="center">{total}</td><td>{esc(run["defect"])}</td></tr>')
    return f"""
<section>
  <h2>Defect severity matrix</h2>
  <p>Severity is qualitative and derived from the review findings in <code>summary.md</code>. Total is High=3, Medium=2, Low=1, None=0.</p>
  <table>
    <thead><tr><th>Run</th>{''.join(f'<th>{esc(c)}</th>' for c in SEVERITY_COLS)}<th>Total</th><th>Finding basis</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>
"""


def html_report() -> str:
    data = []
    for run in RUNS:
        item = dict(run)
        item["quality_score"] = round(quality_score(run), 1)
        data.append(item)
    json_blob = esc(json.dumps(data, indent=2))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Coding Agent Benchmark Visualizations</title>
<style>
:root {{ color-scheme: light; --ink:#17202a; --muted:#5c6773; --line:#d8dee4; --bg:#f8fafc; --card:#ffffff; }}
body {{ margin: 0; font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }}
main {{ max-width: 1180px; margin: 0 auto; padding: 32px 24px 56px; }}
h1 {{ margin: 0 0 4px; font-size: 30px; }}
h2 {{ margin: 34px 0 8px; font-size: 22px; }}
p {{ margin: 6px 0 14px; color: var(--muted); }}
table {{ width: 100%; border-collapse: collapse; background: var(--card); box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
th, td {{ border: 1px solid var(--line); padding: 8px 9px; vertical-align: top; }}
th {{ text-align: left; background: #f1f5f9; }}
.center {{ text-align: center; }}
.grid {{ display: grid; gap: 16px; }}
.grid.two {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
.card {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 10px; overflow-x: auto; }}
.wide {{ grid-column: 1 / -1; }}
svg {{ width: 100%; height: auto; }}
.axis {{ stroke: #64748b; stroke-width: 1; }}
.gridline {{ stroke: #e2e8f0; stroke-width: 1; }}
.svg-title {{ text-anchor: middle; font-size: 17px; font-weight: 700; fill: var(--ink); }}
.axis-label {{ text-anchor: middle; font-size: 12px; fill: var(--muted); }}
.rotate {{ transform: rotate(-90deg); transform-origin: 18px 210px; }}
.small-label {{ font-size: 11px; fill: var(--ink); }}
.tick {{ text-anchor: middle; font-size: 11px; fill: var(--muted); }}
.right {{ text-anchor: end; }}
.legend {{ font-size: 12px; fill: var(--muted); }}
summary {{ cursor: pointer; margin: 12px 0; }}
pre {{ white-space: pre-wrap; background: #0f172a; color: #e2e8f0; padding: 14px; border-radius: 8px; overflow-x: auto; }}
@media (max-width: 820px) {{ .grid.two {{ grid-template-columns: 1fr; }} .wide {{ grid-column: auto; }} }}
</style>
</head>
<body>
<main>
  <h1>AI Coding Agent Benchmark Visualizations</h1>
  <p>Source: <code>summary.md</code>. Scope: local exploratory benchmark, not statistically powered. Codex / Opus 4.6 is excluded because routing failed.</p>
  {model_shift()}
  {pareto()}
  {heatmap()}
  {defect_matrix()}
  <section>
    <h2>Source data embedded in report</h2>
    <details><summary>Show JSON</summary><pre>{json_blob}</pre></details>
  </section>
</main>
</body>
</html>
"""


SVG_STYLE = """
<style>
  .axis { stroke: #64748b; stroke-width: 1; }
  .gridline { stroke: #e2e8f0; stroke-width: 1; }
  .svg-title { text-anchor: middle; font: 700 17px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #17202a; }
  .axis-label { text-anchor: middle; font: 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #5c6773; }
  .small-label { font: 11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #17202a; }
  .tick { text-anchor: middle; font: 11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #5c6773; }
  .right { text-anchor: end; }
  .legend { font: 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #5c6773; }
</style>
""".replace("  ", "")


def standalone_svg(svg: str) -> str:
    return svg.replace(">", ">\n" + SVG_STYLE, 1) + "\n"


def feature_heatmap_svg() -> str:
    rows = sorted(RUNS, key=lambda r: (-quality_score(r), r["duration_min"]))
    label_w, cell_w, score_w = 190, 112, 70
    top, row_h, header_h = 54, 36, 38
    width = label_w + cell_w * len(FEATURES) + score_w + 24
    height = top + header_h + row_h * len(rows) + 24
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Quality heatmap">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             f'<text x="{width / 2:.0f}" y="24" class="svg-title">Quality heatmap</text>']
    x = label_w
    for feature in FEATURES:
        parts.append(f'<text x="{x + cell_w / 2:.0f}" y="{top + 24}" class="tick">{esc(feature)}</text>')
        x += cell_w
    parts.append(f'<text x="{x + score_w / 2:.0f}" y="{top + 24}" class="tick">Score</text>')
    for i, run in enumerate(rows):
        y = top + header_h + i * row_h
        parts.append(f'<text x="8" y="{y + 23}" class="small-label">{esc(run["run"])}</text>')
        x = label_w
        for feature in FEATURES:
            value = run["features"][feature]
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{row_h}" fill="{FEATURE_COLOR[value]}" stroke="#d8dee4"/>')
            parts.append(f'<text x="{x + cell_w / 2:.0f}" y="{y + 23}" class="tick">{feature_label(value)}</text>')
            x += cell_w
        parts.append(f'<rect x="{x}" y="{y}" width="{score_w}" height="{row_h}" fill="#f8fafc" stroke="#d8dee4"/>')
        parts.append(f'<text x="{x + score_w / 2:.0f}" y="{y + 23}" class="tick">{quality_score(run):.0f}</text>')
    parts.append('</svg>')
    return "".join(parts)


def defect_matrix_svg() -> str:
    label_w, cell_w, total_w = 190, 112, 58
    top, row_h, header_h = 54, 36, 38
    width = label_w + cell_w * len(SEVERITY_COLS) + total_w + 24
    height = top + header_h + row_h * len(RUNS) + 24
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Defect severity matrix">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             f'<text x="{width / 2:.0f}" y="24" class="svg-title">Defect severity matrix</text>']
    x = label_w
    for col in SEVERITY_COLS:
        parts.append(f'<text x="{x + cell_w / 2:.0f}" y="{top + 24}" class="tick">{esc(col)}</text>')
        x += cell_w
    parts.append(f'<text x="{x + total_w / 2:.0f}" y="{top + 24}" class="tick">Total</text>')
    for i, run in enumerate(RUNS):
        y = top + header_h + i * row_h
        parts.append(f'<text x="8" y="{y + 23}" class="small-label">{esc(run["run"])}</text>')
        x = label_w
        total = 0
        for col in SEVERITY_COLS:
            sev = run["severity"][col]
            total += SEVERITY_SCORE[sev]
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{row_h}" fill="{SEVERITY_COLOR[sev]}" stroke="#d8dee4"/>')
            parts.append(f'<text x="{x + cell_w / 2:.0f}" y="{y + 23}" class="tick">{esc(sev)}</text>')
            x += cell_w
        parts.append(f'<rect x="{x}" y="{y}" width="{total_w}" height="{row_h}" fill="#f8fafc" stroke="#d8dee4"/>')
        parts.append(f'<text x="{x + total_w / 2:.0f}" y="{y + 23}" class="tick">{total}</text>')
    parts.append('</svg>')
    return "".join(parts)


def write_svg_assets() -> None:
    assets = {
        "model_shift_fresh_tokens.svg": slope_svg("fresh_tokens", "Fresh tokens", token_k),
        "model_shift_duration.svg": slope_svg("duration_min", "Duration minutes", lambda v: f"{v:.1f}m"),
        "model_shift_quality.svg": slope_svg("quality", "Feature quality score", lambda v: f"{v:.0f}/100"),
        "pareto_duration_quality.svg": pareto_svg(),
        "quality_heatmap.svg": feature_heatmap_svg(),
        "defect_severity_matrix.svg": defect_matrix_svg(),
    }
    for name, svg in assets.items():
        (OUT_DIR / name).write_text(standalone_svg(svg))


def main() -> None:
    data = []
    for run in RUNS:
        item = dict(run)
        item["quality_score"] = round(quality_score(run), 1)
        data.append(item)
    (OUT_DIR / "benchmark_visualizations_data.json").write_text(json.dumps(data, indent=2) + "\n")
    (OUT_DIR / "benchmark_visualizations.html").write_text(html_report())
    write_svg_assets()


if __name__ == "__main__":
    main()
