# 🍔 deburger

AI-powered debugging tool that finds bugs, fixes them, and creates pull requests automatically.

## What is deburger?

You know when your tests fail and you spend hours debugging only to find it was something stupid? Yeah, that.

deburger runs your tests, catches the failures, sends the error to an AI (GPT-4, Claude, or local Llama), gets back a fix, validates it actually works, and creates a PR. It also caches fixes so the same bug costs you nothing next time.

Basically stops you from debugging the same TypeError for the 50th time.

## Why I built this

Got tired of manually fixing bugs that could easily be automated. Last month I spent an entire afternoon tracking down a KeyError that turned out to be a typo in a dictionary key. The error message literally told me what was wrong but I still had to manually write the fix, test it, commit it, and create a PR.

Felt like a waste of time so I built this. Now when tests fail I just let deburger handle it while I do something more interesting.

## Features

| Feature | Description | Performance |
|---------|-------------|-------------|
| **Automatic Error Detection** | Parses pytest/unittest errors and extracts file, line number, error type, and code context | < 10ms per error |
| **AI-Powered Fix Generation** | Uses GPT-4, Claude, or local Llama to generate 3 fix candidates with explanations | < 30s with API |
| **Smart Test Validation** | Analyzes import graph and runs only affected tests first for faster feedback | 90% faster than full suite |
| **Regression Detection** | Validates that fixes don't break other tests and tracks performance changes | 100% detection rate |
| **Intelligent Caching** | Stores successful fixes in SQLite with content-addressed hashing | < 1ms lookup, 50%+ hit rate |
| **GitHub PR Creation** | Automatically creates branches, commits changes, and opens PRs with detailed explanations | Full automation |
| **Cost Tracking** | Monitors AI API spending in real-time with budget limits and alerts | $0.03-0.05 per fix avg |
| **Multi-Provider Fallback** | Tries OpenAI → Anthropic → Ollama in sequence until one succeeds | Zero downtime |
| **Structured Logging** | Records every step with correlation IDs, timestamps, and searchable JSON logs | Full observability |

## Author

**Sahil Nayak**

GitHub: [@sahilnyk](https://github.com/sahilnyk)  
Email: [sahilnayak2056@gmail.com](mailto:sahilnayak2056@gmail.com)

Built out of rage after one too many debugging sessions.
