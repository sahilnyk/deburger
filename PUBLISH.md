# 📦 Publishing deburger to PyPI

Complete guide for publishing deburger to PyPI.

---

## Prerequisites

### 1. Install Tools
```bash
pip install build twine
```

### 2. Create PyPI Accounts
- **Production**: https://pypi.org/account/register/
- **Test**: https://test.pypi.org/account/register/

### 3. Generate API Tokens

**Test PyPI:**
1. Go to https://test.pypi.org/manage/account/token/
2. Create token with "Entire account" scope
3. Save token

**Production PyPI:**
1. Go to https://pypi.org/manage/account/token/
2. Create token with "Entire account" scope
3. Save token

### 4. Configure Credentials

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-TOKEN-HERE
```

Secure it:
```bash
chmod 600 ~/.pypirc
```

---

## Quick Publish (Automated Script)

### Test Publish
```bash
python publish_to_pypi.py --test
```

### Production Publish
```bash
python publish_to_pypi.py --prod
```

The script handles everything:
- ✓ Version check
- ✓ Run tests
- ✓ Lint code
- ✓ Clean builds
- ✓ Build package
- ✓ Upload to PyPI

---

## Manual Publish Steps

### 1. Update Version

Edit **both** files (must match):

**src/deburger/_version.py:**
```python
__version__ = "0.2.1"
```

**pyproject.toml (line 3):**
```toml
version = "0.2.1"
```

### 2. Update Changelog

**CHANGELOG.md:**
```markdown
## [0.2.1] - 2026-05-21

### Added
- Multi-language security scanning
- Structured logging
- Improved CLI

### Changed
- Dynamic config loading

### Fixed
- Config validation
```

### 3. Run Tests
```bash
pytest tests/ -v
```

### 4. Lint Code
```bash
ruff check src/
```

### 5. Clean Builds
```bash
rm -rf build/ dist/ *.egg-info src/*.egg-info
```

### 6. Build Package
```bash
python setup.py sdist bdist_wheel
```

Verify:
```bash
ls dist/
# deburger-0.2.1-py3-none-any.whl
# deburger-0.2.1.tar.gz
```

### 7. Check Package
```bash
twine check dist/*
```

### 8. Upload to TestPyPI (Recommended First)
```bash
twine upload --repository testpypi dist/*
```

Test installation:
```bash
python -m venv test_env
source test_env/bin/activate
pip install --index-url https://test.pypi.org/simple/ deburger
deburger --help
deactivate
```

### 9. Upload to Production PyPI
```bash
twine upload dist/*
```

---

## Post-Publishing

### 1. Create Git Tag
```bash
git tag v0.2.1
git push origin v0.2.1
```

### 2. Create GitHub Release
1. Go to https://github.com/sahilnyk/deburger/releases/new
2. Tag: `v0.2.1`
3. Title: `deburger v0.2.1`
4. Description: Copy from CHANGELOG.md
5. Attach dist files

### 3. Test Installation
```bash
pip install deburger
deburger --help
deburger version
```

---

## Troubleshooting

### "File already exists"
**Fix:** Increment version, rebuild, re-upload

### "Invalid credentials"
**Fix:** Check `~/.pypirc` token is correct

### "HTTPError: 403"
**Fix:** Regenerate API token on PyPI

### "Package verification failed"
**Fix:** 
```bash
twine check dist/*
cat MANIFEST.in
```

---

## Quick Reference

```bash
# Automated publish (test)
python publish_to_pypi.py --test

# Automated publish (production)
python publish_to_pypi.py --prod

# Manual build & upload
rm -rf dist/
python setup.py sdist bdist_wheel
twine check dist/*
twine upload dist/*
```

---

## Security

1. Never commit tokens to git
2. Use `.gitignore` for `.pypirc`
3. Rotate tokens periodically
4. Enable 2FA on PyPI

---

**Ready to publish? Run:**
```bash
python publish_to_pypi.py --test    # Test first
python publish_to_pypi.py --prod    # Then production
```
