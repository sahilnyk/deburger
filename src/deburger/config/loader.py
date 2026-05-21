import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import yaml


DEFAULT_CONFIG = {
    "provider": "aws",
    "region": "us-east-1",
    "traffic": {
        "requests_per_day": 100000,
        "avg_duration_ms": 1000,
        "avg_memory_mb": 1024,
        "db_queries_per_request": 10,
        "concurrent_connections": 100,
        "data_transfer_gb": 100,
    },
    "detect": {
        "n_plus_one_queries": True,
        "sequential_async": True,
        "over_provisioned": True,
        "missing_caching": True,
    },
    "performance": {
        "max_workers": 32,
        "incremental": True,
        "cache_ttl": 86400,
    },
    "hooks": {
        "pre_commit": True,
        "fail_on_critical": True,
        "max_monthly_cost": 500,
    },
    "output": {
        "format": "rich",
        "verbose": False,
        "show_fixes": True,
    }
}


@dataclass
class DeburgerConfig:
    provider: str = "aws"
    region: str = "us-east-1"
    traffic: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["traffic"].copy())
    detect: Dict[str, bool] = field(default_factory=lambda: DEFAULT_CONFIG["detect"].copy())
    performance: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["performance"].copy())
    hooks: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["hooks"].copy())
    output: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["output"].copy())

    def to_dict(self) -> Dict:
        return {
            "provider": self.provider,
            "region": self.region,
            "traffic": self.traffic,
            "detect": self.detect,
            "performance": self.performance,
            "hooks": self.hooks,
            "output": self.output,
        }


def find_config_file(start_path: Optional[str] = None) -> Optional[Path]:
    # walk up looking for .deburger.yml
    path = Path(start_path or os.getcwd()).resolve()

    while path != path.parent:
        config_file = path / ".deburger.yml"
        if config_file.exists():
            return config_file

        config_file = path / ".deburger.yaml"
        if config_file.exists():
            return config_file

        path = path.parent

    return None


def load_config(config_path: Optional[str] = None) -> DeburgerConfig:
    # load config from file + env vars
    config = DeburgerConfig()

    # find and load config file
    if config_path:
        file_path = Path(config_path)
    else:
        file_path = find_config_file()

    if file_path and file_path.exists():
        with open(file_path, 'r') as f:
            file_config = yaml.safe_load(f) or {}

        # merge file config into defaults
        if "provider" in file_config:
            config.provider = file_config["provider"]
        if "region" in file_config:
            config.region = file_config["region"]
        if "traffic" in file_config:
            config.traffic.update(file_config["traffic"])
        if "detect" in file_config:
            config.detect.update(file_config["detect"])
        if "performance" in file_config:
            config.performance.update(file_config["performance"])
        if "hooks" in file_config:
            config.hooks.update(file_config["hooks"])
        if "output" in file_config:
            config.output.update(file_config["output"])

    # env vars override everything (DEBURGER_PROVIDER, DEBURGER_REGION, etc)
    env_provider = os.environ.get("DEBURGER_PROVIDER")
    if env_provider:
        config.provider = env_provider

    env_region = os.environ.get("DEBURGER_REGION")
    if env_region:
        config.region = env_region

    env_requests = os.environ.get("DEBURGER_REQUESTS_PER_DAY")
    if env_requests:
        config.traffic["requests_per_day"] = int(env_requests)

    env_workers = os.environ.get("DEBURGER_MAX_WORKERS")
    if env_workers:
        config.performance["max_workers"] = int(env_workers)

    return config


def generate_default_config() -> str:
    # generate a fresh .deburger.yml
    return yaml.dump(DEFAULT_CONFIG, default_flow_style=False, sort_keys=False)
