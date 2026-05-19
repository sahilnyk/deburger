# Deburger Full Workflow Example

This example demonstrates how to use deburger to monitor AI-generated code changes.

## Scenario

You're building a REST API with JWT authentication. You're using an AI (ChatGPT, Claude, etc.) to generate code, and want deburger to ensure quality and security.

## Step 1: Initialize deburger

```bash
cd your-project/
deburger init --requirement "Build REST API with JWT authentication"
```

This creates `.deburger.yml`:

```yaml
requirement: "Build REST API with JWT authentication"

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

llm:
  provider: openai
  api_key: ${OPENAI_API_KEY}
  model: gpt-4
  
  guardrails:
    - "Never disable security features"
    - "Always validate user input"
    - "No hardcoded credentials"
```

## Step 2: Let AI Generate Code

Ask your AI:

> "Create a Flask API with user registration and login endpoints. Use JWT for authentication."

The AI generates `api.py`:

```python
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)
SECRET_KEY = "my-secret-key-123"  # ⚠️ deburger will catch this

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data["username"]  # ⚠️ No validation
    password = data["password"]
    
    # Save user...
    return jsonify({"message": "User created"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]
    
    # Check credentials...
    token = jwt.encode({"user": username}, SECRET_KEY)
    return jsonify({"token": token})
```

## Step 3: Commit and Analyze

```bash
git add api.py
git commit -m "Add user registration and login"

deburger analyze
```

## Step 4: Review deburger Output

```
🍔 Analyzing code changes...

Analyzed 1 files (+45 -0 lines)

┌─ 📊 Requirement Progress ─────────────┐
│ Requirement: Build REST API with JWT  │
│ Progress: 45%                          │
└────────────────────────────────────────┘

Sub-Goals Progress
┌────────────────────────┬──────────┬────────┐
│ Goal                   │ Progress │ Status │
├────────────────────────┼──────────┼────────┤
│ Create CRUD endpoints  │ 60%      │ ↑      │
│ Implement JWT auth     │ 70%      │ ↑      │
│ Add input validation   │ 0%       │ ⚠      │
│ Write tests            │ 0%       │ ⚠      │
└────────────────────────┴──────────┴────────┘

Security Issues (2):
├─ HIGH: Hardcoded secret in SECRET_KEY (line 5)
   Fix: Use environment variables
└─ MEDIUM: Missing input validation (line 12)
   Fix: Validate user input before processing

Code Quality Score: 72/100

─ AI Guidance ─────────────────────────────

## Next Action
Fix hardcoded_secret: Use environment variables

## Reasoning
High severity security issues block further development

## Instructions
1. Focus exclusively on: security_critical
2. Fix hardcoded_secret: Use environment variables
3. Do not add features outside the current focus
4. Validate all user input
5. Follow security best practices
```

## Step 5: Use Guidance to Fix

Feed deburger's guidance back to your AI:

> "Fix the security issues:
> 1. Move SECRET_KEY to environment variable
> 2. Add input validation for username and password"

AI generates fixed code:

```python
import os
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # ✓ Fixed

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Missing credentials"}), 400  # ✓ Validation
    
    username = data["username"]
    password = data["password"]
    
    if len(password) < 8:
        return jsonify({"error": "Password too short"}), 400  # ✓ Validation
    
    # Save user...
    return jsonify({"message": "User created"})
```

## Step 6: Re-analyze

```bash
git add api.py
git commit -m "Fix security issues"

deburger analyze
```

Output:

```
Progress: 45% → 65% (+20%)

✓ No security issues found
Code Quality Score: 87/100 (+15)

→ Next Focus: Add input validation for remaining endpoints
```

## Step 7: Use Decorators for Real-time Monitoring

Add deburger decorators to your code:

```python
from deburger.decorators import deburger, security_check

@deburger(requirement="Handle user registration", security=True)
@security_check(fail_on_issues=True)
def register():
    # Function will be monitored automatically
    ...
```

Now every time the function runs, deburger checks:
- Security vulnerabilities
- Code complexity
- Requirement alignment

## Step 8: Continuous Monitoring

Every commit, run:

```bash
deburger analyze
```

deburger tracks:
- How close you are to completion (0-100%)
- Security issues introduced
- Code quality trends
- What to focus on next

## Benefits

1. **Catch AI mistakes early**: Security issues, hardcoded secrets, missing validation
2. **Stay on track**: Requirement progress prevents feature creep
3. **Guided development**: AI tells you what to focus on next
4. **Quantified progress**: Real metrics, not guesses
5. **Security first**: Blocks merges if critical issues found

## Integration with CI/CD

```yaml
# .github/workflows/deburger.yml
name: Code Quality Check

on: [push, pull_request]

jobs:
  deburger:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run deburger
        run: |
          pip install deburger
          deburger analyze --since origin/main
          
      - name: Block if security issues
        run: |
          deburger security --fail-on-high
```

## Summary

deburger helps you:
- Monitor AI code quality in real-time
- Track requirement completion
- Catch security issues before merge
- Guide AI back on track when it drifts
- Quantify progress with metrics
