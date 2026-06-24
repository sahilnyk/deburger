# deburger user manual

you wrote code. it works. but your cloud bill is $8k and growing.
deburger looks at your code and tells you *which lines* are burning money — and by how much.

it does NOT need api keys, cloud credentials, or internet. just your code.

---

## commands

### `deburger init`

creates a `.deburger.yml` so deburger knows your setup.

```bash
deburger init --provider aws
```

this writes a config file with sensible defaults. you edit it later to match your actual traffic (requests/day, memory, etc).

use this once per project.

---

### `deburger check`

this is the main one. scans your code and dumps out what's costing you.

```bash
deburger check .
deburger check src/ --full
deburger check . -v
```

by default it only scans git-changed files (fast). `--full` scans everything.

the output shows:
- file + line number
- what pattern it found (n+1 query, s3 in loop, etc)
- severity (critical = fix now, low = meh)
- estimated monthly waste in dollars
- how much you'd save if you fix it

add `-v` and it breaks down the math — what formula it used, what pricing it assumed, so you know the number isn't pulled out of thin air.

```bash
# ci/cd friendly
deburger check . --json
```

exits with code 1 if issues found. pipe to jq or whatever.

---

### `deburger optimize`

tries to auto-fix the expensive patterns it found.

```bash
deburger optimize .
deburger optimize . --apply       # actually write the fixes
deburger optimize . --auto-apply  # only apply safe ones
```

it shows you what it wants to change and how confident it is. by default it's dry-run — add `--apply` to actually rewrite files.

backups are created as `.deburger-backup` before any write.

---

### `deburger diff`

compares two git branches and tells you what new expensive code you're adding.

```bash
deburger diff main..feature
deburger diff v1.0..v2.0
```

useful in ci/cd or before merging a pr. shows only the cost *delta* — what changed, not everything.

---

### `deburger blame`

git blame + cost analysis = who's costing the company money.

```bash
deburger blame .
deburger blame src/ --top 3
```

groups issues by author, sorted by total monthly cost. great for team dashboards or friday afternoon banter.

---

### `deburger hook`

installs a git pre-commit hook that runs deburger before every commit.

```bash
deburger hook --install
deburger hook --uninstall
```

if it finds critical-cost code, the commit is blocked. use `git commit --no-verify` to skip.

---

### `deburger pr-comment`

posts a cost-breakdown comment on a github pr.

```bash
deburger pr-comment 42
```

requires the `gh` cli to be installed and authenticated.

---

### `deburger version`

```bash
deburger version
deburger --version
```

prints `deburger v1.0.1` or whatever.

---

## config (`.deburger.yml`)

you probably want to tweak the traffic numbers so cost estimates match your actual usage:

```yaml
provider: aws
region: us-east-1
traffic:
  requests_per_day: 100000     # how many requests your app handles
  avg_duration_ms: 1000        # average function duration
  avg_memory_mb: 1024          # average memory per function
  db_queries_per_request: 10   # queries per request on average
```

these numbers directly affect the dollar amounts deburger shows. if you have 1M req/day instead of 100k, your costs are 10x higher.

---

## suppressing false positives

put `deburger:ignore` on the line above or same line:

```python
# deburger:ignore
for item in items:
    result = db.query(item.id)  # this is fine, it's cached
```

deburger skips those lines.

---

## what each pattern means

| pattern | what it looks for | why it costs |
|---------|------------------|--------------|
| n+1 query | db query inside a for loop | each iteration = one db call. 500 items = 500 queries instead of 1. |
| sequential async | `await` calls one after another | each waits for previous to finish. parallel = faster = less compute time. |
| s3 in loop | s3 get/put inside a loop | 100 s3 api calls instead of 1 batch. s3 charges per request. |
| unbounded query | `.all()` or `SELECT *` without limit | returns entire table. as data grows, this gets slower and more expensive. |
| missing pool | new db connection per request | opening a connection takes ~50ms. with a pool you reuse them. |
| cold start | heavy imports at top level of lambda | pandas, torch, etc add 500ms-2s to cold starts. lazy import = faster. |
| expensive logging | logging inside loops | cloudwatch charges by volume. logging 100k times = real money. |
| unindexed query | filter on columns without indexes | full table scan on every request. indexes = cheap scans. |

---

## supported languages

- **python** — ast-based. walks the syntax tree, knows exactly what's a loop, what's a db call.
- **typescript** (`.ts`, `.tsx`) — regex-based line scanner. catches the same patterns as python but won't handle deeply nested or dynamic code.

---

## privacy

deburger never sends your code anywhere. no telemetry, no api calls, no "call home". pricing data is hardcoded for each cloud provider.
