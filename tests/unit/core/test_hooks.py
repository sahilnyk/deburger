"""Tests for git hook management."""

import pytest
from pathlib import Path
from unittest.mock import patch
from deburger.hooks.manager import install_hook, uninstall_hook, HOOK_SCRIPT


class TestInstallHook:
    def test_creates_hook_file(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        with patch("deburger.hooks.manager.get_hooks_dir", return_value=hooks_dir):
            install_hook()

        hook = hooks_dir / "pre-commit"
        assert hook.exists()
        assert "deburger" in hook.read_text()
        assert hook.stat().st_mode & 0o755

    def test_appends_to_existing_hook(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook = hooks_dir / "pre-commit"
        hook.write_text("#!/bin/sh\necho 'existing hook'\n")

        with patch("deburger.hooks.manager.get_hooks_dir", return_value=hooks_dir):
            install_hook()

        content = hook.read_text()
        assert "existing hook" in content
        assert "deburger" in content

    def test_skips_if_already_installed(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook = hooks_dir / "pre-commit"
        hook.write_text(HOOK_SCRIPT)

        with patch("deburger.hooks.manager.get_hooks_dir", return_value=hooks_dir):
            install_hook()

        assert hook.read_text().count("deburger") == HOOK_SCRIPT.count("deburger")


class TestUninstallHook:
    def test_removes_deburger_hook(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook = hooks_dir / "pre-commit"
        hook.write_text(HOOK_SCRIPT)

        with patch("deburger.hooks.manager.get_hooks_dir", return_value=hooks_dir):
            uninstall_hook()

        assert not hook.exists()

    def test_removes_only_deburger_lines(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook = hooks_dir / "pre-commit"
        hook.write_text("#!/bin/sh\necho 'keep'\ndeburger check\n")

        with patch("deburger.hooks.manager.get_hooks_dir", return_value=hooks_dir):
            uninstall_hook()

        content = hook.read_text()
        assert "keep" in content
        assert "deburger" not in content

    def test_noop_if_no_hook(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()

        with patch("deburger.hooks.manager.get_hooks_dir", return_value=hooks_dir):
            uninstall_hook()  # should not raise
