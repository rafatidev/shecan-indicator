# Shecan Indicator

<p align="center">
  <img src="gnome-extension/icons/shecan-connected.png" alt="Shecan connected" width="64" height="64" />
</p>

<p align="center">
  <strong>GNOME panel indicator for Shecan DNS</strong><br/>
  وضعیت اتصال به شکن را در پنل گنوم نشان می‌دهد
</p>

<p align="center">
  <a href="#english">English</a> · <a href="#فارسی">فارسی</a>
</p>

---

<a id="english"></a>

## English

Monitor whether you are connected to [Shecan](https://shecan.ir) DNS, update your authorized IP via DDNS, and open the Shecan panel — all from the GNOME top bar.

### Features

- Live status from `https://check.shecan.ir/` (response `2` = connected)
- Green / red / gray tray icons
- Configurable check interval
- Icon-only or icon + custom text
- Persian & English UI
- One-click **Update Shecan IP** (your personal DDNS URL)
- Shortcut to [Shecan panel](https://my.shecan.ir/panel/)
- Desktop notifications

### Two packages in this repo

| Package | Path | Use when |
|--------|------|----------|
| **GNOME Shell Extension** | `gnome-extension/` | Publishing on [extensions.gnome.org](https://extensions.gnome.org/) |
| **AppIndicator (Python)** | `shecan_indicator/` | Tray app via AppIndicator on Ubuntu/GNOME |

### Install — GNOME Shell Extension (recommended)

1. Download / build the zip:

```bash
cd gnome-extension
zip -r ../shecan-indicator@rafatidev.shell-extension.zip . \
  -x '*.git*' -x '*~'
```

2. Install:

```bash
gnome-extensions install --force shecan-indicator@rafatidev.shell-extension.zip
# Log out and back in (or restart GNOME Shell on X11: Alt+F2 → r)
gnome-extensions enable shecan-indicator@rafatidev
```

Or open **Extensions** app → install from zip → enable **Shecan Indicator**.

### Install — AppIndicator (Python)

```bash
./install.sh
```

Requirements (pulled in by the script if missing): `python3-gi`, `gir1.2-appindicator3-0.1`, `gir1.2-notify-0.7`, AppIndicator GNOME extension.

### Configuration

- **Extension:** right-click / menu → Settings, or GNOME Extensions preferences  
- **AppIndicator:** menu → Settings…

You can set:

- UI language (فارسی / English)
- Poll interval
- Label texts
- Personal DDNS update URL, e.g. `https://ddns.shecan.ir/update?password=YOUR_TOKEN`

> Keep your DDNS token private. It is stored only in local settings.

### License

[GPL-2.0-or-later](LICENSE)

### Links

- Panel: https://my.shecan.ir/panel/
- Check endpoint: https://check.shecan.ir/
- Author: [rafatidev](https://github.com/rafatidev)

---

<a id="فارسی"></a>

## فارسی

با این ابزار می‌توانی از نوار بالای گنوم ببینی به DNS شکن وصل هستی یا نه، آی‌پی مجاز را با یک کلیک به‌روز کنی، و پنل شکن را باز کنی.

### امکانات

- بررسی زنده از `https://check.shecan.ir/` (پاسخ `2` یعنی متصل)
- آیکون سبز / قرمز / خاکستری
- تنظیم بازهٔ بررسی
- فقط آیکون یا آیکون + متن دلخواه
- رابط فارسی و انگلیسی
- **به‌روزرسانی آی‌پی شکن** با لینک اختصاصی DDNS
- میانبر [پنل شکن](https://my.shecan.ir/panel/)
- اعلان دسکتاپ

### دو بخش در این ریپو

| بسته | مسیر | کاربرد |
|------|------|--------|
| **اکستنشن گنوم** | `gnome-extension/` | انتشار در [extensions.gnome.org](https://extensions.gnome.org/) |
| **AppIndicator (پایتون)** | `shecan_indicator/` | آیکون سینی در اوبونتو/گنوم |

### نصب — اکستنشن گنوم (پیشنهادی)

```bash
cd gnome-extension
zip -r ../shecan-indicator@rafatidev.shell-extension.zip . \
  -x '*.git*' -x '*~'
gnome-extensions install --force shecan-indicator@rafatidev.shell-extension.zip
# یک‌بار خارج و دوباره وارد شوید
gnome-extensions enable shecan-indicator@rafatidev
```

### نصب — AppIndicator

```bash
./install.sh
```

### تنظیمات

در منوی آیکون → تنظیمات می‌توانی زبان، بازهٔ زمانی، متن‌ها و لینک DDNS شخصی را وارد کنی.

> توکن DDNS را عمومی نکن؛ فقط در تنظیمات محلی ذخیره می‌شود.

### مجوز

[GPL-2.0-or-later](LICENSE)

### لینک‌ها

- پنل: https://my.shecan.ir/panel/
- اندپوینت چک: https://check.shecan.ir/
- نویسنده: [rafatidev](https://github.com/rafatidev)
