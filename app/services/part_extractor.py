from __future__ import annotations

import re

from ..config import TIME_PATTERN


def extract_parts(text: str, start_char: str, end_char: str) -> list[str]:
    """囲み文字内のパート名を抽出する。タイムタグを含む項目は除外する。"""
    if len(start_char) != 1 or len(end_char) != 1:
        raise ValueError("開始文字と終了文字は1文字で指定してください。")
    if start_char == end_char:
        raise ValueError("開始文字と終了文字には別の文字を指定してください。")

    pattern = re.compile(
        re.escape(start_char) + r"([^\r\n]*?)" + re.escape(end_char)
    )

    results: set[str] = set()
    for match in pattern.finditer(text):
        item = match.group(1).strip()
        if not item:
            continue
        if TIME_PATTERN.search(item):
            continue
        results.add(item)

    return sorted(results)
