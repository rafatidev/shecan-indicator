import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import Clutter from 'gi://Clutter';
import Soup from 'gi://Soup';
import St from 'gi://St';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import {Extension, gettext as _} from 'resource:///org/gnome/shell/extensions/extension.js';

import {
    CHECK_URL,
    CONNECTED_BODY,
    PANEL_URL,
    isValidDdnsUrl,
    normalizeLang,
    t,
} from './i18n.js';

const Status = {
    UNKNOWN: 'unknown',
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected',
};

const ShecanIndicator = GObject.registerClass(
class ShecanIndicator extends PanelMenu.Button {
    _init(extension) {
        super._init(0.0, 'Shecan Indicator', false);
        this._ext = extension;
        this._settings = extension.getSettings();
        this._session = new Soup.Session({timeout: 10});
        this._status = Status.UNKNOWN;
        this._timerId = 0;
        this._lastNotified = null;
        this._checking = false;
        this._updatingIp = false;

        this._icon = new St.Icon({
            style_class: 'system-status-icon',
            icon_size: 16,
        });
        this._label = new St.Label({
            text: '',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'shecan-indicator-label',
        });

        const box = new St.BoxLayout({style_class: 'panel-status-menu-box'});
        box.add_child(this._icon);
        box.add_child(this._label);
        this.add_child(box);

        this._statusItem = new PopupMenu.PopupMenuItem('', {reactive: false});
        this._detailItem = new PopupMenu.PopupMenuItem('', {reactive: false});
        this.menu.addMenuItem(this._statusItem);
        this.menu.addMenuItem(this._detailItem);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this._refreshItem = new PopupMenu.PopupMenuItem('');
        this._refreshItem.connect('activate', () => this._checkStatus());
        this.menu.addMenuItem(this._refreshItem);

        this._updateIpItem = new PopupMenu.PopupMenuItem('');
        this._updateIpItem.connect('activate', () => this._updateIp());
        this.menu.addMenuItem(this._updateIpItem);

        this._panelItem = new PopupMenu.PopupMenuItem('');
        this._panelItem.connect('activate', () => {
            Gio.AppInfo.launch_default_for_uri(PANEL_URL, null);
        });
        this.menu.addMenuItem(this._panelItem);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this._settingsItem = new PopupMenu.PopupMenuItem('');
        this._settingsItem.connect('activate', () => this._ext.openPreferences());
        this.menu.addMenuItem(this._settingsItem);

        this._settingsChangedId = this._settings.connect('changed', () => {
            this._relabel();
            this._applyUi();
            this._armTimer();
        });

        this._relabel();
        this._applyUi();
        this._armTimer();
        this._checkStatus();
    }

    get _lang() {
        return normalizeLang(this._settings.get_string('language'));
    }

    _iconFile(status) {
        const name = {
            [Status.CONNECTED]: 'shecan-connected.png',
            [Status.DISCONNECTED]: 'shecan-disconnected.png',
            [Status.UNKNOWN]: 'shecan-unknown.png',
        }[status];
        return Gio.File.new_for_path(`${this._ext.path}/icons/${name}`);
    }

    _relabel() {
        const lang = this._lang;
        this._refreshItem.label.text = t(lang, 'refresh');
        this._updateIpItem.label.text = t(lang, 'updateIp');
        this._panelItem.label.text = t(lang, 'openPanel');
        this._settingsItem.label.text = t(lang, 'settings');
    }

    _statusLabel(status) {
        if (status === Status.CONNECTED)
            return this._settings.get_string('label-connected') || t(this._lang, 'connected');
        if (status === Status.DISCONNECTED)
            return this._settings.get_string('label-disconnected') || t(this._lang, 'disconnected');
        return this._settings.get_string('label-unknown') || t(this._lang, 'unknown');
    }

    _applyUi(detailText = null) {
        const label = this._statusLabel(this._status);
        this._statusItem.label.text = label;
        if (detailText !== null)
            this._detailItem.label.text = detailText;

        const file = this._iconFile(this._status);
        this._icon.gicon = new Gio.FileIcon({file});

        if (this._settings.get_boolean('show-label'))
            this._label.text = label;
        else
            this._label.text = '';
    }

    _armTimer() {
        if (this._timerId) {
            GLib.source_remove(this._timerId);
            this._timerId = 0;
        }
        const sec = Math.max(3, this._settings.get_int('poll-interval-sec'));
        this._timerId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, sec, () => {
            this._checkStatus();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _httpGet(url, timeoutSec = 10) {
        return new Promise((resolve, reject) => {
            const message = Soup.Message.new('GET', url);
            if (!message) {
                reject(new Error('Invalid URL'));
                return;
            }
            message.request_headers.append('Cache-Control', 'no-cache');
            this._session.timeout = timeoutSec;
            this._session.send_and_read_async(
                message,
                GLib.PRIORITY_DEFAULT,
                null,
                (session, result) => {
                    try {
                        const bytes = session.send_and_read_finish(result);
                        const status = message.get_status();
                        const body = new TextDecoder().decode(bytes.get_data()).trim();
                        resolve({status, body});
                    } catch (e) {
                        reject(e);
                    }
                }
            );
        });
    }

    async _checkStatus() {
        if (this._checking)
            return;
        this._checking = true;
        const previous = this._status;
        try {
            const {status, body} = await this._httpGet(CHECK_URL, 5);
            const ok = status >= 200 && status < 300 && body === CONNECTED_BODY;
            this._status = ok ? Status.CONNECTED : Status.DISCONNECTED;
            const stamp = GLib.DateTime.new_now_local().format('%H:%M:%S');
            this._applyUi(`${body || status} — ${stamp}`);
            this._maybeNotify(previous, this._status);
        } catch (e) {
            this._status = Status.DISCONNECTED;
            this._applyUi(String(e.message || e));
            this._maybeNotify(previous, this._status);
        } finally {
            this._checking = false;
        }
    }

    _notify(title, body) {
        Main.notify(title, body);
    }

    _maybeNotify(previous, current) {
        if (!this._settings.get_boolean('notify-on-change'))
            return;
        if (current === Status.UNKNOWN)
            return;
        if (previous === current)
            return;
        if (this._lastNotified === current)
            return;
        if (previous === Status.UNKNOWN && this._lastNotified === null) {
            this._lastNotified = current;
            return;
        }
        this._notify(t(this._lang, 'statusTitle'), this._statusLabel(current));
        this._lastNotified = current;
    }

    async _updateIp() {
        if (this._updatingIp)
            return;
        const url = (this._settings.get_string('ddns-update-url') || '').trim();
        if (!isValidDdnsUrl(url)) {
            this._notify(t(this._lang, 'ipTitle'), t(this._lang, 'ipMissing'));
            return;
        }

        this._updatingIp = true;
        this._updateIpItem.setSensitive(false);
        this._notify(t(this._lang, 'ipTitle'), t(this._lang, 'ipUpdating'));
        try {
            const {status, body} = await this._httpGet(url, 15);
            if (status >= 200 && status < 300) {
                this._notify(
                    t(this._lang, 'ipTitle'),
                    `${t(this._lang, 'ipSuccess')}\n${body || status}`
                );
                this._checkStatus();
            } else {
                this._notify(
                    t(this._lang, 'ipTitle'),
                    `${t(this._lang, 'ipError')}\n${body || status}`
                );
            }
        } catch (e) {
            this._notify(
                t(this._lang, 'ipTitle'),
                `${t(this._lang, 'ipError')}\n${e.message || e}`
            );
        } finally {
            this._updatingIp = false;
            this._updateIpItem.setSensitive(true);
        }
    }

    destroy() {
        if (this._timerId) {
            GLib.source_remove(this._timerId);
            this._timerId = 0;
        }
        if (this._settingsChangedId) {
            this._settings.disconnect(this._settingsChangedId);
            this._settingsChangedId = 0;
        }
        if (this._session) {
            this._session.abort();
            this._session = null;
        }
        super.destroy();
    }
});

export default class ShecanExtension extends Extension {
    enable() {
        this._indicator = new ShecanIndicator(this);
        Main.panel.addToStatusArea(this.uuid, this._indicator);
    }

    disable() {
        this._indicator?.destroy();
        this._indicator = null;
    }
}
