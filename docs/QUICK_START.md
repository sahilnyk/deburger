# deburger commands and use cases

This guide covers each CLI command with a practical use case.

## Install

```bash
pip install deburger
```

## Init

Create a config file in your repo.

```bash
deburger init --provider aws
```

Use when you start a new project or want a baseline config.

## Check

Scan a path and estimate monthly cost impact.

```bash
deburger check .
deburger check src/ --full
```

Use when you want a quick cost scan before merging changes.

## Diff

Compare two git refs and see cost impact between branches.

```bash
deburger diff main..feature/new-cache
```

Use during code review or before opening a PR.

## Optimize

Suggest fixes and show potential savings.

```bash
deburger optimize .
deburger optimize . --auto-apply
```

Use when you want suggested fixes for expensive patterns.

## Blame

Attribute cost impact to commits and authors.

```bash
deburger blame . --top 5
```

Use for ownership reviews or to find where costs were introduced.

## Hook

Install or manage git hooks for automatic scans.

```bash
deburger hook install
deburger hook status
deburger hook uninstall
```

Use when you want checks to run on commit or push.

## PR comment

Post cost impact to a GitHub PR.

```bash
deburger pr-comment --repo owner/name --pr 42
```

Use in CI to give reviewers a cost summary.

## Version

Show the installed version.

```bash
deburger --version
deburger version
```

Use when reporting issues or verifying a release.

## Config reference

`deburger init` creates `.deburger.yml`. Typical fields include provider, region, budgets, and traffic estimates.
