import os
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

ALIASES = {
    "num_workers": "workers",
}

app = FastAPI(title="Effective Configuration API", version="1.0.0")

# This API is intended to be called directly by the assignment page's browser.
# No credentials are enabled, so wildcard ACAO is valid for this public endpoint.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


def canonical_key(key: str) -> str:
    normalized = key.strip().lower()
    return ALIASES.get(normalized, normalized)


def coerce(key: str, value):
    key = canonical_key(key)
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "on"}
    if key == "api_key":
        return str(value)
    return str(value)


def merge_config(cli_sets: Optional[List[str]] = None):
    config = dict(DEFAULTS)

    # Layer 2: environment-specific YAML. APP_ENV defaults to development.
    environment = os.environ.get("APP_ENV", "development")
    yaml_path = BASE_DIR / f"config.{environment}.yaml"
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as f:
            yaml_layer = yaml.safe_load(f) or {}
        if isinstance(yaml_layer, dict):
            for key, value in yaml_layer.items():
                config[canonical_key(key)] = value

    # Layer 3: .env values (does not overwrite OS environment).
    env_file_path = BASE_DIR / ".env"
    dotenv_layer = dotenv_values(env_file_path) if env_file_path.exists() else {}
    for raw_key, value in dotenv_layer.items():
        if value is None:
            continue
        key = raw_key.strip().lower()
        if key.startswith("app_"):
            key = key[4:]
        key = canonical_key(key)
        config[key] = value

    # Layer 4: process environment variables with APP_ prefix.
    for raw_key, value in os.environ.items():
        if raw_key.upper().startswith("APP_"):
            key = canonical_key(raw_key[4:])
            config[key] = value

    # Layer 5: repeated CLI overrides, each formatted key=value.
    for item in cli_sets or []:
        if "=" not in item:
            continue
        raw_key, raw_value = item.split("=", 1)
        key = canonical_key(raw_key)
        config[key] = raw_value

    # Normalize known values after merging so their types are consistent.
    normalized = {}
    for key, value in config.items():
        normalized[canonical_key(key)] = coerce(key, value)

    # Mask secrets unconditionally.
    normalized["api_key"] = "****"
    return normalized


@app.get("/")
def health():
    return {"status": "ok", "endpoint": "/effective-config"}


@app.get("/effective-config")
def effective_config(set: Optional[List[str]] = Query(default=None)):
    config = merge_config(set)
    # Ensure the five required fields are present and emitted in stable order.
    return {
        "port": int(config.get("port", 8000)),
        "workers": int(config.get("workers", 1)),
        "debug": bool(config.get("debug", False)),
        "log_level": str(config.get("log_level", "info")),
        "api_key": "****",
    }
