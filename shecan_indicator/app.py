from __future__ import annotations

import fcntl
import logging
import os
import signal
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("Notify", "0.7")

from gi.repository import AppIndicator3, GLib, Gtk, Notify  # noqa: E402

from . import __version__
from .config import Settings, load_settings, save_settings
from .i18n import PANEL_URL, normalize_lang, t
from .settings_dialog import SettingsDialog

CHECK_URL = "https://check.shecan.ir/"
CONNECTED_BODY = "2"
REQUEST_TIMEOUT_S = 5.0
DDNS_TIMEOUT_S = 15.0
USER_AGENT = f"ShecanIndicator/{__version__}"

ICONS_DIR = Path(__file__).resolve().parent / "icons"
LOCK_PATH = Path(GLib.get_user_runtime_dir()) / "shecan-indicator.lock"

log = logging.getLogger("shecan-indicator")


class Status(Enum):
    UNKNOWN = auto()
    CONNECTED = auto()
    DISCONNECTED = auto()


@dataclass(frozen=True)
class CheckResult:
    status: Status
    detail: str
    checked_at: datetime


def _icon_path(name: str) -> str:
    for ext in (".png", ".svg"):
        path = ICONS_DIR / f"{name}{ext}"
        if path.is_file():
            return str(path)
    raise FileNotFoundError(f"Icon not found: {name}")


ICON_BY_STATUS = {
    Status.UNKNOWN: "shecan-unknown",
    Status.CONNECTED: "shecan-connected",
    Status.DISCONNECTED: "shecan-disconnected",
}


def probe_shecan(lang: str) -> CheckResult:
    now = datetime.now()
    request = urllib.request.Request(
        CHECK_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain,*/*",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S) as response:
            raw = response.read(64).decode("utf-8", errors="replace").strip()
            http_code = getattr(response, "status", None) or response.getcode()

        if raw == CONNECTED_BODY:
            return CheckResult(
                status=Status.CONNECTED,
                detail=t(lang, "detail_ok", raw=raw, code=http_code),
                checked_at=now,
            )

        return CheckResult(
            status=Status.DISCONNECTED,
            detail=t(lang, "detail_unexpected", raw=raw, code=http_code),
            checked_at=now,
        )
    except urllib.error.HTTPError as exc:
        return CheckResult(
            status=Status.DISCONNECTED,
            detail=t(lang, "detail_http", code=exc.code),
            checked_at=now,
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            status=Status.DISCONNECTED,
            detail=t(lang, "detail_unreachable", error=exc.__class__.__name__),
            checked_at=now,
        )


def request_ddns_update(url: str) -> tuple[bool, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/plain,*/*",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=DDNS_TIMEOUT_S) as response:
            body = response.read(512).decode("utf-8", errors="replace").strip()
            code = getattr(response, "status", None) or response.getcode()
        if 200 <= int(code) < 300:
            return True, body or f"HTTP {code}"
        return False, body or f"HTTP {code}"
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(512).decode("utf-8", errors="replace").strip()
        except Exception:  # noqa: BLE001
            body = ""
        return False, body or f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return False, exc.__class__.__name__


class SingleInstance:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._fh: Optional[object] = None

    def acquire(self) -> bool:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self._path, "w", encoding="utf-8")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.close()
            return False

        fh.write(str(os.getpid()))
        fh.flush()
        self._fh = fh
        return True

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            self._fh.close()
            self._fh = None


class ShecanIndicator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self._checking = False
        self._updating_ip = False
        self._status = Status.UNKNOWN
        self._detail = t(self.lang, "not_checked")
        self._checked_at: Optional[datetime] = None
        self._notify_ready = Notify.init("Shecan Indicator")
        self._last_notified: Optional[Status] = None
        self._timer_id: Optional[int] = None
        self._settings_dialog: Optional[SettingsDialog] = None

        self.indicator = AppIndicator3.Indicator.new(
            "shecan-indicator",
            _icon_path("shecan-unknown"),
            AppIndicator3.IndicatorCategory.SYSTEM_SERVICES,
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title(t(self.lang, "app_name"))

        self.status_item = Gtk.MenuItem(label=t(self.lang, "checking"))
        self.status_item.set_sensitive(False)

        self.detail_item = Gtk.MenuItem(label=self._detail)
        self.detail_item.set_sensitive(False)

        self.refresh_item = Gtk.MenuItem(label=t(self.lang, "refresh"))
        self.refresh_item.connect("activate", self._on_refresh)

        self.update_ip_item = Gtk.MenuItem(label=t(self.lang, "update_ip"))
        self.update_ip_item.connect("activate", self._on_update_ip)

        self.panel_item = Gtk.MenuItem(label=t(self.lang, "open_panel"))
        self.panel_item.connect("activate", self._on_open_panel)

        self.settings_item = Gtk.MenuItem(label=t(self.lang, "settings"))
        self.settings_item.connect("activate", self._on_settings)

        self.quit_item = Gtk.MenuItem(label=t(self.lang, "quit"))
        self.quit_item.connect("activate", self._on_quit)

        self.menu = Gtk.Menu()
        for item in (
            self.status_item,
            self.detail_item,
            Gtk.SeparatorMenuItem(),
            self.refresh_item,
            self.update_ip_item,
            self.panel_item,
            Gtk.SeparatorMenuItem(),
            self.settings_item,
            Gtk.SeparatorMenuItem(),
            self.quit_item,
        ):
            self.menu.append(item)
            item.show()

        self.menu.show_all()
        self.indicator.set_menu(self.menu)
        self._apply_direction()
        self._apply_ui(initial=True)

    @property
    def lang(self) -> str:
        return normalize_lang(self.settings.language)

    def start(self) -> None:
        self._arm_timer()
        self._schedule_check()
        Gtk.main()

    def _apply_direction(self) -> None:
        direction = Gtk.TextDirection.RTL if self.lang == "fa" else Gtk.TextDirection.LTR
        self.menu.set_direction(direction)

    def _arm_timer(self) -> None:
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None
        interval_ms = max(3, int(self.settings.poll_interval_sec)) * 1000
        self._timer_id = GLib.timeout_add(interval_ms, self._on_timer)

    def _on_timer(self) -> bool:
        self._schedule_check()
        return True

    def _on_refresh(self, _widget: Gtk.MenuItem) -> None:
        self._schedule_check()

    def _on_open_panel(self, _widget: Gtk.MenuItem) -> None:
        webbrowser.open(PANEL_URL)

    def _on_update_ip(self, _widget: Gtk.MenuItem) -> None:
        url = (self.settings.ddns_update_url or "").strip()
        if not url:
            self._notify(
                t(self.lang, "ip_notify_title"),
                t(self.lang, "ip_missing_url"),
                "shecan-disconnected",
            )
            return

        with self._lock:
            if self._updating_ip:
                return
            self._updating_ip = True

        self.update_ip_item.set_sensitive(False)
        self._notify(
            t(self.lang, "ip_notify_title"),
            t(self.lang, "ip_updating"),
            "shecan-unknown",
        )
        thread = threading.Thread(
            target=self._ddns_worker, args=(url,), name="shecan-ddns", daemon=True
        )
        thread.start()

    def _ddns_worker(self, url: str) -> None:
        try:
            ok, body = request_ddns_update(url)
        finally:
            with self._lock:
                self._updating_ip = False
        GLib.idle_add(self._on_ddns_done, ok, body, priority=GLib.PRIORITY_DEFAULT)

    def _on_ddns_done(self, ok: bool, body: str) -> bool:
        self.update_ip_item.set_sensitive(True)
        if ok:
            self._notify(
                t(self.lang, "ip_notify_title"),
                t(self.lang, "ip_success", body=body),
                "shecan-connected",
            )
            self._schedule_check()
        else:
            self._notify(
                t(self.lang, "ip_notify_title"),
                t(self.lang, "ip_error", body=body),
                "shecan-disconnected",
            )
        return False

    def _on_settings(self, _widget: Gtk.MenuItem) -> None:
        if self._settings_dialog is not None:
            self._settings_dialog.present()
            return
        dialog = SettingsDialog(None, self.settings, on_save=self._apply_settings)
        dialog.connect("destroy", self._on_settings_closed)
        self._settings_dialog = dialog

    def _on_settings_closed(self, _dialog: Gtk.Dialog) -> None:
        self._settings_dialog = None

    def _apply_settings(self, settings: Settings) -> None:
        interval_changed = settings.poll_interval_sec != self.settings.poll_interval_sec
        self.settings = settings
        save_settings(settings)
        if interval_changed:
            self._arm_timer()
        self._relabel_menu()
        self._apply_direction()
        self._apply_ui()
        log.info(
            t(
                self.lang,
                "settings_saved",
                interval=settings.poll_interval_sec,
                show_label=settings.show_label,
            )
        )

    def _relabel_menu(self) -> None:
        self.refresh_item.set_label(t(self.lang, "refresh"))
        self.update_ip_item.set_label(t(self.lang, "update_ip"))
        self.panel_item.set_label(t(self.lang, "open_panel"))
        self.settings_item.set_label(t(self.lang, "settings"))
        self.quit_item.set_label(t(self.lang, "quit"))
        self.indicator.set_title(t(self.lang, "app_name"))

    def _on_quit(self, _widget: Gtk.MenuItem) -> None:
        if self._notify_ready:
            Notify.uninit()
        Gtk.main_quit()

    def _schedule_check(self) -> None:
        with self._lock:
            if self._checking:
                return
            self._checking = True

        thread = threading.Thread(target=self._worker, name="shecan-check", daemon=True)
        thread.start()

    def _worker(self) -> None:
        try:
            result = probe_shecan(self.lang)
            GLib.idle_add(self._update_from_result, result, priority=GLib.PRIORITY_DEFAULT)
        finally:
            with self._lock:
                self._checking = False

    def _update_from_result(self, result: CheckResult) -> bool:
        previous = self._status
        self._status = result.status
        self._detail = result.detail
        self._checked_at = result.checked_at
        self._apply_ui()
        self._maybe_notify(previous, result.status)
        return False

    def _label_for(self, status: Status) -> str:
        if status == Status.CONNECTED:
            return self.settings.label_connected
        if status == Status.DISCONNECTED:
            return self.settings.label_disconnected
        return self.settings.label_unknown

    def _title_for(self, status: Status) -> str:
        return t(self.lang, "title_prefix", label=self._label_for(status))

    def _apply_ui(self, initial: bool = False) -> None:
        icon = _icon_path(ICON_BY_STATUS[self._status])
        title = self._title_for(self._status)
        label = self._label_for(self._status)

        self.indicator.set_icon_full(icon, title)
        self.indicator.set_title(title)

        if self.settings.show_label:
            guide = max(
                self.settings.label_connected,
                self.settings.label_disconnected,
                self.settings.label_unknown,
                key=len,
            )
            self.indicator.set_label(label, guide)
        else:
            self.indicator.set_label("", "")

        self.status_item.set_label(label)

        if self._checked_at is None:
            detail = self._detail
        else:
            stamp = self._checked_at.strftime("%H:%M:%S")
            detail = f"{self._detail} — {stamp}"
        self.detail_item.set_label(detail)

        if not initial:
            log.info("%s | %s", label, self._detail)

    def _notify(self, title: str, body: str, icon_name: str) -> None:
        if not self._notify_ready:
            return
        notification = Notify.Notification.new(title, body, _icon_path(icon_name))
        notification.set_timeout(6000)
        notification.show()

    def _maybe_notify(self, previous: Status, current: Status) -> None:
        if not self.settings.notify_on_change:
            return
        if current == Status.UNKNOWN:
            return
        if previous == current:
            return
        if self._last_notified == current:
            return
        if previous == Status.UNKNOWN and self._last_notified is None:
            self._last_notified = current
            return

        self._notify(
            t(self.lang, "status_notify_title"),
            self._label_for(current),
            ICON_BY_STATUS[current],
        )
        self._last_notified = current


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    verbose = "--verbose" in argv or "-v" in argv

    configure_logging(verbose=verbose)

    instance = SingleInstance(LOCK_PATH)
    if not instance.acquire():
        settings = load_settings()
        log.error(t(settings.language, "already_running"))
        return 1

    def _shutdown(*_args: object) -> None:
        def _quit() -> bool:
            instance.release()
            if Notify.is_initted():
                Notify.uninit()
            Gtk.main_quit()
            return False

        GLib.idle_add(_quit)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        settings = load_settings()
        app = ShecanIndicator(settings)
        app.start()
    finally:
        instance.release()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
