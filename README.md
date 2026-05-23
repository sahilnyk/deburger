# deburger

Catch expensive code before it ships by scanning your repo and estimating cloud costs.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/deburger.svg)](https://pypi.org/project/deburger/)
[![AWS](https://img.shields.io/badge/AWS-supported-FF9900?logo=amazon-aws)](https://aws.amazon.com/)
[![GCP](https://img.shields.io/badge/GCP-supported-4285F4?logo=google-cloud)](https://cloud.google.com/)
[![Azure](https://img.shields.io/badge/Azure-supported-0078D4?logo=microsoft-azure)](https://azure.microsoft.com/)
[![Cost savings](https://img.shields.io/badge/cost%20savings-focus-brightgreen)](https://pypi.org/project/deburger/)

## Install

```bash
pip install deburger
```

## Quick start

```bash
cd your-project/
deburger init --provider aws
deburger check .
```

## Commands

```bash
deburger init       # create .deburger.yml
deburger check      # scan code and estimate costs
deburger diff       # compare two git refs
deburger optimize   # suggest or apply fixes
deburger blame      # attribute cost to commits/authors
deburger hook       # install or manage git hooks
deburger pr-comment # post PR comment with cost impact
deburger version    # show version
```

## Config

`deburger init` creates `.deburger.yml`. Edit it to set providers, budgets, and traffic assumptions.

## Docs

Command examples and use cases are in [docs/QUICK_START.md](docs/QUICK_START.md).

---

## contributing

found a bug? want to add a feature? PRs welcome!

```bash
git clone https://github.com/sahilnyk/deburger
cd deburger
pip install -e ".[dev]"
pytest
```

---

## license

MIT - go wild 🍔

---

## links

**repo:** github.com/sahilnyk/deburger  
**pypi:** pypi.org/project/deburger  
**issues:** github.com/sahilnyk/deburger/issues  

---

## tagline

**your cloud bill is bloated. deburger slims it down.**

built by [@sahilnyk](https://github.com/sahilnyk)

*stop deploying expensive code. start saving money.* 💰
