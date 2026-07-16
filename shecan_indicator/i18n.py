from __future__ import annotations

from typing import Dict

STRINGS: Dict[str, Dict[str, str]] = {
    "fa": {
        "app_name": "شکن",
        "settings_title": "تنظیمات شکن",
        "language": "زبان رابط:",
        "lang_fa": "فارسی",
        "lang_en": "English",
        "interval": "بازهٔ بررسی (ثانیه):",
        "display_mode": "حالت نمایش:",
        "mode_icon": "فقط آیکون",
        "mode_label": "آیکون + متن",
        "labels_hint": "متن کنار آیکون:",
        "label_connected": "وقتی متصل است:",
        "label_disconnected": "وقتی قطع است:",
        "label_unknown": "در حال بررسی:",
        "notify_on_change": "اعلان هنگام تغییر وضعیت",
        "ddns_section": "به‌روزرسانی آی‌پی (لینک اختصاصی):",
        "ddns_hint": "لینک DDNS شکن را اینجا بگذارید (شامل password شما).",
        "ddns_placeholder": "https://ddns.shecan.ir/update?password=…",
        "cancel": "انصراف",
        "save": "ذخیره",
        "refresh": "بررسی دوباره",
        "update_ip": "به‌روزرسانی آی‌پی شکن",
        "open_panel": "باز کردن پنل شکن",
        "settings": "تنظیمات…",
        "quit": "خروج",
        "checking": "در حال بررسی…",
        "not_checked": "هنوز بررسی نشده",
        "status_notify_title": "وضعیت شکن",
        "ip_notify_title": "به‌روزرسانی آی‌پی شکن",
        "ip_updating": "در حال به‌روزرسانی آی‌پی…",
        "ip_missing_url": "ابتدا لینک به‌روزرسانی آی‌پی را در تنظیمات وارد کنید.",
        "ip_success": "آی‌پی مجاز شد:\n{body}",
        "ip_error": "به‌روزرسانی ناموفق:\n{body}",
        "default_connected": "متصل",
        "default_disconnected": "قطع",
        "default_unknown": "…",
        "detail_ok": "پاسخ: {raw} (HTTP {code})",
        "detail_unexpected": "پاسخ غیرمنتظره: {raw!r} (HTTP {code})",
        "detail_http": "خطای HTTP {code}",
        "detail_unreachable": "عدم دسترسی: {error}",
        "title_prefix": "شکن: {label}",
        "already_running": "نمونه‌ی دیگری از Shecan Indicator در حال اجراست.",
        "settings_saved": "تنظیمات ذخیره شد: interval={interval}s show_label={show_label}",
    },
    "en": {
        "app_name": "Shecan",
        "settings_title": "Shecan Settings",
        "language": "UI language:",
        "lang_fa": "فارسی",
        "lang_en": "English",
        "interval": "Check interval (seconds):",
        "display_mode": "Display mode:",
        "mode_icon": "Icon only",
        "mode_label": "Icon + text",
        "labels_hint": "Tray label text:",
        "label_connected": "When connected:",
        "label_disconnected": "When disconnected:",
        "label_unknown": "While checking:",
        "notify_on_change": "Notify on status change",
        "ddns_section": "IP update (personal link):",
        "ddns_hint": "Paste your Shecan DDNS update URL (includes your password).",
        "ddns_placeholder": "https://ddns.shecan.ir/update?password=…",
        "cancel": "Cancel",
        "save": "Save",
        "refresh": "Check again",
        "update_ip": "Update Shecan IP",
        "open_panel": "Open Shecan panel",
        "settings": "Settings…",
        "quit": "Quit",
        "checking": "Checking…",
        "not_checked": "Not checked yet",
        "status_notify_title": "Shecan status",
        "ip_notify_title": "Shecan IP update",
        "ip_updating": "Updating IP…",
        "ip_missing_url": "Set your IP update link in Settings first.",
        "ip_success": "IP authorized:\n{body}",
        "ip_error": "Update failed:\n{body}",
        "default_connected": "Connected",
        "default_disconnected": "Disconnected",
        "default_unknown": "…",
        "detail_ok": "Response: {raw} (HTTP {code})",
        "detail_unexpected": "Unexpected response: {raw!r} (HTTP {code})",
        "detail_http": "HTTP error {code}",
        "detail_unreachable": "Unreachable: {error}",
        "title_prefix": "Shecan: {label}",
        "already_running": "Another Shecan Indicator instance is already running.",
        "settings_saved": "Settings saved: interval={interval}s show_label={show_label}",
    },
}

PANEL_URL = "https://my.shecan.ir/panel/"
DDNS_URL_PREFIX = "https://ddns.shecan.ir/"


def normalize_lang(lang: str) -> str:
    return "en" if str(lang).lower().startswith("en") else "fa"


def t(lang: str, key: str, **kwargs: object) -> str:
    lang = normalize_lang(lang)
    text = STRINGS.get(lang, STRINGS["fa"]).get(key) or STRINGS["fa"].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
