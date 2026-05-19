# 🍔 deburger

**AI Code Quality Guardian** - Monitor how AI changes your code, track requirement alignment, and catch vulnerabilities.

## What is deburger?

When you use AI to generate code, you get changes fast but lose visibility into quality, security, and requirement alignment. deburger solves this.

It analyzes each AI-generated change, runs comprehensive tests, checks security vulnerabilities, measures requirement adherence, and guides the AI back on track when it drifts.

Think of it as a production-grade quality gate for AI-assisted development.

## Why this exists

AI generates code fast. Too fast. You paste a prompt, get 200 lines back, and hope it's correct.

But did it actually solve your problem? Did it introduce XSS? Is it 60% toward the requirement or 95%? You don't know until something breaks.

deburger gives you metrics, security analysis, and requirement tracking in real-time. No more blind trust.

## Core Features

| Feature | Description |
|---------|-------------|
| **Requirement Tracking** | Measures how each AI change moves toward your actual goal (0-100% completion) |
| **Security Analysis** | Detects OWASP Top 10 vulnerabilities, hardcoded secrets, unsafe patterns |
| **Test Generation** | Creates unit, integration, and edge-case tests automatically |
| **Metrics Dashboard** | Code quality score, complexity, coverage, performance benchmarks |
| **AI Guidance** | Provides guardrails and prompts to steer AI back on track |
| **Zero Dependencies** | Pure Python stdlib where possible, minimal external deps |
| **LLM Agnostic** | Works with any LLM via API (OpenAI, Anthropic, Ollama, etc.) |

## How it works

```bash
# 1. Define your requirement
deburger init --requirement "Build REST API with auth"

# 2. Let AI generate code (use any tool/LLM)

# 3. Run deburger to analyze changes
deburger analyze --since HEAD~3

# Output:
# ✓ Requirement Progress: 67% → 82% (+15%)
# ⚠ Security Issues: 2 found (SQL injection, hardcoded secret)
# ✓ Tests Generated: 12 unit, 3 integration
# ✓ Code Quality: 87/100 (+5)
# → AI Guidance: Focus on input validation next
```

## Installation

```bash
pip install deburger
```

Or from source:
```bash
git clone https://github.com/sahilnyk/deburger.git
cd deburger
poetry install
deburger --version
```

## Quick Start

```bash
# Initialize project
deburger init

# Analyze recent changes
deburger analyze

# Run with custom prompts/guardrails
deburger analyze --config .deburger.yml

# Generate report
deburger report --format html
```

## Security Features

- SQL injection detection
- XSS vulnerability scanning
- Hardcoded credentials finder
- Unsafe deserialization checks
- Path traversal detection
- Command injection patterns
- Insecure random usage
- No jailbreak attempts (guardrails enforced)

## Requirement Tracking

deburger breaks down your high-level requirement into measurable sub-goals:

```yaml
# .deburger.yml
requirement: "Build REST API with JWT auth"

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
    description: "Write comprehensive tests"
    weight: 10
```

Each commit is scored against these goals to show real progress.

## LLM Integration

Configure your LLM provider:

```yaml
# .deburger.yml
llm:
  provider: openai
  api_key: ${OPENAI_API_KEY}
  model: gpt-4
  
  guardrails:
    - "Never disable security features"
    - "Always validate user input"
    - "Prefer explicit over implicit"
  
  prompts:
    guidance: |
      You are {progress}% toward the goal.
      Next focus: {next_focus}
      Security issues: {security_count}
```

## Commands

```bash
deburger init                    # Initialize project config
deburger analyze                 # Analyze recent changes
deburger analyze --since HASH    # Analyze from specific commit
deburger test                    # Generate and run tests
deburger security                # Run security scan
deburger report                  # Generate metrics report
deburger guide                   # Get AI guidance
deburger config                  # Configure settings
```

## Example Output

```
🍔 deburger analysis

Requirement: Build REST API with JWT auth
Progress: 67% → 82% (+15%)

Changes analyzed: 3 commits, 456 lines
├─ endpoints: 85% complete ✓
├─ auth: 78% complete ↑
├─ validation: 45% complete ⚠
└─ tests: 92% complete ✓

Security Issues (2):
├─ HIGH: SQL injection in user_query() (api.py:45)
└─ MED: Hardcoded API key (config.py:12)

Tests Generated: 12 unit, 3 integration
Code Quality: 87/100 (+5 from last run)

AI Guidance:
→ Focus on input validation for query parameters
→ Move API keys to environment variables
→ Add rate limiting to prevent abuse

Next Steps:
1. Fix security issues (deburger fix)
2. Run generated tests (pytest tests/)
3. Continue with validation logic
```

## Architecture

```
deburger/
├── analyzer/          # Code change analysis
├── requirements/      # Requirement tracking
├── security/          # Security scanners
├── testing/           # Test generation
├── metrics/           # Quality metrics
├── guidance/          # AI steering logic
└── llm/              # LLM integration
```

## Design Principles

- **Zero trust AI** - Verify every change
- **Metrics over feelings** - Quantify everything
- **Security first** - Scan before merge
- **Minimal deps** - Use stdlib when possible
- **Clean code** - No AI-generated comments
- **Fast** - Results in seconds, not minutes

## Algorithms

- **Requirement matching**: TF-IDF + semantic similarity
- **Security scanning**: Pattern matching + AST analysis
- **Complexity**: Cyclomatic complexity + cognitive complexity
- **Test generation**: Coverage-guided fuzzing + boundary analysis

## Development

```bash
git clone https://github.com/sahilnyk/deburger.git
cd deburger
poetry install
poetry run pytest
poetry run ruff check src/
poetry run mypy src/
```

## License

MIT - See LICENSE file

## Author

**Sahil Nayak**  
GitHub: [@sahilnyk](https://github.com/sahilnyk)  
Email: [sahilnayak2056@gmail.com](mailto:sahilnayak2056@gmail.com)

---

Built because AI generates code fast, but someone needs to check its work.
