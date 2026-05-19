# 🍔 Publishing to PyPI

## Prerequisites

1. **PyPI Account**: Create at https://pypi.org/account/register/
2. **API Token**: Get from https://pypi.org/manage/account/token/
3. **Install Tools**:
   ```bash
   pip install build twine
   ```

## Step-by-Step Publish

### 1. Clean Previous Builds

```bash
make clean
# or
rm -rf build/ dist/ *.egg-info
```

### 2. Build Package

```bash
make build
# or
python -m build
```

This creates:
- `dist/deburger-0.2.0.tar.gz` (source)
- `dist/deburger-0.2.0-py3-none-any.whl` (wheel)

### 3. Check Package

```bash
twine check dist/*
```

Should show: `PASSED`

### 4. Test on TestPyPI (Optional)

```bash
twine upload --repository testpypi dist/*
# Username: __token__
# Password: <your-testpypi-token>

# Test install
pip install --index-url https://test.pypi.org/simple/ deburger
```

### 5. Publish to Real PyPI

```bash
twine upload dist/*
# Username: __token__
# Password: <your-pypi-token>
```

### 6. Verify

```bash
pip install deburger
deburger --help
```

## Using GitHub Actions (Automated)

1. Add PyPI token to GitHub Secrets:
   - Go to repo Settings → Secrets → Actions
   - Add: `PYPI_API_TOKEN`

2. Create a GitHub Release:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

3. Create release on GitHub:
   - Go to Releases → Draft new release
   - Tag: v0.2.0
   - Title: v0.2.0
   - Click "Publish release"

4. GitHub Actions will auto-publish to PyPI

## Version Updates

Before publishing new version:

1. Update version in:
   - `setup.py` (line 12)
   - `pyproject.toml` (line 3)
   - `src/deburger/__init__.py` (line 3)
   - `PKG-INFO` (line 3)

2. Update `CHANGELOG.md`

3. Commit:
   ```bash
   git add setup.py pyproject.toml src/deburger/__init__.py PKG-INFO CHANGELOG.md
   git commit -m "updated: version to 0.3.0"
   git tag v0.3.0
   git push origin master --tags
   ```

## Troubleshooting

**Authentication Failed**
- Make sure you're using `__token__` as username
- Copy token correctly (no extra spaces)

**File Already Exists**
- Can't re-upload same version
- Increment version number

**Invalid Distribution**
- Run `twine check dist/*`
- Check setup.py syntax
- Ensure README.md exists

## Quick Commands

```bash
# Full publish workflow
make clean
make build
twine check dist/*
twine upload dist/*

# Or with Makefile
make publish
```
