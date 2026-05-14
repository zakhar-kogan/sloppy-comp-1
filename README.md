# AI Coding Agent Benchmark

Local benchmark comparing Codex, OMP, OpenCode, Claude Code, and Droid on the same TypeScript CLI task across GPT-5.4 and Opus 4.6. The task: fetch a GitHub user's public repositories, sort by stars, support table/JSON output, `--limit N`, error handling, and tests.

This is an exploratory local-machine benchmark, not a statistically powered benchmark suite.

## Key findings

- **Codex / Opus 4.6** was the strongest completed run: fastest (~2.0 min), lightest (47.6 MB avg RSS), paginated, timeout-aware, clean JSON, API header, separate tests, live demo.
- **Codex / GPT-5.4** remains the lightest on fresh tokens (~37K), but lacked a timeout.
- **OMP / Opus 4.6** had the lowest reliably accounted token count among Opus runs (~40K), with pagination and timeout.
- **Droid / Opus 4.6** was the fastest wall-clock run (~1.3 min) and produced a working paginated CLI, but needed a one-tool BYOK workaround and lacked a timeout/API version header.
- **OpenCode** was fast, but the GPT run missed pagination; the Opus run improved materially.
- **Claude Code** had the weakest reliability profile, especially the Opus run with tests embedded in the production CLI file.

## Main view: duration vs quality

Upper-left is better: shorter duration, higher checklist quality. Bubble size is fresh token usage.

<img src="visualizations/pareto_duration_quality.png" alt="Pareto chart of duration versus quality score">

## Correctness heatmaps

Checklist score uses yes=1, partial=0.5, no=0.

<img src="visualizations/quality_heatmap.png" alt="Quality heatmap across completed benchmark runs">

Severity is qualitative and derived from manual review findings in `summary.md`. Total uses High=3, Medium=2, Low=1, None=0.

<img src="visualizations/defect_severity_matrix.png" alt="Defect severity matrix across completed benchmark runs">

## More detail

- Narrative summary: [`summary.md`](summary.md)
- Full visual report: [`visualizations/benchmark_visualizations.html`](visualizations/benchmark_visualizations.html)
- Normalized visualization data: [`visualizations/benchmark_visualizations_data.json`](visualizations/benchmark_visualizations_data.json)
- Raw resource metrics: [`results/`](results/)

## Reproduce visualizations

```sh
python3 visualizations/build_visualizations.py
```

## Caveats

- Local-machine benchmark only.
- Small sample size.
- Some summary values are approximate.
- GitHub unauthenticated API rate limits affected later live verification checks.
- GPT-5.4 and Opus 4.6 runs are not perfectly equivalent because tool sandboxes and provider paths differ.
- Codex Opus 4.6 was routed via omniroute; other tools used quotio. Both resolve to the same underlying model.
