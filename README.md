# 🍔 deburger

catch bugs before they catch you

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/deburger.svg)](https://pypi.org/project/deburger/)

## what's this?

AI writes code fast, but you lose track:
- did it actually fix the thing?
- did it sneak in vulnerabilities?  
- how close are you to done? 60%? 95%?

**deburger** gives you answers by analyzing commits, tracking progress, catching security issues across **multiple languages**, and keeping clean logs.

## Installation

```bash
pip install deburger
```

With LLM support (for AI guidance features):
```bash
pip install deburger[llm]
```

## quick start

```bash
# 1. set up in your project
deburger init "build a REST API"

# 2. code with AI (ChatGPT, Claude, whatever)

# 3. commit
git add . && git commit -m "added user endpoints"

# 4. check what happened
deburger analyze

# what you'll see:
# Files: 3 | +156 -12
# Progress: 67%
# Security: 2 issues
# Quality: 87/100
```

## commands

| command | what it does | example |
|---------|--------------|---------|
| `deburger init` | set things up | `deburger init "build REST API"` |
| `deburger analyze` | check your changes | `deburger analyze --since HEAD~5` |
| `deburger scan` | find security issues | `deburger scan --severity high` |
| `deburger guide` | get AI suggestions | `deburger guide -o prompt.txt` |
| `deburger report` | see the metrics | `deburger report --format json` |
| `deburger logs` | check the logs | `deburger logs -n 100` |
| `deburger config` | tweak settings | `deburger config --show` |

## features

### progress tracking
- break goals into smaller pieces
- see completion % per commit
- get told what to work on next

### security scanning (multi-language)
catches issues in:
- **python** – eval(), exec(), pickle, hardcoded secrets
- **javascript/typescript** – eval(), innerHTML, XSS
- **go** – command injection, hardcoded stuff
- **java** – Runtime.exec(), secrets
- **ruby** – eval(), system() injection
- **php** – eval(), SQL injection
- **sql** – hardcoded passwords

includes CWE IDs for proper vulnerability classification

### code quality
- complexity scoring
- maintainability index  
- quality score (0-100)
- line count tracking

### AI helpers
- generates prompts for your AI
- keeps guardrails in place
- works with OpenAI and Anthropic

### logging
- auto log rotation (10MB chunks)
- JSON logs for easy parsing
- tracks everything you do

## Configuration

Initialize creates `.deburger.yml`:

```yaml
requirement: "Build REST API with authentication"

sub_goals:
  - id: endpoints
    description: "Create CRUD endpoints"
    weight: 40
    keywords: ["endpoint", "route", "api"]
    
  - id: auth
    description: "Implement JWT authentication"
    weight: 30
    keywords: ["auth", "jwt", "token"]
    
  - id: validation
    description: "Add input validation"
    weight: 20
    keywords: ["validate", "sanitize", "check"]
    
  - id: tests
    description: "Write comprehensive tests"
    weight: 10
    keywords: ["test", "spec", "assert"]

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
  fail_on_critical: true
  ignore_patterns:
    - tests/
    - docs/

metrics:
  min_quality_score: 70
  max_complexity: 10
  min_test_coverage: 80
```

## CLI Examples

### Initialize Project
```bash
# Simple init
deburger init "Build e-commerce platform"

# Interactive init with wizard
deburger init --interactive
```

### Analyze Changes
```bash
# Analyze last commit
deburger analyze

# Analyze last 5 commits
deburger analyze --since HEAD~5

# Verbose output
deburger analyze --verbose
```

### Security Scanning
```bash
# Scan current directory (all languages)
deburger scan

# Scan specific directory
deburger scan src/

# Show only high severity issues
deburger scan --severity high

# Scan specific file
deburger scan app.py
```

### View Logs
```bash
# Show last 50 log entries
deburger logs

# Show last 200 entries
deburger logs -n 200

# Follow logs in real-time
deburger logs --follow

# Clear all logs
deburger logs --clear
```

### Configuration Management
```bash
# Show current config
deburger config --show

# Validate config
deburger config --validate

# Edit config in editor
deburger config --edit
```

## Sample Output

### Analyze Command
```
🍔 Analyzing code changes...

Files: 3 | +156 -12

┌─ 📊 Requirement Progress ─────────────┐
│ Build REST API with authentication    │
│ Progress: 67%                          │
└────────────────────────────────────────┘

Sub-Goals
┌────────────────────┬──────────┬────────┐
│ Goal               │ Progress │ Status │
├────────────────────┼──────────┼────────┤
│ CRUD endpoints     │ 85%      │   ✓    │
│ JWT authentication │ 78%      │   ↑    │
│ Input validation   │ 45%      │   ⚠    │
│ Tests              │ 92%      │   ✓    │
└────────────────────┴──────────┴────────┘

📈 Quality: 87/100

→ Next Focus: Add input validation for query parameters
```

### Security Scan
```
🔒 Running security scan...

┌─ Scan Summary ───────────────┐
│ Scanned: src/                │
│ Issues Found: 3              │
│ Files Affected: 2            │
│ Languages: python, javascript│
└──────────────────────────────┘

CRITICAL (1)
────────────────────────────────────────────
  File          Line  Issue                    Language
  api.py        45    Hardcoded secret         python

HIGH (2)
────────────────────────────────────────────
  File          Line  Issue                    Language
  auth.py       12    Use of eval()            python
  app.js        78    innerHTML XSS risk       javascript

Example Issues:

1. Hardcoded secret detected
   src/api.py:45
   password = "super_secret_123"
   Fix: Use environment variables or secure vault
   CWE: CWE-798
```

## Use Cases

| Use Case | Description |
|----------|-------------|
| **Monitor AI Code** | Track quality as AI writes code |
| **Requirement Alignment** | Ensure code matches actual goals |
| **Security Gate** | Block merges with critical vulnerabilities |
| **Progress Tracking** | Quantify completion (0-100%) |
| **Multi-Language Projects** | Scan Python, JS, Go, Java, Ruby, PHP |
| **CI/CD Integration** | Add as quality gate in pipelines |

## Architecture

```
deburger/
├── cli/              Command-line interface
├── analyzer/         Code change analysis
├── security/         Multi-language vulnerability detection
├── metrics/          Code quality metrics
├── requirements/     Progress tracking
├── guidance/         AI steering
├── utils/            Config, logging, helpers
└── ui/               Rich terminal output
```

## Logs Location

Logs are stored in `~/.deburger/logs/`:
- `deburger.log` – Human-readable logs (rotated at 10MB)
- `deburger.jsonl` – Structured JSON logs for parsing

## Development

```bash
# Clone repository
git clone https://github.com/sahilnyk/deburger.git
cd deburger

# Install in development mode
pip install -e ".[dev,llm]"

# Run tests
pytest

# Lint
ruff check src/

# Format
black src/

# Type check
mypy src/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - See [LICENSE](LICENSE)

## Author

**Sahil Nayak**

- GitHub: [@sahilnyk](https://github.com/sahilnyk)
- Email: sahilnayak2056@gmail.com

---

**Why deburger?** AI generates code fast, but someone needs to check its work. deburger is that someone.

Built with ❤️ for developers working with AI coding assistants.
