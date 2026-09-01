"""Tests for config loader."""

import pytest
from pathlib import Path
from deburger.config import ConfigError, DeburgerConfig, generate_default_config, load_config


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


def test_rejects_unknown_provider(tmp_path):
    config_path = tmp_path / ".deburger.yml"
    config_path.write_text("provider: digital-ocean\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="unsupported provider"):
        load_config(str(config_path))


def test_rejects_non_mapping_config(tmp_path):
    config_path = tmp_path / ".deburger.yml"
    config_path.write_text("- aws\n- gcp\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="must be a mapping"):
        load_config(str(config_path))


def test_rejects_non_positive_traffic(tmp_path):
    config_path = tmp_path / ".deburger.yml"
    config_path.write_text("traffic:\n  requests_per_day: 0\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="requests_per_day"):
        load_config(str(config_path))


def test_to_dict():
    config = DeburgerConfig()
    d = config.to_dict()
    assert d["provider"] == "aws"
    assert "traffic" in d
    assert "detect" in d
    assert "performance" in d
