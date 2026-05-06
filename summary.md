# AI Coding Agent Benchmark Summary

Date: 2026-04-23 (updated 2026-05-04)

This benchmark compares local runs of Codex, OMP, OpenCode, and Claude Code on the same TypeScript CLI task.

Task: create a TypeScript CLI that accepts a GitHub username, fetches public repositories, sorts by stars, outputs a table or JSON, supports `--limit N`, handles errors, and includes tests.

Prompt: `prompt.md`

Results: `results/*.csv`

## Scope

Two model families were tested:

| Model | Tools tested | Notes |
|---|---|---|
| GPT-5.4 | Codex, OMP, OpenCode, Claude Code | Full four-way comparison completed. |
| Opus 4.6 | Codex, OMP, OpenCode, Claude Code | Full four-way comparison completed. |

Opus 4.6 routing used:

| Tool | Selector | Verified model |
|---|---|---|
| Claude Code | `--model opus` | `kiro-claude-opus-4-6` |
| OMP | `--model quotio/kiro-claude-opus-4-6` | `kiro-claude-opus-4-6` |
| OpenCode | `-m quotio/kiro-claude-opus-4-6` | `kiro-claude-opus-4-6` |
| Codex | `-p omniroute-opus` | `kr/claude-opus-4.6` via omniroute |

## GPT-5.4 Results

### Resources And Tokens

| Tool | Peak RSS | Avg RSS | Peak CPU | Avg CPU | Duration | Fresh Tokens | Cache Reads | Total Tokens | Rounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Codex | 69.9 MB | 63.1 MB | 6.5% | 1.0% | ~4.0 min | ~37K | — | ~37K | ~few |
| OMP | 305 MB | ~180 MB | 28% | ~15% | ~10.0 min | ~66K | 1,127K | 1,193K | 29 |
| OpenCode | 462 MB | 419 MB | 112.6% | 31.7% | ~2.0 min | ~127K | 9K | 136K | 7 |
| Claude Code | 406.5 MB | 359.9 MB | 57.6% | 20.9% | ~2.0 min | ~106K | 745K | 851K | 26 |

### Code Quality

| Tool | Lines | Tests | Pagination | Timeout | API Version Header | Clean JSON | Main Issue |
|---|---:|---:|---|---|---|---|---|
| Codex | 446 | 13 | Yes | No | Yes | Yes | No timeout; silent 100-page cap. |
| OMP | 503 | 8 | Yes | Yes (10s) | Yes | No | Over-structured; JSON emits full GitHub blob. |
| OpenCode | 382 | 10 | No | No | No | Yes | Missing pagination; wrong output on first run. |
| Claude Code | 336 | 12 | No | No | No | No | Missing pagination; raw GitHub field names. |

GPT-5.4 ranking:

| Rank | Tool | Reason |
|---:|---|---|
| 1 | Codex | Best resource/token efficiency and strong correctness on rerun. |
| 2 | OMP | Most defensive implementation, but over-structured and slower. |
| 3 | Claude Code | Lean and adaptive, but incomplete. |
| 4 | OpenCode | Fast but least reliable; missed pagination in GPT run. |

## Opus 4.6 Results

### Resources And Tokens

| Tool | Peak RSS | Avg RSS | Peak CPU | Avg CPU | Duration | Fresh Tokens | Cache Reads | Total Tokens | Rounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Codex | 73.7 MB | 47.6 MB | 33.2% | 1.4% | ~2.0 min | ~57K | 0 | ~57K | ~few |
| OMP | 451.6 MB | 221.8 MB | 52.6% | 1.6% | ~2.3 min | ~40K | 0 | ~40K | 7 |
| OpenCode | 347.4 MB | 256.6 MB | 101.1% | 7.8% | ~3.3 min | ~86K | 0 | ~86K | 15 |
| Claude Code | 319.0 MB | 191.5 MB | 112.7% | 9.6% | ~4.1 min | ~429K | 0 | ~429K | 47 |

OMP Opus token data was recovered from:

`~/.omp/agent/sessions/-benchmark-omp-opus46/2026-04-23T18-36-08-728Z_14c635852615c263.jsonl`

### Code Quality

| Tool | Lines | Tests | Pagination | Timeout | API Version Header | Clean JSON | Live Verification | Main Issue |
|---|---:|---:|---|---|---|---|---|---|
| Codex | 379 | 18 | Yes | Yes (15s) | Yes | Yes | Yes | 10-page cap. |
| OMP | 338 | 21 | Yes | Yes (15s) | No | Yes | Yes | Fetch/network behavior not unit-tested; no tie-breaker. |
| OpenCode | 316 | 20 | Yes | No | No | Yes | Yes, then rate-limited | No timeout; weaker error-path coverage. |
| Claude Code | 225 | 11 embedded | Yes | No | No | No | No; sandbox/rate-limit blocked | Tests embedded in production file; no separate test file. |

Opus 4.6 ranking:

| Rank | Tool | Reason |
|---:|---|---|
| 1 | Codex | Fastest, lightest RSS/CPU, pagination, timeout, API header, clean JSON, separate tests, live demo. |
| 2 | OMP | Lowest token count, pagination, timeout, separate tests; higher RSS than Codex. |
| 3 | OpenCode | Much improved vs GPT run: paginated, clean JSON, separate tests; higher tokens/resources. |
| 4 | Claude Code | Pagination present, but output shape is structurally wrong because tests live inside the CLI file. |

## Merged Table

| Tool | Model | Peak RSS | Avg RSS | Peak CPU | Avg CPU | Duration | Fresh Tokens | Cache Reads | Total Tokens | Rounds | Quality Summary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Codex | GPT-5.4 | 69.9 MB | 63.1 MB | 6.5% | 1.0% | ~4.0 min | ~37K | — | ~37K | ~few | Best single greenfield run. |
| Codex | Opus 4.6 | 73.7 MB | 47.6 MB | 33.2% | 1.4% | ~2.0 min | ~57K | 0 | ~57K | ~few | Fastest Opus run; full feature set. |
| OMP | GPT-5.4 | 305 MB | ~180 MB | 28% | ~15% | ~10.0 min | ~66K | 1,127K | 1,193K | 29 | Defensive but over-structured. |
| OMP | Opus 4.6 | 451.6 MB | 221.8 MB | 52.6% | 1.6% | ~2.3 min | ~40K | 0 | ~40K | 7 | Best Opus token efficiency. |
| OpenCode | GPT-5.4 | 462 MB | 419 MB | 112.6% | 31.7% | ~2.0 min | ~127K | 9K | 136K | 7 | Fast, but missed pagination and first run was wrong. |
| OpenCode | Opus 4.6 | 347.4 MB | 256.6 MB | 101.1% | 7.8% | ~3.3 min | ~86K | 0 | ~86K | 15 | Much improved over GPT run. |
| Claude Code | GPT-5.4 | 406.5 MB | 359.9 MB | 57.6% | 20.9% | ~2.0 min | ~106K | 745K | 851K | 26 | Lean but incomplete. |
| Claude Code | Opus 4.6 | 319.0 MB | 191.5 MB | 112.7% | 9.6% | ~4.1 min | ~429K | 0 | ~429K | 47 | Structurally flawed; tests in CLI file. |

### Harness Averages

| Harness | Completed Runs | Avg Peak RSS | Avg RSS | Avg Peak CPU | Avg CPU | Avg Duration |
|---|---:|---:|---:|---:|---:|---:|
| Codex | 2 | 71.8 MB | 55.4 MB | 19.9% | 1.2% | ~3.0 min |
| OMP | 2 | 378.3 MB | ~200.9 MB | 40.3% | ~8.3% | ~6.2 min |
| OpenCode | 2 | 404.7 MB | 337.8 MB | 106.9% | 19.8% | ~2.7 min |
| Claude Code | 2 | 362.8 MB | 275.7 MB | 85.2% | 15.3% | ~3.1 min |

System-only interpretation:

- Codex is the lightest harness across both runs by a wide margin: lowest avg RSS (55.4 MB) and lowest avg CPU (1.2%).
- OMP has the second-lowest average CPU among the multi-run tools, but its average duration is pulled up by the slow GPT-5.4 run.
- OpenCode is fastest on average among the multi-run tools, but has the highest average CPU pressure.
- Claude Code is middle on memory and duration, but had high peak CPU on Opus 4.6.

## Model Data Visualizations

These views are better for model/run-level data than a single average table, because model choice changes behavior materially.

### Fresh Token Bars

Lower is better.

| Run | Fresh Tokens | Bar |
|---|---:|---|
| Codex / GPT-5.4 | ~37K | #### |
| OMP / Opus 4.6 | ~40K | #### |
| Codex / Opus 4.6 | ~57K | ###### |
| OMP / GPT-5.4 | ~66K | ####### |
| OpenCode / Opus 4.6 | ~86K | ######### |
| Claude Code / GPT-5.4 | ~106K | ########### |
| OpenCode / GPT-5.4 | ~127K | ############# |
| Claude Code / Opus 4.6 | ~429K | ########################################### |

### Model Shift By Harness

Shows how each harness changed when moving from GPT-5.4 to Opus 4.6.

| Harness | Fresh Tokens: GPT-5.4 -> Opus 4.6 | Quality: GPT-5.4 -> Opus 4.6 | System: GPT-5.4 -> Opus 4.6 |
|---|---|---|---|
| Codex | ~37K -> ~57K | Best GPT run -> Best Opus run | Slightly higher peak CPU; lower RSS and faster |
| OMP | ~66K -> ~40K | Good -> Strong | Slower/high-cache GPT run -> faster/lower-CPU Opus run |
| OpenCode | ~127K -> ~86K | Weak -> Strong | High CPU both runs, lower RSS on Opus |
| Claude Code | ~106K -> ~429K | Incomplete -> structurally flawed | Lower avg RSS on Opus, higher peak CPU |

### Feature Heatmap

Best read as a correctness map, not a resource map.

| Run | Pagination | Timeout | Clean JSON | Separate Tests | Live Demo | Main Defect |
|---|---|---|---|---|---|---|
| Codex / GPT-5.4 | Yes | No | Yes | Yes | Yes | No timeout; 100-page cap |
| Codex / Opus 4.6 | Yes | Yes (15s) | Yes | Yes | Yes | 10-page cap |
| OMP / GPT-5.4 | Yes | Yes | No | Yes | Yes | Full GitHub blob JSON |
| OMP / Opus 4.6 | Yes | Yes | Yes | Yes | Yes | No fetch tests |
| OpenCode / GPT-5.4 | No | No | Yes | Yes | Retry only | Missing pagination |
| OpenCode / Opus 4.6 | Yes | No | Yes | Yes | Yes | Weaker error tests |
| Claude Code / GPT-5.4 | No | No | No | Yes | Yes | Missing pagination |
| Claude Code / Opus 4.6 | Yes | No | No | No | No | Tests embedded in CLI file |

## Review Findings

### GPT-5.4

| Tool | Findings |
|---|---|
| Codex | No timeout. Has a 100-page pagination cap that can silently truncate extremely large users. |
| OMP | Most defensive. JSON output is noisy because it emits full GitHub API objects. Structure heavier than task required. |
| OpenCode | Missing pagination. Did not notice wrong first-run output. Highest resource use and worst fresh-token use. |
| Claude Code | Missing pagination. JSON uses raw GitHub field names rather than task-oriented fields. |

### Opus 4.6

| Tool | Findings |
|---|---|
| Codex | No material runtime defect. Uses `node:https` directly instead of `fetch`. Has a 10-page pagination cap (1000 repos max). Timeout present (15s). API version header present. Clean JSON output with mapped fields. |
| OMP | No material runtime defect. Medium concern: fetch/network behavior is not unit-tested. Low concern: no deterministic tie-breaker for equal stars. |
| OpenCode | No material runtime defect. Medium concern: no network-error test. Low concern: rate-limit error lacks reset time. |
| Claude Code | High severity: embedded tests inside `github-repos.ts`, so CLI execution runs tests first. Also claimed a separate test file that was not created. |

## Final Ranking

| Scope | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| GPT-5.4 | Codex | OMP | Claude Code | OpenCode |
| Opus 4.6 | Codex | OMP | OpenCode | Claude Code |
| Across completed runs | Codex | OMP | OpenCode | Claude Code |

## Caveats

- This is a local-machine benchmark, not a statistically powered benchmark suite.
- GitHub unauthenticated API rate limits affected later live verification checks.
- GPT-5.4 and Opus 4.6 runs are not perfectly equivalent because tool sandboxes and provider paths differ.
- Codex Opus 4.6 was routed via omniroute (`kr/claude-opus-4.6`); other tools used `quotio/kiro-claude-opus-4-6`. Both resolve to the same underlying model.
- OMP wraps Pi. OMP-specific conclusions here should not be inferred from OpenCode-specific external claims.

## Files

Benchmark directories:

- `codex/`
- `codex2/`
- `codex-opus46/`
- `omp/`
- `opencode/`
- `claude-code/`
- `omp-opus46/`
- `opencode-opus46/`
- `claude-opus46/`

Resource CSVs:

- `results/codex.csv`
- `results/codex2.csv`
- `results/codex-opus46.csv`
- `results/omp.csv`
- `results/opencode.csv`
- `results/claude-code.csv`
- `results/omp-opus46.csv`
- `results/opencode-opus46.csv`
- `results/claude-opus46.csv`

Useful scripts:

- `monitor.sh`
- `run_opencode.sh`
- `run_claude.sh`
- `run_codex_opus46.sh`
- `run_omp_opus46.sh`
- `run_opencode_opus46.sh`
- `run_claude_opus46.sh`
