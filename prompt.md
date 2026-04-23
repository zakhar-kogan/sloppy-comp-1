# Benchmark Task

Create a CLI tool in TypeScript that:

1. Accepts a GitHub username as a CLI argument
2. Fetches their public repositories using the GitHub REST API (no auth required)
3. Sorts repos by star count (descending)
4. Outputs a formatted table showing: name, stars, language, last updated
5. Supports a `--limit N` flag to show top N repos (default: 10)
6. Supports a `--json` flag to output raw JSON instead of a table
7. Includes proper error handling (invalid user, network errors, rate limiting)
8. Includes tests

Constraints:
- Use only node built-ins and the standard test runner (node:test)
- No external dependencies
- Single file is fine if it stays clean
- Use `npx tsx` to run

When done, run the tests and demonstrate the tool with the username "sindresorhus".
