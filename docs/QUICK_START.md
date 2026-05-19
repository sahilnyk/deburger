# 🍔 Quick Start Guide

## Installation

```bash
pip install deburger
```

## Basic Usage

### 1. Initialize

```bash
cd your-project/
deburger init --requirement "Build REST API"
```

### 2. Make Changes

Use AI to generate code (ChatGPT, Claude, etc.)

### 3. Analyze

```bash
git add src/
git commit -m "added: user authentication"
deburger analyze
```

## Commands

```bash
deburger init           # Setup project
deburger analyze        # Analyze changes
deburger security       # Security scan
deburger guide          # AI guidance
```

## Configuration

Edit `.deburger.yml`:

```yaml
requirement: "Build REST API"

sub_goals:
  - id: api
    description: "Create endpoints"
    weight: 50
  - id: auth
    description: "Add authentication"
    weight: 50

llm:
  provider: openai
  api_key: ${OPENAI_API_KEY}
```

## Example Output

```
🍔 deburger analyze

Progress: 67% → 82% (+15%)
Security: 2 issues found
Quality: 87/100

Next Focus: Add input validation
```

## With Decorators

```python
from deburger.decorators import deburger

@deburger(requirement="Auth", security=True)
def login(username, password):
    return authenticate(username, password)
```

## Next Steps

- Run `deburger analyze` after each commit
- Fix security issues before merging
- Track progress to 100%
- Use AI guidance to stay on track
