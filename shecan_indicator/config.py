from __future__ import annotations

import json
import logging
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from gi.repository import GLib

from .i18n import DDNS_URL_PREFIX, normalize_lang, t

log = logging.getLogger("shecan-indicator")

CONFIG_DIR = Path(GLib.get_user_config_dir()) / "shecan-indicator"
CONFIG_PATH = CONFIG_DIR / "config.json"

MIN_INTERVAL_SEC = 3
MAX_INTERVAL_SEC = 3600


@dataclass
class Settings:
    language: str = "fa"
    poll_interval_sec: int = 10
    show_label: bool = False
    label_connected: str = "متصل"
    label_disconnected: str = "قطع"
    label_unknown: str = "…"
    notify_on_change: bool = True
    ddns_update_url: str = ""

    def clamp(self) -> "Settings":
        self.language = normalize_lang(self.language)
        self.poll_interval_sec = max(
            MIN_INTERVAL_SEC, min(MAX_INTERVAL_SEC, int(self.poll_interval_sec))
        )
        self.show_label = bool(self.show_label)
        self.notify_on_change = bool(self.notify_on_change)
        self.label_connected = (
            self.label_connected or t(self.language, "default_connected")
        ).strip() or t(self.language, "default_connected")
        self.label_disconnected = (
            self.label_disconnected or t(self.language, "default_disconnected")
        ).strip() or t(self.language, "default_disconnected")
        self.label_unknown = (
            self.label_unknown or t(self.language, "default_unknown")
        ).strip() or t(self.language, "default_unknown")
        self.ddns_update_url = sanitize_ddns_url(self.ddns_update_url)
        return self


DEFAULTS = Settings()


def sanitize_ddns_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return ""
    if not parsed.netloc.endswith("shecan.ir"):
        return ""
    if not url.startswith(DDNS_URL_PREFIX):
        # Allow https://ddns.shecan.ir/... only
        if parsed.netloc != "ddns.shecan.ir":
            return ""
    return url


def _from_dict(data: dict[str, Any]) -> Settings:
    base = asdict(DEFAULTS)
    base.update({k: v for k, v in data.items() if k in base})
    return Settings(**base).clamp()


def load_settings() -> Settings:
    if not CONFIG_PATH.is_file():
        return deepcopy(DEFAULTS)
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("config root must be an object")
        return _from_dict(data)
    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to read settings (%s); using defaults.", exc)
        return deepcopy(DEFAULTS)


def save_settings(settings: Settings) -> None:
    settings = settings.clamp()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(asdict(settings), fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    tmp.replace(CONFIG_PATH)
