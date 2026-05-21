# 🍔 deburger

**your cloud bill is getting fat. time to slim it down.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/deburger.svg)](https://pypi.org/project/deburger/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![AWS](https://img.shields.io/badge/AWS-supported-FF9900?logo=amazon-aws)](https://aws.amazon.com/)
[![GCP](https://img.shields.io/badge/GCP-supported-4285F4?logo=google-cloud)](https://cloud.google.com/)
[![Azure](https://img.shields.io/badge/Azure-supported-0078D4?logo=microsoft-azure)](https://azure.microsoft.com/)

catch expensive code **before** it hits production. analyze your commits and predict cloud costs in real-time.

---

## the problem

your developer commits code. looks fine. passes tests. deploys.

**3 days later:** AWS bill goes from $8K to $47K 💀

**the issue?** one API endpoint doing 500 database queries per request.

**cost to fix:** 10 minutes  
**damage done:** $39,000

this happens. every. single. month.

---

## the solution

```bash
git commit -m "added dashboard"

🍔 deburger analyzing...

⚠️  COST ALERT
This code will cost $12,400/month (+155%)

Issue: N+1 database queries
File: api/dashboard.py:42

Current: $8,000/month
After deploy: $20,400/month

Fix available (saves $12,160/month):
[Apply Fix] [Ignore] [Cancel]
```

**boom.** caught before production. crisis averted.

---

## what it does

✓ analyzes code on every commit  
✓ predicts cloud costs (AWS, GCP, Azure)  
✓ detects N+1 queries, over-provisioned lambdas, etc.  
✓ one-click fixes with savings calculator  
✓ blocks expensive deployments automatically  

**supports:**
- **clouds:** AWS, GCP, Azure
- **languages:** Python, JavaScript, TypeScript, Go
- **resources:** Lambda, RDS, DynamoDB, Cloud Functions, BigQuery, containers

---

## install

```bash
pip install deburger
```

---

## quick start

```bash
# setup in your project
cd your-project/
deburger init

# configure cloud provider
export AWS_PROFILE=default
# or
export GOOGLE_APPLICATION_CREDENTIALS=key.json
# or  
export AZURE_SUBSCRIPTION_ID=xxx

# done! now every commit is checked
git add .
git commit -m "new feature"
# deburger auto-runs and shows cost impact
```

---

## commands

```bash
deburger check              # analyze current code
deburger diff main..dev     # compare branches
deburger optimize           # auto-fix expensive code
deburger watch              # continuous monitoring
deburger report             # cost breakdown
deburger leaderboard        # team savings stats
```

---

## how it works

**1. code analysis**
```python
# deburger detects this:
for user in users:  # 500 users
    profile = db.get(user.id)  # 500 queries! 💸
```

**2. cost prediction**
```
500 queries × 50K requests/day = 25M queries/month
RDS cost: $8,200/month
```

**3. optimization**
```python
# deburger suggests:
profiles = db.query(Profile).filter(id.in_(user_ids))
# 1 query instead of 500
# new cost: $16/month
# savings: $8,184/month 🎉
```

---

## config

create `.deburger.yml`:

```yaml
providers:
  aws:
    enabled: true
    region: us-east-1
  gcp:
    enabled: false
  azure:
    enabled: false

budget:
  monthly_limit: 10000
  block_threshold: 1.0

traffic:
  requests_per_day: 100000
```

---

## examples

**caught before production:**
- N+1 queries → saved $8K/month
- over-provisioned lambda (1024MB → 256MB) → saved $3K/month
- missing pagination → saved $5K/month in data transfer
- sequential API calls → saved $2K/month

**real savings:** $18K/month = $216K/year

**deburger cost:** free (open source)

**ROI:** infinite 🚀

---

## features

| feature | status |
|---------|--------|
| AWS support | ✓ |
| GCP support | ✓ |
| Azure support | ✓ |
| Python analysis | ✓ |
| JavaScript/TS | ✓ |
| Go analysis | ✓ |
| auto-fix | ✓ |
| git hooks | ✓ |
| CI/CD integration | ✓ |
| team leaderboard | ✓ |
| cost tracking | ✓ |

---

## why deburger

**other tools:**
- show you costs AFTER you spent money 💸
- generic recommendations
- no code analysis
- reactive, not proactive

**deburger:**
- catches expensive code BEFORE production ⚡
- shows exact savings per fix
- auto-generates optimized code
- blocks deploys that exceed budget
- actually saves you money

---

## use cases

**startups:** avoid burning cash on cloud waste  
**scale-ups:** control costs as you grow  
**enterprises:** prevent $100K+ incidents  
**developers:** become the hero who saved $500K  

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
