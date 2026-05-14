import { parseArgs } from "node:util";
import { describe, it, mock } from "node:test";
import assert from "node:assert";

// ─── Types ───────────────────────────────────────────────────────────────────

interface Repo {
  name: string;
  stargazers_count: number;
  language: string | null;
  updated_at: string;
}

interface FetchOptions {
  username: string;
  limit: number;
  json: boolean;
}

// ─── Core logic ──────────────────────────────────────────────────────────────

async function fetchRepos(username: string): Promise<Repo[]> {
  const repos: Repo[] = [];
  let page = 1;
  const perPage = 100;

  while (true) {
    const url = `https://api.github.com/users/${encodeURIComponent(username)}/repos?per_page=${perPage}&page=${page}`;
    const res = await fetch(url, {
      headers: { Accept: "application/vnd.github.v3+json", "User-Agent": "github-repos-cli" },
    });

    if (res.status === 404) {
      throw new Error(`User "${username}" not found.`);
    }
    if (res.status === 403 || res.status === 429) {
      const reset = res.headers.get("x-ratelimit-reset");
      const resetTime = reset ? new Date(Number(reset) * 1000).toISOString() : "unknown";
      throw new Error(`Rate limited by GitHub API. Resets at ${resetTime}.`);
    }
    if (!res.ok) {
      throw new Error(`GitHub API error: ${res.status} ${res.statusText}`);
    }

    const data: Repo[] = await res.json() as Repo[];
    repos.push(...data);

    if (data.length < perPage) break;
    page++;
  }

  return repos;
}

function sortByStars(repos: Repo[]): Repo[] {
  return [...repos].sort((a, b) => b.stargazers_count - a.stargazers_count);
}

function formatTable(repos: Repo[]): string {
  const header = ["Name", "Stars", "Language", "Last Updated"];
  const rows = repos.map((r) => [
    r.name,
    String(r.stargazers_count),
    r.language ?? "—",
    r.updated_at.slice(0, 10),
  ]);

  const widths = header.map((h, i) =>
    Math.max(h.length, ...rows.map((row) => row[i].length))
  );

  const sep = widths.map((w) => "─".repeat(w + 2)).join("┼");
  const fmt = (row: string[]) =>
    row.map((cell, i) => ` ${cell.padEnd(widths[i])} `).join("│");

  return [fmt(header), sep, ...rows.map(fmt)].join("\n");
}

function formatJson(repos: Repo[]): string {
  return JSON.stringify(
    repos.map((r) => ({
      name: r.name,
      stars: r.stargazers_count,
      language: r.language,
      updated_at: r.updated_at,
    })),
    null,
    2
  );
}

// ─── CLI ─────────────────────────────────────────────────────────────────────

async function main() {
  const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: {
      limit: { type: "string", short: "l", default: "10" },
      json: { type: "boolean", default: false },
      help: { type: "boolean", short: "h", default: false },
      test: { type: "boolean", default: false },
    },
  });

  if (values.test) {
    await runTests();
    return;
  }

  if (values.help || positionals.length === 0) {
    console.log(`Usage: npx tsx github-repos.ts <username> [--limit N] [--json]

Options:
  --limit, -l   Number of repos to show (default: 10)
  --json        Output raw JSON instead of table
  --help, -h    Show this help message
  --test        Run unit tests`);
    process.exit(values.help ? 0 : 1);
  }

  const username = positionals[0];
  const limit = Math.max(1, parseInt(values.limit as string, 10) || 10);
  const useJson = values.json ?? false;

  try {
    const repos = await fetchRepos(username);
    const sorted = sortByStars(repos).slice(0, limit);

    if (sorted.length === 0) {
      console.log(`No public repositories found for "${username}".`);
      return;
    }

    console.log(useJson ? formatJson(sorted) : formatTable(sorted));
  } catch (err: any) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

// ─── Tests ───────────────────────────────────────────────────────────────────

async function runTests() {
  const { test } = await import("node:test");

  await test("sortByStars sorts descending", () => {
    const repos: Repo[] = [
      { name: "a", stargazers_count: 5, language: "TS", updated_at: "2024-01-01T00:00:00Z" },
      { name: "b", stargazers_count: 100, language: "JS", updated_at: "2024-02-01T00:00:00Z" },
      { name: "c", stargazers_count: 50, language: null, updated_at: "2024-03-01T00:00:00Z" },
    ];
    const sorted = sortByStars(repos);
    assert.strictEqual(sorted[0].name, "b");
    assert.strictEqual(sorted[1].name, "c");
    assert.strictEqual(sorted[2].name, "a");
  });

  await test("sortByStars does not mutate original", () => {
    const repos: Repo[] = [
      { name: "x", stargazers_count: 1, language: null, updated_at: "2024-01-01T00:00:00Z" },
      { name: "y", stargazers_count: 99, language: null, updated_at: "2024-01-01T00:00:00Z" },
    ];
    const sorted = sortByStars(repos);
    assert.strictEqual(repos[0].name, "x");
    assert.notStrictEqual(sorted, repos);
  });

  await test("formatTable produces correct structure", () => {
    const repos: Repo[] = [
      { name: "hello", stargazers_count: 42, language: "Go", updated_at: "2024-06-15T10:00:00Z" },
    ];
    const table = formatTable(repos);
    assert.ok(table.includes("hello"));
    assert.ok(table.includes("42"));
    assert.ok(table.includes("Go"));
    assert.ok(table.includes("2024-06-15"));
    assert.ok(table.includes("Name"));
    assert.ok(table.includes("Stars"));
  });

  await test("formatTable handles null language", () => {
    const repos: Repo[] = [
      { name: "nil", stargazers_count: 0, language: null, updated_at: "2024-01-01T00:00:00Z" },
    ];
    const table = formatTable(repos);
    assert.ok(table.includes("—"));
  });

  await test("formatJson produces valid JSON with correct fields", () => {
    const repos: Repo[] = [
      { name: "proj", stargazers_count: 7, language: "Rust", updated_at: "2024-04-01T00:00:00Z" },
    ];
    const output = formatJson(repos);
    const parsed = JSON.parse(output);
    assert.strictEqual(parsed.length, 1);
    assert.strictEqual(parsed[0].name, "proj");
    assert.strictEqual(parsed[0].stars, 7);
    assert.strictEqual(parsed[0].language, "Rust");
    assert.strictEqual(parsed[0].updated_at, "2024-04-01T00:00:00Z");
  });

  await test("fetchRepos throws on invalid user", async () => {
    await assert.rejects(
      () => fetchRepos("__this_user_definitely_does_not_exist_xyz123__"),
      (err: Error) => {
        assert.ok(err.message.includes("not found"));
        return true;
      }
    );
  });
}

// ─── Entry point ─────────────────────────────────────────────────────────────

main();
