#!/usr/bin/env npx tsx

import { request } from "node:https";
import { URL } from "node:url";

// ── Types ──────────────────────────────────────────────────────────────

interface Repo {
  name: string;
  stargazers_count: number;
  language: string | null;
  updated_at: string;
}

interface Options {
  username: string;
  limit: number;
  json: boolean;
}

// ── GitHub fetch ───────────────────────────────────────────────────────

function fetchJSON(url: string): Promise<{ status: number; body: unknown }> {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const req = request(
      {
        hostname: parsed.hostname,
        path: parsed.pathname + parsed.search,
        method: "GET",
        headers: {
          "User-Agent": "github-repos-cli",
          Accept: "application/vnd.github.v3+json",
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c: Buffer) => chunks.push(c));
        res.on("end", () => {
          const raw = Buffer.concat(chunks).toString();
          let body: unknown;
          try {
            body = JSON.parse(raw);
          } catch {
            body = raw;
          }
          resolve({ status: res.statusCode ?? 0, body });
        });
      },
    );
    req.on("error", reject);
    req.setTimeout(15_000, () => {
      req.destroy(new Error("Request timed out"));
    });
    req.end();
  });
}

async function fetchAllRepos(username: string): Promise<Repo[]> {
  const repos: Repo[] = [];
  let page = 1;
  const perPage = 100;
  const maxPages = 10;

  while (page <= maxPages) {
    const url = `https://api.github.com/users/${encodeURIComponent(username)}/repos?per_page=${perPage}&page=${page}`;
    const { status, body } = await fetchJSON(url);

    if (status === 404) {
      throw new Error(`User "${username}" not found`);
    }
    if (status === 403) {
      const msg =
        typeof body === "object" && body !== null && "message" in body
          ? (body as { message: string }).message
          : "Forbidden";
      throw new Error(`Rate limited or forbidden: ${msg}`);
    }
    if (status < 200 || status >= 300) {
      throw new Error(`GitHub API error (HTTP ${status})`);
    }
    if (!Array.isArray(body)) {
      throw new Error("Unexpected response format from GitHub API");
    }

    repos.push(...(body as Repo[]));
    if (body.length < perPage) break;
    page++;
  }

  return repos;
}

// ── Formatting ─────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  return iso.slice(0, 10);
}

function pad(str: string, len: number): string {
  return str.length >= len ? str.slice(0, len) : str + " ".repeat(len - str.length);
}

function printTable(repos: Repo[]): void {
  const header = { name: "Name", stars: "Stars", language: "Language", updated: "Updated" };

  const rows = repos.map((r) => ({
    name: r.name,
    stars: String(r.stargazers_count),
    language: r.language ?? "—",
    updated: formatDate(r.updated_at),
  }));

  const colW = {
    name: Math.max(header.name.length, ...rows.map((r) => r.name.length)),
    stars: Math.max(header.stars.length, ...rows.map((r) => r.stars.length)),
    language: Math.max(header.language.length, ...rows.map((r) => r.language.length)),
    updated: Math.max(header.updated.length, ...rows.map((r) => r.updated.length)),
  };

  const line = (n: string, s: string, l: string, u: string) =>
    `${pad(n, colW.name)}  ${pad(s, colW.stars)}  ${pad(l, colW.language)}  ${pad(u, colW.updated)}`;

  console.log(line(header.name, header.stars, header.language, header.updated));
  console.log(
    line(
      "─".repeat(colW.name),
      "─".repeat(colW.stars),
      "─".repeat(colW.language),
      "─".repeat(colW.updated),
    ),
  );
  for (const r of rows) {
    console.log(line(r.name, r.stars, r.language, r.updated));
  }
}

// ── CLI parsing ────────────────────────────────────────────────────────

function parseArgs(argv: string[]): Options {
  const args = argv.slice(2);
  let username = "";
  let limit = 10;
  let json = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "--limit") {
      const next = args[++i];
      if (next === undefined || Number.isNaN(Number(next)) || Number(next) < 1) {
        throw new Error("--limit requires a positive integer");
      }
      limit = Number(next);
    } else if (arg === "--json") {
      json = true;
    } else if (arg.startsWith("-")) {
      throw new Error(`Unknown flag: ${arg}`);
    } else {
      if (username) throw new Error("Only one username allowed");
      username = arg;
    }
  }

  if (!username) {
    throw new Error("Usage: github-repos <username> [--limit N] [--json]");
  }

  return { username, limit, json };
}

// ── Main ───────────────────────────────────────────────────────────────

export async function run(argv: string[]): Promise<void> {
  const opts = parseArgs(argv);
  const repos = await fetchAllRepos(opts.username);

  repos.sort((a, b) => b.stargazers_count - a.stargazers_count);
  const top = repos.slice(0, opts.limit);

  if (opts.json) {
    const output = top.map((r) => ({
      name: r.name,
      stars: r.stargazers_count,
      language: r.language,
      updated: r.updated_at,
    }));
    console.log(JSON.stringify(output, null, 2));
  } else {
    if (top.length === 0) {
      console.log("No public repositories found.");
    } else {
      printTable(top);
    }
  }
}

// Exports for testing
export { parseArgs, printTable, formatDate, fetchAllRepos, pad };
export type { Repo, Options };

// Run when executed directly
const isDirectRun =
  process.argv[1] &&
  (process.argv[1].endsWith("github-repos.ts") ||
    process.argv[1].endsWith("github-repos"));

if (isDirectRun) {
  run(process.argv).catch((err: Error) => {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  });
}
