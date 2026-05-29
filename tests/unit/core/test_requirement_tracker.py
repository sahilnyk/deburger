"""Tests for config loader."""

import pytest
from pathlib import Path
from deburger.config import DeburgerConfig, load_config, generate_default_config


def test_default_config():
    config = DeburgerConfig()
    assert config.provider == "aws"
    assert config.region == "us-east-1"
    assert config.traffic["requests_per_day"] == 100000


def test_load_config_from_file(tmp_path, monkeypatch):
    config_file = tmp_path / ".deburger.yml"
    config_file.write_text("provider: gcp\nregion: us-central1\n")
    monkeypatch.chdir(tmp_path)

    config = load_config()
    assert config.provider == "gcp"
    assert config.region == "us-central1"


def test_env_vars_override(monkeypatch):
    monkeypatch.setenv("DEBURGER_PROVIDER", "azure")
    monkeypatch.setenv("DEBURGER_REGION", "eastus")

    config = load_config(config_path="/nonexistent")
    assert config.provider == "azure"
    assert config.region == "eastus"


def test_generate_default_config():
    content = generate_default_config()
    assert "provider: aws" in content
    assert "region: us-east-1" in content
    assert "requests_per_day" in content


def test_to_dict():
    config = DeburgerConfig()
    d = config.to_dict()
    assert d["provider"] == "aws"
    assert "traffic" in d
    assert "detect" in d
    assert "performance" in d
