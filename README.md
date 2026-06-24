# deburger 🍔

**Catch expensive cloud code before it ships.** Static analysis that detects costly patterns and estimates your monthly bill impact — fully local, no credentials needed.

[![PyPI version](https://img.shields.io/pypi/v/deburger.svg)](https://pypi.org/project/deburger/)
[![Python](https://img.shields.io/pypi/pyversions/deburger.svg)](https://pypi.org/project/deburger/)
[![License](https://img.shields.io/pypi/l/deburger.svg)](https://pypi.org/project/deburger/)

## Why deburger?

> "We found $8K/mo in Lambda waste after running deburger once." — beta user

Every N+1 query, unbounded `SELECT *`, or S3 call in a loop burns money. deburger finds them before they hit prod and **shows you the math** — pricing source, formula, and exact monthly cost.

```bash
pip install deburger
deburger check .
```

## When to use

| When | What it finds |
|------|--------------|
| CI/CD pipeline | Blocks PRs that add expensive patterns |
| Before deployment | `deburger check` scans changed files via git |
| Code review | `deburger diff main..feature` shows cost delta |
| Cost optimization | `deburger optimize --apply` auto-fixes code |

## Quickstart

```bash
# init project config
deburger init --provider aws

# scan for expensive code
deburger check .

# get detailed cost breakdown with math
deburger check -v

# auto-fix what you can
deburger optimize --apply
```

## What it detects

| Pattern | Cost Impact |
|---------|-------------|
| N+1 queries in loops | up to 100x more DB IOs |
| Sequential async calls | 2-10x slower execution → more compute |
| S3/storage calls in loops | 10-100x more API requests |
| Unbounded queries (no LIMIT) | OOM risk + data transfer costs |
| Missing connection pools | 50ms+ overhead per request |
| Heavy imports on cold starts | 500ms-2s extra Lambda duration |
| Expensive logging in loops | CloudWatch costs scale with traffic |
| Unindexed queries, full scans | DB CPU + IO spikes |

## Integrations

- **CI/CD**: `--json` output, non-zero exit on issues
- **Git hooks**: `deburger hook --install` to block expensive commits
- **GitHub PRs**: `deburger pr-comment 42` posts cost breakdown
- **Cloud providers**: AWS, GCP, Azure pricing models
- **Languages**: Python (AST), JavaScript/TypeScript (pattern matching)

## CLI

| Command | Description |
|---------|-------------|
| `deburger check .` | Scan for expensive patterns |
| `deburger check -v` | With cost breakdown evidence |
| `deburger check --json` | Machine-readable for CI |
| `deburger optimize` | Generate + apply auto-fixes |
| `deburger diff base..head` | Compare cost impact between branches |
| `deburger blame .` | Cost leaderboard by developer |
| `deburger hook --install` | Pre-commit hook |
| `deburger pr-comment <n>` | GitHub PR cost comment |
| `deburger init` | Create project config |

## Privacy

Fully local. No code sent anywhere, no API keys, no telemetry.
