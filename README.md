# 🍔 deburger

**AI Code Quality Guardian** - Monitor AI-generated code, track requirements, catch vulnerabilities.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## What is deburger?

When AI generates code, you get changes fast but lose visibility. Did it solve your problem? Introduce XSS? Are you 60% done or 95%?

deburger answers these questions. It analyzes each commit, tracks requirement progress (0-100%), detects vulnerabilities, and guides AI back on track when it drifts.

## Installation

```bash
pip install deburger
```

From source:
```bash
git clone https://github.com/sahilnyk/deburger.git
cd deburger
pip install -e .
```

With LLM support:
```bash
pip install deburger[llm]
```

## Quick Start

```bash
# Initialize
🍔 deburger init --requirement "Build REST API with JWT auth"

# Make changes with AI (ChatGPT, Claude, etc.)

# Analyze
🍔 deburger analyze

# Output:
# ✓ Progress: 67% → 82% (+15%)
# ⚠ Security: 2 issues (SQL injection, hardcoded secret)
# ✓ Tests: 12 generated
# ✓ Quality: 87/100
```

## Commands

| Command | Description |
|---------|-------------|
| `deburger init` | Initialize project configuration |
| `deburger analyze` | Analyze recent code changes |
| `deburger security` | Run security vulnerability scan |
| `deburger guide` | Get AI guidance for next steps |
| `deburger report` | Generate metrics report |
| `deburger config` | Configure settings |

## Features

**Requirement Tracking**
- Break down goals into measurable sub-goals
- Track completion percentage per commit
- Evidence-based progress scoring
- Next focus suggestions

**Security Scanning**
- SQL injection detection
- XSS vulnerability scanning
- Hardcoded credentials finder
- Command injection patterns
- Unsafe deserialization checks

**Quality Metrics**
- Cyclomatic complexity
- Maintainability index
- Code quality score (0-100)
- Lines of code tracking

**AI Steering**
- Generate actionable guidance prompts
- Enforce guardrails (no jailbreak)
- Focus area determination
- LLM-ready prompt formatting

**Test Generation**
- Automatic unit test creation
- Edge case test generation
- Integration test scaffolding

## Usage Example

```python
# Monitor functions with decorators
from deburger.decorators import deburger, security_check

@deburger(requirement="Handle authentication", security=True)
@security_check(fail_on_issues=True)
def authenticate_user(username: str, password: str):
    # Function is monitored automatically
    return jwt.encode({"user": username}, secret)
```

## Configuration

Create `.deburger.yml`:

```yaml
requirement: "Build REST API with authentication"

sub_goals:
  - id: endpoints
    description: "Create CRUD endpoints"
    weight: 40
  - id: auth
    description: "Implement JWT authentication"
    weight: 30
  - id: validation
    description: "Add input validation"
    weight: 20
  - id: tests
    description: "Write tests"
    weight: 10

llm:
  provider: openai
  api_key: ${OPENAI_API_KEY}
  model: gpt-4
  
  guardrails:
    - "Never disable security features"
    - "Always validate user input"
    - "No hardcoded credentials"

security:
  enabled: true
  fail_on_high: true

metrics:
  min_quality_score: 70
  max_complexity: 10
```

## CLI Output Example

```
🍔 deburger analyze

Files: 3 | +456 -12

┌─ 📊 Requirement Progress ─────┐
│ Build REST API with JWT auth  │
│ ████████████░░░░░░░░ 67%      │
└────────────────────────────────┘

Sub-Goals Progress
┌────────────────────┬──────────┬────────┐
│ Goal               │ Progress │ Status │
├────────────────────┼──────────┼────────┤
│ CRUD endpoints     │ 85%      │   ✓    │
│ JWT auth           │ 78%      │   ↑    │
│ Input validation   │ 45%      │   ⚠    │
│ Tests              │ 92%      │   ✓    │
└────────────────────┴──────────┴────────┘

🔒 Security (2 issues)
├─ HIGH: SQL injection in user_query() (line 45)
│  → Use parameterized queries
└─ HIGH: Hardcoded API key (line 12)
   → Move to environment variables

📈 Code Quality: 87/100

🤖 Next Focus: Add input validation for query parameters
```

## Use Cases

**Monitor AI Code Generation**
Track quality as AI writes code in real-time

**Requirement Alignment**
Ensure code matches actual goals, not what AI thinks

**Security Gate**
Block merges with critical vulnerabilities

**Progress Tracking**
Quantify completion instead of guessing

**AI Guidance**
Steer LLM back on track when it drifts

## Architecture

```
deburger/
├── analyzer/       Code change analysis
├── security/       Vulnerability detection
├── metrics/        Quality calculation
├── requirements/   Progress tracking
├── guidance/       AI steering
├── testing/        Test generation
├── llm/           LLM integration
├── decorators/     Function monitoring
└── ui/            Beautiful CLI output
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Format
black src/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT - See [LICENSE](LICENSE)

## Author

**Sahil Nayak**

GitHub: [@sahilnyk](https://github.com/sahilnyk)  
Email: sahilnayak2056@gmail.com

Built because AI generates code fast, but someone needs to check its work.
