# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- Handle RecursionError in AST parser to prevent crashes on deeply nested code
- Resolve all ruff lint errors for better code quality

### Added
- Test and publish workflows for GitHub Actions CI/CD

### Changed
- Remove horizontal lines from README for cleaner formatting

## [1.0.1] - 2025-01-15

### Changed
- Update README with command outputs
- Bump version to v1.0.1

## [1.0.0] - 2024-12-10

### Added
- JavaScript/TypeScript analyzer with full test coverage
- Python analyzer with suppression and pattern detector tests
- Core unit tests for CLI, cache, hooks, optimizer, providers, and edges
- Inline suppression support via `deburger:ignore` comments
- `--json` flag for CI integration
- Professional PyPI ready documentation

### Changed
- Move old test files into language-specific directories
- Hoist imports in scanner and integrations, remove unused fields
- Clean README with badges, trim pyproject.toml
- Pre-compile regexes in all analyzers and pattern detectors

### Improved
- Performance: Reuse SQLite connection in cache
- Performance: Fix double-read in FileCache
- Performance: Hoist imports for faster load times

### Fixed
- Quick test script now matches current code

## [Earlier Versions]

- v0.x: Initial development and pattern detection framework
