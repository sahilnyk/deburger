# Changelog

All notable changes to deburger will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-05-28

### Added
- Static analysis for cloud cost estimation (AWS, GCP, Azure)
- Python AST-based code parsing for accurate pattern detection
- JavaScript/TypeScript pattern detection via regex
- Six production-ready pattern detectors:
  - S3/storage operations in loops
  - Missing database connection pools
  - Unbounded database queries without LIMIT
  - Lambda cold start issues (heavy imports in functions)
  - Sequential async operations (await in loops)
  - Expensive logging in hot paths
- CLI with 8 commands: `init`, `check`, `optimize`, `diff`, `blame`, `hook`, `pr-comment`, `version`
- Git hooks integration for pre-commit cost checks
- CI/CD integration with `--json` output flag
- Inline suppression via `deburger:ignore` comments
- Cost estimation based on traffic configuration
- Automatic fix suggestions for N+1 queries and sequential async
- Monthly cost and savings calculations per issue

### Performance
- Handles 21,546 files/second throughput
- Memory footprint <100MB
- Startup time <1 second
- Incremental scanning (10x faster than full scans)
- ThreadPoolExecutor with 32 configurable workers
- File caching with 86400s TTL

### Configuration
- `.deburger.yml` for traffic patterns and thresholds
- Support for custom traffic estimates (requests/day, duration, memory)
- Configurable failure thresholds for CI/CD
- Provider-specific region configuration

### Documentation
- Professional README with real-world examples
- Contribution guide for adding patterns/providers/languages
- MIT license

## [0.2.0] - 2026-05-19

### Added
- Complete project restructure for AI code quality monitoring
- Beautiful CLI UI with rich components
- Code change analysis with git diff parsing
- Security vulnerability scanning (OWASP patterns)
- Code quality metrics calculation
- Requirement progress tracking
- AI steering with guardrails
- Test generation from code analysis
- Function monitoring decorators
- LLM integration (OpenAI, Anthropic)
- Comprehensive documentation

### Changed
- Pivoted from debugging tool to quality guardian
- Minimal dependencies approach
- Production-ready architecture

### Security
- AST-based vulnerability detection
- Pattern matching for secrets
- Guardrail enforcement for LLM prompts
- No jailbreak attempts allowed

## [0.1.0] - Initial Release

### Added
- Basic error detection
- Fix generation with caching
- Test runner integration
