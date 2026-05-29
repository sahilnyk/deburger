# deburger

[![PyPI version](https://img.shields.io/pypi/v/deburger.svg)](https://pypi.org/project/deburger/)
[![Python](https://img.shields.io/pypi/pyversions/deburger.svg)](https://pypi.org/project/deburger/)
[![License](https://img.shields.io/pypi/l/deburger.svg)](https://pypi.org/project/deburger/)
[![Downloads](https://img.shields.io/pypi/dm/deburger.svg)](https://pypi.org/project/deburger/)

your cloud bill is cooked. deburger finds the expensive code *before* it hits prod.

## Install

```bash
pip install deburger
```

## Commands

### `deburger init`

*sets up your project config — takes 2 seconds*

```bash
deburger init --provider aws
```

```
created .deburger.yml (provider: aws)
run 'deburger check' to start scanning
```

### `deburger check`

*the main one — scans your code and shows what's burning money*

```bash
deburger check .
```

```
issues found
┏━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ file   ┃ line ┃ type            ┃ severity ┃ monthly cost ┃ savings ┃
┡━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ app.py │   42 │ s3 in loop      │ high     │      $120.00 │ $108.00 │
│ api.py │   15 │ unbounded query │ critical │       $25.00 │  $22.50 │
└────────┴──────┴─────────────────┴──────────┴──────────────┴─────────┘

╭─────────── cost summary ───────────╮
│ total monthly waste: $145.00       │
│ after optimization: $14.50         │
│ savings: 90%                       │
╰────────────────────────────────────╯
```

*add `-v` for detailed explanations and fix suggestions per issue*

### `deburger check --json`

*for CI pipelines — spits out machine-readable output*

```bash
deburger check . --json
```

```json
{
  "issues": [
    {
      "file": "app.py",
      "line": 42,
      "type": "s3_in_loop",
      "severity": "high",
      "monthly_cost": 120.0,
      "savings": 108.0,
      "fix": "Use batch operations"
    }
  ],
  "summary": {
    "total_issues": 2,
    "total_monthly_cost": 145.0,
    "savings_percentage": 90
  }
}
```

### `deburger optimize`

*generates actual fixes — not just complaints*

```bash
deburger optimize .
```

```
optimizations
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ file       ┃ fix                        ┃ confidence ┃ savings/mo┃ auto-safe ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━┩
│ app.py:42  │ Replace with batch get     │        92% │   $108.00 │ yes       │
│ api.py:15  │ Add LIMIT clause           │        87% │    $22.50 │ no        │
└────────────┴────────────────────────────┴────────────┴───────────┴───────────┘

total potential savings: $130.50/mo

run with --apply to apply fixes
```

### `deburger diff`

*compare cost impact between branches — great for PR reviews*

```bash
deburger diff main..feature-branch
```

```
main -> feature-branch
3 files changed

new issues: 2
estimated cost impact: $145.00/mo
  app.py:42 - s3_in_loop
  api.py:15 - unbounded_query
```

### `deburger blame`

*find out who's costing the most lol*

```bash
deburger blame .
```

```
cost leaderboard (who's burning money)
┏━━━┳━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ developer   ┃ issues ┃ monthly cost ┃ worst issue              ┃
┡━━━╇━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ sahil       │      4 │      $230.00 │ S3 in loop               │
│ 2 │ dev2        │      2 │       $45.00 │ unbounded query          │
└───┴─────────────┴────────┴──────────────┴──────────────────────────┘

total waste: $275.00/month
```

### `deburger hook`

*auto-blocks expensive commits so they never reach the repo*

```bash
deburger hook --install
```

```
pre-commit hook installed
deburger will run on every commit
```

now every `git commit` runs a cost check first. expensive code = blocked.

### `deburger pr-comment`

*drops a cost breakdown comment on your github PR*

```bash
deburger pr-comment 42
```

```
comment posted on PR #42
```

## Features

| feature | details |
|---------|---------|
| pattern detection | N+1 queries, S3 in loops, unbounded queries, cold starts, sequential async |
| cost estimation | monthly $ impact from your traffic config |
| languages | Python (AST) + JS/TS (pattern matching) |
| cloud providers | AWS, GCP, Azure |
| CI/CD | `--json` output, non-zero exit on issues |
| git hooks | blocks expensive commits automatically |
| suppression | `deburger:ignore` for false positives |
| privacy | fully local — no creds, no network |
