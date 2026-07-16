from __future__ import annotations

import re

TIME_PATTERN = re.compile(r"\[(?:\d+\|)?\d{2}:\d{2}:\d{2}\]")
TIME_CAPTURE = re.compile(r"\[(?:\d+\|)?(\d{2}):(\d{2}):(\d{2})\]")

GITHUB_API = "https://api.github.com/repos/OshinoItsuki/lyrics_formatter/releases/latest"
SETTINGS_FILE = "settings.json"
APP_NAME = "歌詞改行ツール"
APP_VERSION = "1.10"

DEFAULT_THRESHOLD = "00:03:10"
DEFAULT_LINE_COUNT = "2"
DEFAULT_CHECK_UPDATE_ON_START = True
DEFAULT_WINDOW_SIZE = "900x700"
DEFAULT_INSPECTOR_SIZE = "220x400"
DEFAULT_IGNORE_FIRST_TAG_ERROR = True
DEFAULT_SORT_BY_FIRST_TAG = True
DEFAULT_PART_START_CHAR = "("
DEFAULT_PART_END_CHAR = ")"
