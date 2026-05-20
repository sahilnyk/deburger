# deburger v0.2.0 - Major Improvements

## what changed

### 1. better CLI commands
- **init** - simpler setup, interactive mode option
- **analyze** - cleaner output, better progress tracking
- **scan** - replaces "security", multi-language support
- **logs** - NEW! view and manage logs
- **config** - manage settings easily
- **guide** - get AI suggestions
- **report** - see metrics

### 2. multi-language security scanning
now catches issues in:
- python
- javascript/typescript
- go
- java
- ruby
- php
- sql

### 3. proper logging
- auto-rotating logs (~/.deburger/logs/)
- JSON format for parsing
- tracks commands and security issues

### 4. dynamic config loading
- no more hardcoded values
- reads from .deburger.yml properly
- validates config

### 5. better terminal output
- cleaner tables and panels
- progress indicators
- color-coded severity levels

### 6. genZ-friendly language
- casual, clear messages
- no excessive emojis (just 🍔)
- human-readable output

## how to use

### setup
```bash
pip install deburger
deburger init "your project goal"
```

### workflow
```bash
# code something
git commit -m "added feature"

# check it
deburger analyze

# scan for issues
deburger scan

# view logs
deburger logs
```

### config
edit `.deburger.yml` to customize:
- sub-goals and weights
- security patterns
- llm settings
- quality thresholds

## publishing to pypi

### automated way
```bash
# test first
python publish_to_pypi.py --test

# then production
python publish_to_pypi.py --prod
```

### manual way
```bash
# clean
rm -rf dist/

# build
python setup.py sdist bdist_wheel

# upload
twine upload dist/*
```

## file structure

```
deburger/
├── src/deburger/
│   ├── cli/                    # all commands
│   ├── security/               # multi-language scanner
│   ├── utils/                  # config, logging
│   ├── analyzer/               # code analysis
│   ├── requirements/           # progress tracking
│   └── ui/                     # terminal output
├── tests/                      # unit tests
├── docs/                       # guides
├── publish_to_pypi.py          # publishing script
└── .deburger.yml               # config example
```

## what's next

- auto-fix for common issues
- more languages (rust, c++, swift)
- github actions integration
- web dashboard
- team collaboration features

## support

- repo: https://github.com/sahilnyk/deburger
- pypi: https://pypi.org/project/deburger/
- issues: https://github.com/sahilnyk/deburger/issues

built by sahil nayak
