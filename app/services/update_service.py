from __future__ import annotations

import json
import urllib.request
from typing import Any

from ..config import GITHUB_API


def get_latest_release() -> dict[str, Any] | None:
    try:
        request = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "LyricsFormatter"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        assets = data.get("assets", [])
        download_url = None
        if assets:
            download_url = assets[0].get("browser_download_url")

        return {
            "version": data["tag_name"],
            "date": data["published_at"][:10],
            "url": data["html_url"],
            "download": download_url,
        }
    except Exception:
        return None
