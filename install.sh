#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${HOME}/.local"
BIN_DIR="${PREFIX}/bin"
APP_DIR="${PREFIX}/share/shecan-indicator"
AUTOSTART_DIR="${HOME}/.config/autostart"
ICON_DIR="${PREFIX}/share/icons/hicolor/scalable/apps"
DESKTOP_DIR="${PREFIX}/share/applications"

echo "==> نصب وابستگی‌های سیستم (در صورت نیاز)…"
MISSING=()
python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" 2>/dev/null || MISSING+=("python3-gi")
python3 -c "import gi; gi.require_version('AppIndicator3','0.1'); from gi.repository import AppIndicator3" 2>/dev/null || MISSING+=("gir1.2-appindicator3-0.1")
python3 -c "import gi; gi.require_version('Notify','0.7'); from gi.repository import Notify" 2>/dev/null || MISSING+=("gir1.2-notify-0.7")

if ((${#MISSING[@]})); then
  echo "بسته‌های زیر لازم هستند: ${MISSING[*]}"
  echo "در حال نصب با apt…"
  sudo apt-get update
  sudo apt-get install -y python3-gi gir1.2-appindicator3-0.1 gir1.2-notify-0.7 gnome-shell-extension-appindicator
fi

echo "==> کپی فایل‌ها…"
mkdir -p "${BIN_DIR}" "${APP_DIR}" "${AUTOSTART_DIR}" "${ICON_DIR}" "${DESKTOP_DIR}"

rsync -a --delete \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "${ROOT}/shecan_indicator/" "${APP_DIR}/shecan_indicator/"

install -m 755 /dev/null "${BIN_DIR}/shecan-indicator"
cat > "${BIN_DIR}/shecan-indicator" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${APP_DIR}\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m shecan_indicator "\$@"
EOF
chmod 755 "${BIN_DIR}/shecan-indicator"

install -m 644 "${ROOT}/shecan_indicator/icons/shecan-connected.svg" "${ICON_DIR}/shecan-connected.svg"
install -m 644 "${ROOT}/packaging/shecan-indicator.desktop" "${DESKTOP_DIR}/shecan-indicator.desktop"
sed -i "s|^Exec=.*|Exec=${BIN_DIR}/shecan-indicator|" "${DESKTOP_DIR}/shecan-indicator.desktop"
sed -i "s|^Icon=.*|Icon=${APP_DIR}/shecan_indicator/icons/shecan-connected.png|" "${DESKTOP_DIR}/shecan-indicator.desktop"

install -m 644 "${DESKTOP_DIR}/shecan-indicator.desktop" "${AUTOSTART_DIR}/shecan-indicator.desktop"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "${PREFIX}/share/icons/hicolor" >/dev/null 2>&1 || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${DESKTOP_DIR}" >/dev/null 2>&1 || true
fi

# Ensure PATH includes ~/.local/bin for this and future shells.
case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *)
    for rc in "${HOME}/.bashrc" "${HOME}/.profile"; do
      if [[ -f "${rc}" ]] && ! grep -qF '.local/bin' "${rc}"; then
        printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "${rc}"
        echo "==> ${BIN_DIR} به PATH در ${rc} اضافه شد."
        break
      fi
    done
    export PATH="${BIN_DIR}:${PATH}"
    ;;
esac

echo "==> راه‌اندازی ایندیکاتور…"
pkill -f '[p]ython3 -m shecan_indicator' >/dev/null 2>&1 || true
sleep 0.3
nohup "${BIN_DIR}/shecan-indicator" >/tmp/shecan-indicator.log 2>&1 &

echo
echo "نصب انجام شد."
echo "  اجرا:           shecan-indicator"
echo "  تنظیمات:        از منوی آیکون → تنظیمات…"
echo "  فایل تنظیمات:   ${HOME}/.config/shecan-indicator/config.json"
echo "  لاگ:            /tmp/shecan-indicator.log"
echo "  شروع خودکار:    فعال (${AUTOSTART_DIR}/shecan-indicator.desktop)"
echo
echo "اگر آیکون را در نوار بالا نمی‌بینی، مطمئن شو افزونه‌ی AppIndicator فعال است:"
echo "  gnome-extensions enable ubuntu-appindicators@ubuntu.com"
echo "  یا: gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com"
