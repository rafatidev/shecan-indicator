#!/usr/bin/env bash
set -euo pipefail

PREFIX="${HOME}/.local"
BIN_DIR="${PREFIX}/bin"
APP_DIR="${PREFIX}/share/shecan-indicator"
AUTOSTART_DIR="${HOME}/.config/autostart"
ICON_DIR="${PREFIX}/share/icons/hicolor/scalable/apps"
DESKTOP_DIR="${PREFIX}/share/applications"

echo "==> توقف فرآیند…"
pkill -f '[p]ython3 -m shecan_indicator' >/dev/null 2>&1 || true

echo "==> حذف فایل‌ها…"
rm -f "${BIN_DIR}/shecan-indicator"
rm -rf "${APP_DIR}"
rm -f "${AUTOSTART_DIR}/shecan-indicator.desktop"
rm -f "${DESKTOP_DIR}/shecan-indicator.desktop"
rm -f "${ICON_DIR}/shecan-connected.svg"
rm -f "${HOME}/.cache/shecan-indicator.lock" 2>/dev/null || true

RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
rm -f "${RUNTIME_DIR}/shecan-indicator.lock" 2>/dev/null || true

echo "حذف انجام شد."
