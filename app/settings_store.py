from __future__ import annotations

import json
import os
from typing import Any

from .config import (
    DEFAULT_CHECK_UPDATE_ON_START,
    DEFAULT_IGNORE_FIRST_TAG_ERROR,
    DEFAULT_INSPECTOR_SIZE,
    DEFAULT_LINE_COUNT,
    DEFAULT_PART_END_CHAR,
    DEFAULT_PART_START_CHAR,
    DEFAULT_SORT_BY_FIRST_TAG,
    DEFAULT_THRESHOLD,
    DEFAULT_WINDOW_SIZE,
    SETTINGS_FILE,
)


def default_settings() -> dict[str, Any]:
    return {
        "threshold": DEFAULT_THRESHOLD,
        "line_count": DEFAULT_LINE_COUNT,
        "window_geometry": DEFAULT_WINDOW_SIZE,
        "inspector_geometry": DEFAULT_INSPECTOR_SIZE,
        "ignore_first_tag_error": DEFAULT_IGNORE_FIRST_TAG_ERROR,
        "sort_by_first_tag": DEFAULT_SORT_BY_FIRST_TAG,
        "check_update_on_start": DEFAULT_CHECK_UPDATE_ON_START,
        "part_start_char": DEFAULT_PART_START_CHAR,
        "part_end_char": DEFAULT_PART_END_CHAR,
    }


def write_settings(data: dict[str, Any]) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_settings_data() -> dict[str, Any]:
    if not os.path.exists(SETTINGS_FILE):
        data = default_settings()
        write_settings(data)
        return data

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError("settings.json must contain an object")
    except (OSError, ValueError, json.JSONDecodeError):
        data = default_settings()
        write_settings(data)
        return data

    data = default_settings()
    data.update(loaded)
    return data
