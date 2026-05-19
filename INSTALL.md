# Installation Guide

## Quick Install

### From source (recommended for now)

```bash
git clone https://github.com/sahilnyk/deburger.git
cd deburger
pip install -e .
```

### With LLM support

```bash
pip install -e ".[llm]"
```

### For development

```bash
pip install -e ".[dev,llm]"
```

## Verify Installation

```bash
deburger --help
```

You should see:

```
Usage: deburger [OPTIONS] COMMAND [ARGS]...

🍔 AI Code Quality Guardian

Commands:
  analyze   Analyze code changes
  config    Configure deburger settings
  guide     Get AI guidance for next steps
  init      Initialize deburger configuration
  report    Generate metrics report
  security  Run security vulnerability scan
  version   Show deburger version
```

## Quick Start

### 1. Initialize in your project

```bash
cd your-project/
deburger init --requirement "Build REST API with authentication"
```

### 2. Make some changes with AI

Use any AI tool (ChatGPT, Claude, etc.) to generate code.

### 3. Analyze changes

```bash
git add .
git commit -m "Add user authentication"
deburger analyze
```

### 4. Run security scan

```bash
deburger security
```

## Using Makefile

```bash
make help           # Show all commands
make install        # Install package
make install-dev    # Install with dev dependencies
make test           # Run tests
make lint           # Check code quality
make format         # Format code
make run-analyze    # Run analysis
make run-security   # Run security scan
```

## Configuration

### Set API keys (optional, for AI guidance)

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Edit .deburger.yml

```yaml
requirement: "Your main goal"

sub_goals:
  - id: feature1
    description: "First feature"
    weight: 50
  - id: feature2
    description: "Second feature"
    weight: 50

llm:
  provider: openai
  model: gpt-4
  
  guardrails:
    - "Never disable security"
    - "Always validate input"
```

## Usage Examples

### Analyze last commit

```bash
deburger analyze
```

### Analyze last 3 commits

```bash
deburger analyze --since HEAD~3
```

### Security scan only

```bash
deburger security --path src/
```

### Get AI guidance

```bash
deburger guide
```

## Troubleshooting

### Command not found

```bash
pip install -e .
# or
python -m deburger.cli.main --help
```

### Import errors

```bash
pip install typer rich pyyaml
```

### LLM features not working

```bash
pip install openai anthropic
export OPENAI_API_KEY="your-key"
```

## Uninstall

```bash
pip uninstall deburger
```
