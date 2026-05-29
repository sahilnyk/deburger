# deburger

[![PyPI version](https://img.shields.io/pypi/v/deburger.svg)](https://pypi.org/project/deburger/)
[![Python](https://img.shields.io/pypi/pyversions/deburger.svg)](https://pypi.org/project/deburger/)
[![License](https://img.shields.io/pypi/l/deburger.svg)](https://pypi.org/project/deburger/)
[![Downloads](https://img.shields.io/pypi/dm/deburger.svg)](https://pypi.org/project/deburger/)

Catch expensive cloud code before it ships. Static analysis for your cloud bill.

## Install

```bash
pip install deburger
```

## Examples

**Scan your project:**

```bash
deburger init --provider aws
deburger check .
```

<placeholder for images>

**Compare cost between branches:**

```bash
deburger diff main..feature-branch
```

**Block expensive commits with a git hook:**

```bash
deburger hook --install
git commit -m "Add feature"
# Commit blocked if expensive patterns found
```

**CI/CD integration:**

```yaml
- name: Cost Analysis
  run: |
    pip install deburger
    deburger check . --json > cost-report.json
    deburger check . || exit 1
```

**Get optimization suggestions:**

```bash
deburger optimize app.py
```

## Features

- Detects S3/storage calls in loops, missing connection pools, unbounded queries, cold start issues, sequential async, expensive logging
- Estimates monthly cost impact based on your traffic config
- Supports Python (AST) and JavaScript/TypeScript (pattern detection)
- Works with AWS, GCP, and Azure
- Git hook and CI/CD integration
- JSON output for automation (`--json`)
- Inline suppression with `deburger:ignore`
- No cloud credentials needed, runs entirely local
