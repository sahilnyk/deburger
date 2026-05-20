# 🍔 deburger

catch bugs before they catch you

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/deburger.svg)](https://pypi.org/project/deburger/)

## what's this?

AI writes code fast but you lose track. did it fix the thing? did it add vulnerabilities? how close are you to done?

deburger tracks your progress, scans for security issues across multiple languages, and keeps logs.

## install

```bash
pip install deburger
```

## quick start

```bash
deburger init "build a REST API"
# code with AI
git commit -m "added stuff"
deburger analyze
deburger scan
```

## commands

```bash
deburger init "your goal"          # setup
deburger analyze                    # check changes
deburger scan                       # find security issues
deburger logs                       # view logs
deburger config --show              # see config
```

## what it does

**tracks progress**
- breaks goals into pieces
- shows completion %
- tells you what to work on next

**scans security** (python, javascript, go, java, ruby, php, sql)
- catches eval(), hardcoded secrets, SQL injection, XSS
- shows CWE IDs and fixes

**measures quality**
- complexity score
- quality score 0-100
- tracks lines changed

**keeps logs**
- auto-rotating logs in ~/.deburger/logs/
- tracks everything

## example output

```
scanning for security issues...

Issues Found: 3
Files: 2
Languages: python, javascript

CRITICAL (1)
  api.py:45    Hardcoded secret

HIGH (2)
  auth.py:12   Use of eval()
  app.js:78    innerHTML XSS risk

yikes! 3 critical issues - fix these asap
```

## config

edit `.deburger.yml` to customize goals, security patterns, and thresholds

## logs

```bash
deburger logs              # last 50 lines
deburger logs -n 200       # last 200 lines
deburger logs --follow     # live tail
```

## why tho

AI generates code fast but doesn't check its work. deburger does.

## links

- repo: github.com/sahilnyk/deburger
- pypi: pypi.org/project/deburger

built by sahil nayak
