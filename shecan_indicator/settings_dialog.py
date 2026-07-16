from __future__ import annotations

from typing import Callable, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .config import MAX_INTERVAL_SEC, MIN_INTERVAL_SEC, Settings
from .i18n import normalize_lang, t


class SettingsDialog(Gtk.Dialog):
    def __init__(
        self,
        parent: Optional[Gtk.Window],
        settings: Settings,
        on_save: Callable[[Settings], None],
    ) -> None:
        self._lang = normalize_lang(settings.language)
        self._on_save = on_save
        self._settings = settings

        super().__init__(title=t(self._lang, "settings_title"), transient_for=parent, flags=0)
        self.set_modal(True)
        self.set_default_size(480, 520)
        self.set_border_width(12)

        self._cancel_btn = self.add_button(t(self._lang, "cancel"), Gtk.ResponseType.CANCEL)
        self._save_btn = self.add_button(t(self._lang, "save"), Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.get_content_area().pack_start(self._content, True, True, 0)

        self._build_form()
        self.connect("response", self._on_response)
        self.show_all()

    def _apply_direction(self) -> None:
        direction = (
            Gtk.TextDirection.RTL if self._lang == "fa" else Gtk.TextDirection.LTR
        )
        self.get_content_area().set_direction(direction)
        self._content.set_direction(direction)
        if hasattr(self, "_grid"):
            self._grid.set_direction(direction)

    def _clear_content(self) -> None:
        for child in list(self._content.get_children()):
            self._content.remove(child)

    def _build_form(self) -> None:
        self._clear_content()
        self.set_title(t(self._lang, "settings_title"))
        self._cancel_btn.set_label(t(self._lang, "cancel"))
        self._save_btn.set_label(t(self._lang, "save"))
        self._apply_direction()

        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        grid.set_hexpand(True)
        self._grid = grid
        self._content.pack_start(grid, True, True, 0)
        self._apply_direction()

        row = 0
        align = 1.0 if self._lang == "fa" else 0.0

        lbl_lang = Gtk.Label(label=t(self._lang, "language"), xalign=align)
        self.lang_fa = Gtk.RadioButton.new_with_label(None, t(self._lang, "lang_fa"))
        self.lang_en = Gtk.RadioButton.new_with_label_from_widget(
            self.lang_fa, t(self._lang, "lang_en")
        )
        if self._lang == "en":
            self.lang_en.set_active(True)
        else:
            self.lang_fa.set_active(True)
        lang_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        lang_box.pack_start(self.lang_fa, False, False, 0)
        lang_box.pack_start(self.lang_en, False, False, 0)
        grid.attach(lbl_lang, 0, row, 1, 1)
        grid.attach(lang_box, 1, row, 1, 1)
        row += 1

        self.lang_fa.connect("toggled", self._on_language_toggled)
        self.lang_en.connect("toggled", self._on_language_toggled)

        lbl_interval = Gtk.Label(label=t(self._lang, "interval"), xalign=align)
        self.interval = Gtk.SpinButton.new_with_range(
            MIN_INTERVAL_SEC, MAX_INTERVAL_SEC, 1
        )
        self.interval.set_value(self._settings.poll_interval_sec)
        self.interval.set_hexpand(True)
        grid.attach(lbl_interval, 0, row, 1, 1)
        grid.attach(self.interval, 1, row, 1, 1)
        row += 1

        lbl_mode = Gtk.Label(label=t(self._lang, "display_mode"), xalign=align)
        self.mode_icon = Gtk.RadioButton.new_with_label(None, t(self._lang, "mode_icon"))
        self.mode_label = Gtk.RadioButton.new_with_label_from_widget(
            self.mode_icon, t(self._lang, "mode_label")
        )
        if self._settings.show_label:
            self.mode_label.set_active(True)
        else:
            self.mode_icon.set_active(True)
        mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        mode_box.pack_start(self.mode_icon, False, False, 0)
        mode_box.pack_start(self.mode_label, False, False, 0)
        grid.attach(lbl_mode, 0, row, 1, 1)
        grid.attach(mode_box, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 2, 1)
        row += 1

        hint = Gtk.Label(label=t(self._lang, "labels_hint"), xalign=align)
        grid.attach(hint, 0, row, 2, 1)
        row += 1

        self.text_connected = self._add_text_row(
            grid, row, t(self._lang, "label_connected"), self._settings.label_connected, align
        )
        row += 1
        self.text_disconnected = self._add_text_row(
            grid,
            row,
            t(self._lang, "label_disconnected"),
            self._settings.label_disconnected,
            align,
        )
        row += 1
        self.text_unknown = self._add_text_row(
            grid, row, t(self._lang, "label_unknown"), self._settings.label_unknown, align
        )
        row += 1

        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 2, 1)
        row += 1

        ddns_title = Gtk.Label(label=t(self._lang, "ddns_section"), xalign=align)
        grid.attach(ddns_title, 0, row, 2, 1)
        row += 1

        ddns_hint = Gtk.Label(label=t(self._lang, "ddns_hint"), xalign=align)
        ddns_hint.set_line_wrap(True)
        ddns_hint.set_max_width_chars(42)
        grid.attach(ddns_hint, 0, row, 2, 1)
        row += 1

        self.ddns_entry = Gtk.Entry()
        self.ddns_entry.set_text(self._settings.ddns_update_url)
        self.ddns_entry.set_placeholder_text(t(self._lang, "ddns_placeholder"))
        self.ddns_entry.set_visibility(False)
        self.ddns_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.ddns_entry.set_hexpand(True)
        grid.attach(self.ddns_entry, 0, row, 2, 1)
        row += 1

        self.show_ddns = Gtk.CheckButton(
            label="Show link" if self._lang == "en" else "نمایش لینک"
        )
        self.show_ddns.connect("toggled", self._on_toggle_ddns_visibility)
        grid.attach(self.show_ddns, 0, row, 2, 1)
        row += 1

        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 2, 1)
        row += 1

        self.notify = Gtk.CheckButton(label=t(self._lang, "notify_on_change"))
        self.notify.set_active(self._settings.notify_on_change)
        grid.attach(self.notify, 0, row, 2, 1)

        self.mode_icon.connect("toggled", self._sync_text_sensitivity)
        self._sync_text_sensitivity()
        self.show_all()

    def _on_language_toggled(self, button: Gtk.RadioButton) -> None:
        if not button.get_active():
            return
        new_lang = "en" if self.lang_en.get_active() else "fa"
        if new_lang == self._lang:
            return
        # Preserve current form values before rebuild.
        self._settings = self._collect(preview_lang=new_lang)
        self._lang = new_lang
        self._build_form()

    def _on_toggle_ddns_visibility(self, button: Gtk.CheckButton) -> None:
        self.ddns_entry.set_visibility(button.get_active())

    def _add_text_row(
        self, grid: Gtk.Grid, row: int, title: str, value: str, align: float
    ) -> Gtk.Entry:
        label = Gtk.Label(label=title, xalign=align)
        entry = Gtk.Entry()
        entry.set_text(value)
        if self._lang == "fa":
            entry.set_direction(Gtk.TextDirection.RTL)
            entry.set_alignment(1.0)
        else:
            entry.set_direction(Gtk.TextDirection.LTR)
            entry.set_alignment(0.0)
        entry.set_hexpand(True)
        entry.set_max_length(32)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(entry, 1, row, 1, 1)
        return entry

    def _sync_text_sensitivity(self, *_args: object) -> None:
        enabled = self.mode_label.get_active()
        for widget in (self.text_connected, self.text_disconnected, self.text_unknown):
            widget.set_sensitive(enabled)

    def _collect(self, preview_lang: Optional[str] = None) -> Settings:
        lang = preview_lang or ("en" if self.lang_en.get_active() else "fa")
        return Settings(
            language=lang,
            poll_interval_sec=int(self.interval.get_value()),
            show_label=self.mode_label.get_active(),
            label_connected=self.text_connected.get_text(),
            label_disconnected=self.text_disconnected.get_text(),
            label_unknown=self.text_unknown.get_text(),
            notify_on_change=self.notify.get_active(),
            ddns_update_url=self.ddns_entry.get_text(),
        ).clamp()

    def _on_response(self, _dialog: Gtk.Dialog, response: int) -> None:
        if response == Gtk.ResponseType.OK:
            self._on_save(self._collect())
        self.destroy()
