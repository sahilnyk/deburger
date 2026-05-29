import subprocess
from pathlib import Path

HOOK_SCRIPT = '''#!/bin/sh
# deburger pre-commit hook - catches expensive code before it ships
deburger check --incremental 2>/dev/null

if [ $? -ne 0 ]; then
    echo ""
    echo "deburger found expensive patterns in your code"
    echo "run 'deburger check -v' for details"
    echo "use 'git commit --no-verify' to skip"
    exit 1
fi
'''


def get_hooks_dir() -> Path:
    # find git hooks directory
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            git_dir = Path(result.stdout.strip())
            return git_dir / "hooks"

    except Exception:
        pass

    return Path(".git") / "hooks"


def install_hook():
    hooks_dir = get_hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_path = hooks_dir / "pre-commit"

    # don't overwrite existing hook, append
    if hook_path.exists():
        existing = hook_path.read_text()
        if "deburger" in existing:
            return  # already installed

        # append to existing hook
        with open(hook_path, 'a') as f:
            f.write("\n\n# deburger cost check\n")
            f.write("deburger check --incremental\n")
    else:
        hook_path.write_text(HOOK_SCRIPT)

    # make executable
    hook_path.chmod(0o755)


def uninstall_hook():
    hooks_dir = get_hooks_dir()
    hook_path = hooks_dir / "pre-commit"

    if not hook_path.exists():
        return

    content = hook_path.read_text()

    if "deburger" not in content:
        return

    # if it's our hook entirely, remove it
    if content.strip() == HOOK_SCRIPT.strip():
        hook_path.unlink()
        return

    # otherwise just remove our lines
    lines = content.split('\n')
    new_lines = [line for line in lines if 'deburger' not in line]
    hook_path.write_text('\n'.join(new_lines))


def run_hook() -> int:
    # run the pre-commit check (called from hook script)
    import asyncio
    from deburger.config import load_config
    from deburger.scanner import FastScanner

    config = load_config()
    scanner = FastScanner(config.to_dict())

    issues = asyncio.run(scanner.scan_path(".", incremental=True))

    if not issues:
        return 0

    # check if any are critical
    critical = [i for i in issues if i.severity.value == "critical"]

    if critical and config.hooks.get("fail_on_critical", True):
        return 1

    # check cost threshold
    max_cost = config.hooks.get("max_monthly_cost", 500)
    total_cost = sum(float(i.estimated_monthly_cost) for i in issues)

    if total_cost > max_cost:
        return 1

    return 0
