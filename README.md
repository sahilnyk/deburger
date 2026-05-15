# 🍔 deburger

An AI-powered debugging tool that automatically finds, fixes, and validates bugs in your code. No more staring at stack traces at 3 AM.

## What is deburger?

Look, we've all been there. You run your tests, they fail, you spend 2 hours debugging, only to realize you forgot a `!=` instead of `==`. Or worse, a sneaky zero division error that only happens in production.

**deburger** is your debugging companion that detects errors automatically, uses AI to generate fixes, validates them by running your test suite, and creates pull requests with the fix. It caches successful fixes so you never pay for the same bug twice.

It's like having a senior engineer who's really good at debugging, but they work for pennies and never get tired.

## Why I built this

I got tired of fixing the same stupid bugs over and over again. Like, why am I manually debugging a `KeyError` for the 47th time this month? Why can't the computer just fix it?

So I rage-built **deburger** after spending 4 hours debugging a test that failed because I used `x = y` instead of `x == y`. True story. Never again.

Now when my tests fail, I just run `deburger run` and go grab a coffee. By the time I'm back, there's a PR waiting with the fix.

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
