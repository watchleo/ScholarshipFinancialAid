"""Application configuration module.

Loads settings from ``config.json`` ([Unit II] File Management) and merges
them over safe defaults, so the app still runs even if the file is missing.
"""

import json
import os
from pathlib import Path

# Project root = the folder that contains this file
BASE_DIR = Path(__file__).resolve().parent

# Defaults used when config.json is missing or does not override a key
DEFAULTS = {
    "host": "127.0.0.1",
    "port": 5000,
    "debug": False,
    "database_path": "database/scholarship.db",
    "log_path": "logs/app.log",
    "exports_dir": "data/exports",
}


def load_settings(path=None):
    """Read config.json and merge it over DEFAULTS.

    Demonstrates: reading a file with a ``with`` context manager, dict copy
    and dict.update merging.
    """
    settings = dict(DEFAULTS)  # start from a copy of the defaults
    config_file = Path(path) if path else BASE_DIR / "config.json"

    if config_file.exists():
        # [Unit II] File Management: open() used as a context manager
        with open(config_file, "r", encoding="utf-8") as file_handle:
            file_settings = json.load(file_handle)
        if not isinstance(file_settings, dict):
            raise ValueError("config.json must contain a JSON object")
        settings.update(file_settings)  # file values override defaults

    # Turn relative paths into absolute paths anchored at the project root
    for key in ("database_path", "log_path", "exports_dir"):
        settings[key] = str(BASE_DIR / settings[key])

    return settings


SETTINGS = load_settings()


def get(key, fallback=None):
    """Return one setting value with an optional fallback."""
    return SETTINGS.get(key, fallback)


def ensure_runtime_dirs():
    """Create the folders the app writes to (logs, exports) if missing."""
    os.makedirs(os.path.dirname(SETTINGS["log_path"]), exist_ok=True)
    os.makedirs(SETTINGS["exports_dir"], exist_ok=True)
