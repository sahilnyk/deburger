# deburger user manual

This manual explains how to run deburger, tune its estimates, use it in automation, and understand its limits.

## Start a project

Install deburger and create a configuration file:

```bash
python -m pip install deburger
cd your-project
deburger init --provider aws
```

Supported providers are `aws`, `gcp`, and `azure`. The command will not overwrite an existing `.deburger.yml` file.

Open the generated file and replace the sample traffic values with values that resemble your application. These values directly affect every estimate.

## Scan source code

```bash
# Scan files changed in Git
deburger check .

# Scan every supported file under src
deburger check src --full

# Include formulas and suggestions
deburger check src --full --verbose
```

Incremental scanning includes staged, unstaged, and untracked files. If Git is unavailable, deburger falls back to a full scan.

A successful scan with no findings exits with status 0. A scan with findings exits with status 1. This makes the command suitable for CI, but it also means a finding is not the same thing as a command failure. Read the JSON summary when your automation needs to distinguish results.

## Use JSON output

```bash
deburger check . --full --json > deburger-report.json
```

The report contains `issues`, `summary`, and `warnings`. Progress output is disabled in JSON mode. Files that cannot be decoded or read appear in `warnings` instead of being silently ignored.

## Configure estimates

The generated configuration contains these sections:

```yaml
provider: aws
region: us-east-1
traffic:
  requests_per_day: 100000
  avg_duration_ms: 1000
  avg_memory_mb: 1024
  db_queries_per_request: 10
  concurrent_connections: 100
  data_transfer_gb: 100
performance:
  max_workers: 32
  incremental: true
hooks:
  fail_on_critical: true
  max_monthly_cost: 500
```

Positive traffic and worker values must be integers greater than zero. Invalid provider names and invalid value types stop the command with a useful error.

You can override common settings in CI:

```bash
export DEBURGER_PROVIDER=aws
export DEBURGER_REGION=us-east-1
export DEBURGER_REQUESTS_PER_DAY=250000
export DEBURGER_MAX_WORKERS=8
```

## Read a finding

Each finding includes:

- A stable rule type
- File and line number
- Severity
- Estimated monthly cost
- Estimated savings
- An explanation and possible fix

The dollar amount is a planning estimate. It is based on bundled prices and configured traffic, plus rule assumptions such as loop size. Confirm important estimates with production measurements and current provider pricing.

## Suppress a false positive

Place `deburger:ignore` on the finding line or directly above it:

```python
# deburger:ignore: lookup uses a request-local cache
for item in items:
    result = db.query(item.id)
```

Include a short reason. It helps the next reviewer understand why the warning is safe to ignore.

## Preview and apply fixes

```bash
deburger optimize .
deburger optimize . --apply
deburger optimize . --auto-apply
```

The default is a preview. `--apply` writes reviewed suggestions. `--auto-apply` applies only changes marked safe. At present, async concurrency rewrites require manual review because call order and side effects cannot be inferred reliably.

Before each file is changed, deburger creates `<filename>.deburger-backup`. Changes to one file are applied sequentially and written with an atomic replacement. Always run your normal formatter and test suite afterward.

## Compare Git revisions

Both forms below are supported:

```bash
deburger diff main HEAD
deburger diff main..feature
```

deburger reads both revisions from Git and reports findings present in the target revision but not the base revision. Deleted files and unchanged findings are not reported as new problems.

## Install the Git hook

```bash
deburger hook --install
deburger hook --uninstall
```

The hook follows `hooks.fail_on_critical` and `hooks.max_monthly_cost`. Installation respects Git's configured hooks directory and keeps unrelated hook content. Uninstallation removes only the marked deburger block.

## Comment on a pull request

```bash
deburger pr-comment 42 --base main
```

This command requires the GitHub CLI, an authenticated GitHub account, and network access. Review the generated comment shown in the terminal if publishing fails.

## Supported files

- Python: `.py`, analyzed with the Python syntax tree
- JavaScript: `.js` and `.jsx`, analyzed with pattern matching
- TypeScript: `.ts` and `.tsx`, analyzed with pattern matching

Pattern matching can miss complex nesting and can report false positives in unusual syntax. Treat JavaScript and TypeScript results as review prompts, not proof of a defect.

## Troubleshooting

### No files were scanned

Run with `--full`. The default mode scans only Git changes. Also check the `ignore` configuration and confirm that the path exists.

### A source file was skipped

Run without `--json` to see warnings on standard error, or inspect the JSON `warnings` array. Files must be readable as UTF-8 source code.

### Estimates look too high

Check `requests_per_day`, memory, duration, and query counts in `.deburger.yml`. The generated values are examples, not measurements of your application.

### Terminal output is hard to read

Rich output adapts to the terminal width. Set the standard `NO_COLOR` environment variable when your terminal or log viewer should not receive color codes.

## Privacy

Normal scans are local and do not require credentials or network access. Source code is not uploaded and telemetry is not collected. Commands that explicitly publish through the GitHub CLI are the only networked workflow.
