# deburger

deburger scans source code for patterns that can increase cloud costs. It points to the relevant line, explains the concern, and estimates the possible monthly impact using traffic values from your project configuration.

[![PyPI version](https://img.shields.io/pypi/v/deburger.svg)](https://pypi.org/project/deburger/)
[![Python versions](https://img.shields.io/pypi/pyversions/deburger.svg)](https://pypi.org/project/deburger/)
[![License](https://img.shields.io/pypi/l/deburger.svg)](https://pypi.org/project/deburger/)

## Install

deburger supports Python 3.9 and newer.

```bash
python -m pip install deburger
```

Create a configuration file and run your first scan:

```bash
deburger init --provider aws
deburger check . --full
```

The first command creates `.deburger.yml`. Review its traffic values before relying on the cost estimates. A project handling one million requests per day should not use the same assumptions as a small internal service.

## What it finds

deburger currently checks for:

- Database queries inside loops
- Sequential async operations that might run concurrently
- Storage requests inside loops
- Queries without a limit or pagination
- Connections created inside request handlers
- Heavy imports in serverless handlers
- High-volume logging patterns
- Queries that may cause full table scans

Python analysis uses the standard Python syntax tree. JavaScript and TypeScript analysis is pattern based, so complex or generated code may need manual review.

## Main commands

```bash
# Scan files changed in Git
deburger check .

# Scan every supported file
deburger check . --full

# Show formulas and suggested changes
deburger check . --full --verbose

# Produce JSON for CI
deburger check . --full --json

# Preview possible code changes
deburger optimize .

# Apply reviewed changes
deburger optimize . --apply

# Compare two Git revisions
deburger diff main HEAD
deburger diff main..feature
```

`check` exits with status 1 when it finds an issue and status 0 when it does not. Invalid configuration, missing paths, and other command failures also return a nonzero status with an explanation on standard error.

## Cost estimates

Cost values are estimates, not cloud invoices. They depend on:

- Traffic values in `.deburger.yml`
- Bundled provider pricing data
- Rule-specific assumptions such as loop size and request volume
- The source patterns that static analysis can see

Use the estimates to prioritize investigation. Confirm material savings with production metrics and your provider's current pricing before making financial decisions.

## Safe optimization

`deburger optimize` is a preview by default. `--apply` writes changes and creates a `.deburger-backup` file before modifying each source file.

Generated changes still require review and tests. In particular, sequential async operations can depend on one another even when they look independent. deburger does not apply those changes automatically.

## Git and CI

Install the optional pre-commit check with:

```bash
deburger hook --install
```

The hook follows the thresholds in `.deburger.yml`. Remove only the deburger section with:

```bash
deburger hook --uninstall
```

For CI, use JSON output and preserve the command's exit status:

```bash
deburger check . --full --json > deburger-report.json
```

## Privacy

Scanning, analysis, and cost calculation run locally. deburger does not send source code, collect telemetry, or require cloud credentials. The `pr-comment` command is the exception: it calls the authenticated GitHub CLI to publish the generated comment.

## More help

See the [user manual](docs/user-manual.md) for configuration, suppression, exit codes, troubleshooting, and command details.

Issues and feature requests are welcome in the [GitHub issue tracker](https://github.com/sahilnyk/deburger/issues).
