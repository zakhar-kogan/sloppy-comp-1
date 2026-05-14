import { test } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

type Repo = {
  name: string;
  stargazers_count: number;
  language: string | null;
  updated_at: string;
};

type FetchLike = (input: string | URL, init?: RequestInit) => Promise<Response>;

function parseArgs(argv: string[]) {
  let username: string | undefined;
  let limit = 10;
  let json = false;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === '--json') {
      json = true;
      continue;
    }

    if (arg === '--limit') {
      const value = argv[index + 1];
      if (value === undefined) {
        throw new Error('Missing value for --limit');
      }

      if (!/^\d+$/.test(value) || Number(value) < 1) {
        throw new Error('Invalid value for --limit. Expected a positive integer.');
      }

      limit = Number(value);
      index += 1;
      continue;
    }

    if (arg.startsWith('--')) {
      throw new Error(`Unknown flag: ${arg}`);
    }

    if (username !== undefined) {
      throw new Error(`Unexpected argument: ${arg}`);
    }

    username = arg;
  }

  if (!username) {
    throw new Error('Usage: npx tsx github-repos.ts <github-username> [--limit N] [--json]');
  }

  return { username, limit, json };
}

async function fetchRepos(username: string, fetchImpl: FetchLike = fetch): Promise<Repo[]> {
  let response: Response;

  try {
    response = await fetchImpl(`https://api.github.com/users/${encodeURIComponent(username)}/repos?per_page=100&sort=updated`, {
      headers: {
        Accept: 'application/vnd.github+json',
        'User-Agent': 'github-repos-cli',
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Network error while fetching repositories: ${message}`);
  }

  if (response.status === 404) {
    throw new Error(`GitHub user not found: ${username}`);
  }

  if (response.status === 403) {
    const remaining = response.headers.get('x-ratelimit-remaining');
    if (remaining === '0') {
      const reset = response.headers.get('x-ratelimit-reset');
      const resetMessage = reset ? ` Rate limit resets at ${new Date(Number(reset) * 1000).toISOString()}.` : '';
      throw new Error(`GitHub API rate limit exceeded.${resetMessage}`);
    }
  }

  if (!response.ok) {
    throw new Error(`GitHub API request failed with status ${response.status} ${response.statusText}`);
  }

  const payload = await response.json();

  if (!Array.isArray(payload)) {
    throw new Error('Unexpected response format from GitHub API');
  }

  return payload.map((repo) => ({
    name: String(repo.name),
    stargazers_count: Number(repo.stargazers_count ?? 0),
    language: repo.language === null ? null : String(repo.language),
    updated_at: String(repo.updated_at),
  }));
}

function sortAndLimitRepos(repos: Repo[], limit: number) {
  return [...repos]
    .sort((left, right) => right.stargazers_count - left.stargazers_count || left.name.localeCompare(right.name))
    .slice(0, limit);
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toISOString().slice(0, 10);
}

function renderTable(repos: Repo[]) {
  const headers = ['Name', 'Stars', 'Language', 'Last Updated'];
  const rows = repos.map((repo) => [
    repo.name,
    String(repo.stargazers_count),
    repo.language ?? '-',
    formatDate(repo.updated_at),
  ]);

  const widths = headers.map((header, columnIndex) =>
    Math.max(header.length, ...rows.map((row) => row[columnIndex].length)),
  );

  const formatRow = (row: string[]) =>
    row
      .map((cell, columnIndex) => {
        const width = widths[columnIndex];
        return columnIndex === 1 ? cell.padStart(width) : cell.padEnd(width);
      })
      .join('  ');

  const divider = widths.map((width) => '-'.repeat(width)).join('  ');

  return [formatRow(headers), divider, ...rows.map(formatRow)].join('\n');
}

async function run(argv: string[], fetchImpl: FetchLike = fetch) {
  const options = parseArgs(argv);
  const repos = await fetchRepos(options.username, fetchImpl);
  const result = sortAndLimitRepos(repos, options.limit);

  if (options.json) {
    return JSON.stringify(result, null, 2);
  }

  return renderTable(result);
}

async function main() {
  try {
    const output = await run(process.argv.slice(2));
    process.stdout.write(`${output}\n`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  }
}

async function maybeRunEmbeddedTests() {
  const scriptPath = process.argv[1];
  const shouldRun =
    process.execArgv.includes('--test') &&
    typeof scriptPath === 'string' &&
    path.resolve(scriptPath) === path.resolve(import.meta.filename);

  if (!shouldRun) {
    return false;
  }

  return true;
}

function createJsonResponse(data: unknown, init?: ResponseInit) {
  return new Response(JSON.stringify(data), {
    headers: { 'content-type': 'application/json' },
    ...init,
  });
}

test('parseArgs handles username and flags', () => {
  assert.deepEqual(parseArgs(['sindresorhus', '--limit', '5', '--json']), {
    username: 'sindresorhus',
    limit: 5,
    json: true,
  });
});

test('parseArgs rejects invalid limit', () => {
  assert.throws(() => parseArgs(['sindresorhus', '--limit', '0']), /Invalid value for --limit/);
});

test('sortAndLimitRepos orders by stars descending', () => {
  const repos: Repo[] = [
    { name: 'b', stargazers_count: 10, language: 'TS', updated_at: '2024-01-01T00:00:00Z' },
    { name: 'a', stargazers_count: 10, language: 'TS', updated_at: '2024-01-01T00:00:00Z' },
    { name: 'c', stargazers_count: 2, language: null, updated_at: '2024-01-01T00:00:00Z' },
  ];

  assert.deepEqual(
    sortAndLimitRepos(repos, 2).map((repo) => repo.name),
    ['a', 'b'],
  );
});

test('renderTable prints headers and rows', () => {
  const output = renderTable([
    { name: 'alpha', stargazers_count: 42, language: 'TypeScript', updated_at: '2024-06-01T12:00:00Z' },
  ]);

  assert.match(output, /Name/);
  assert.match(output, /alpha/);
  assert.match(output, /2024-06-01/);
});

test('fetchRepos maps successful responses', async () => {
  const repos = await fetchRepos('demo', async () =>
    createJsonResponse([{ name: 'repo', stargazers_count: 3, language: 'JS', updated_at: '2024-01-01T00:00:00Z' }]),
  );

  assert.deepEqual(repos, [
    { name: 'repo', stargazers_count: 3, language: 'JS', updated_at: '2024-01-01T00:00:00Z' },
  ]);
});

test('fetchRepos reports missing users', async () => {
  await assert.rejects(
    () => fetchRepos('missing', async () => new Response('Not Found', { status: 404, statusText: 'Not Found' })),
    /GitHub user not found: missing/,
  );
});

test('fetchRepos reports rate limiting', async () => {
  await assert.rejects(
    () =>
      fetchRepos(
        'busy',
        async () =>
          new Response('Forbidden', {
            status: 403,
            statusText: 'Forbidden',
            headers: {
              'x-ratelimit-remaining': '0',
              'x-ratelimit-reset': '1710000000',
            },
          }),
      ),
    /GitHub API rate limit exceeded/,
  );
});

test('run returns JSON when requested', async () => {
  const output = await run(['demo', '--json', '--limit', '1'], async () =>
    createJsonResponse([
      { name: 'repo', stargazers_count: 7, language: 'TS', updated_at: '2024-01-01T00:00:00Z' },
      { name: 'repo-2', stargazers_count: 1, language: null, updated_at: '2024-01-02T00:00:00Z' },
    ]),
  );

  const parsed = JSON.parse(output) as Repo[];
  assert.equal(parsed.length, 1);
  assert.equal(parsed[0].name, 'repo');
});

const entrypoint = process.argv[1] ? pathToFileURL(path.resolve(process.argv[1])).href : undefined;

if (entrypoint && import.meta.url === entrypoint) {
  void (async () => {
    if (await maybeRunEmbeddedTests()) {
      return;
    }

    await main();
  })();
}
