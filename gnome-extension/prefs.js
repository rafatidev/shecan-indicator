import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gtk from 'gi://Gtk';
import {ExtensionPreferences, gettext as _} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

import {normalizeLang} from './i18n.js';

const UI = {
    fa: {
        page: 'شکن',
        language: 'زبان رابط',
        interval: 'بازهٔ بررسی (ثانیه)',
        showLabel: 'نمایش متن کنار آیکون',
        labelConnected: 'متن هنگام اتصال',
        labelDisconnected: 'متن هنگام قطع',
        labelUnknown: 'متن هنگام بررسی',
        notify: 'اعلان هنگام تغییر وضعیت',
        ddns: 'لینک به‌روزرسانی آی‌پی',
        ddnsHelp: 'مثال: https://ddns.shecan.ir/update?password=…',
    },
    en: {
        page: 'Shecan',
        language: 'UI language',
        interval: 'Check interval (seconds)',
        showLabel: 'Show text next to icon',
        labelConnected: 'Connected label',
        labelDisconnected: 'Disconnected label',
        labelUnknown: 'Checking label',
        notify: 'Notify on status change',
        ddns: 'IP update URL',
        ddnsHelp: 'Example: https://ddns.shecan.ir/update?password=…',
    },
};

export default class ShecanPrefs extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();
        window.set_default_size(520, 560);

        const build = () => {
            window.set_title('Shecan Indicator');
            // Remove previous pages if rebuilding
            const old = window._shecanPage;
            if (old)
                window.remove(old);

            const lang = normalizeLang(settings.get_string('language'));
            const u = UI[lang];
            const page = new Adw.PreferencesPage({title: u.page, icon_name: 'network-workgroup-symbolic'});
            window._shecanPage = page;

            const general = new Adw.PreferencesGroup();
            page.add(general);

            const langRow = new Adw.ComboRow({
                title: u.language,
                model: new Gtk.StringList({strings: ['فارسی', 'English']}),
            });
            langRow.selected = lang === 'en' ? 1 : 0;
            langRow.connect('notify::selected', () => {
                settings.set_string('language', langRow.selected === 1 ? 'en' : 'fa');
                build();
            });
            general.add(langRow);

            const interval = new Adw.SpinRow({
                title: u.interval,
                adjustment: new Gtk.Adjustment({
                    lower: 3,
                    upper: 3600,
                    step_increment: 1,
                    page_increment: 10,
                    value: settings.get_int('poll-interval-sec'),
                }),
            });
            settings.bind('poll-interval-sec', interval, 'value', Gio.SettingsBindFlags.DEFAULT);
            general.add(interval);

            const showLabel = new Adw.SwitchRow({title: u.showLabel});
            settings.bind('show-label', showLabel, 'active', Gio.SettingsBindFlags.DEFAULT);
            general.add(showLabel);

            const labels = new Adw.PreferencesGroup();
            page.add(labels);

            for (const [key, title] of [
                ['label-connected', u.labelConnected],
                ['label-disconnected', u.labelDisconnected],
                ['label-unknown', u.labelUnknown],
            ]) {
                const row = new Adw.EntryRow({title});
                row.text = settings.get_string(key);
                row.connect('changed', () => settings.set_string(key, row.text));
                labels.add(row);
            }

            const actions = new Adw.PreferencesGroup();
            page.add(actions);

            const notify = new Adw.SwitchRow({title: u.notify});
            settings.bind('notify-on-change', notify, 'active', Gio.SettingsBindFlags.DEFAULT);
            actions.add(notify);

            const ddns = new Adw.EntryRow({
                title: u.ddns,
                text: settings.get_string('ddns-update-url'),
            });
            // Keep sensitive value out of plain visible default if possible
            ddns.connect('changed', () => settings.set_string('ddns-update-url', ddns.text.trim()));
            actions.add(ddns);

            const help = new Adw.ActionRow({subtitle: u.ddnsHelp});
            actions.add(help);

            window.add(page);
        };

        build();
    }
}
