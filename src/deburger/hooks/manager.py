import subprocess
from pathlib import Path

HOOK_BLOCK = '''# deburger hook start
deburger hook-check

if [ $? -ne 0 ]; then
    echo ""
    echo "deburger found expensive patterns in your code"
    echo "run 'deburger check -v' for details"
    echo "use 'git commit --no-verify' to skip"
    exit 1
fi
# deburger hook end
'''

HOOK_SCRIPT = f"#!/bin/sh\n{HOOK_BLOCK}"


def get_hooks_dir() -> Path:
    # find git hooks directory
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            return Path(result.stdout.strip())

    except Exception:
        pass

    return Path(".git") / "hooks"


def install_hook():
    hooks_dir = get_hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_path = hooks_dir / "pre-commit"

    # don't overwrite existing hook, append
    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8")
        if "deburger" in existing:
            return  # already installed

        # append to existing hook
        with open(hook_path, "a", encoding="utf-8") as f:
            f.write(f"\n{HOOK_BLOCK}")
    else:
        hook_path.write_text(HOOK_SCRIPT, encoding="utf-8")

    # make executable
    hook_path.chmod(0o755)


def uninstall_hook():
    hooks_dir = get_hooks_dir()
    hook_path = hooks_dir / "pre-commit"

    if not hook_path.exists():
        return

    content = hook_path.read_text(encoding="utf-8")

    if "deburger" not in content:
        return

    # if it's our hook entirely, remove it
    if content.strip() == HOOK_SCRIPT.strip():
        hook_path.unlink()
        return

    start = content.find("# deburger hook start")
    end = content.find("# deburger hook end")
    if start >= 0 and end >= start:
        end += len("# deburger hook end")
        cleaned = (content[:start] + content[end:]).strip() + "\n"
        hook_path.write_text(cleaned, encoding="utf-8")


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
