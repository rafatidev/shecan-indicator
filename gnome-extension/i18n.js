/* Shecan Indicator — bilingual strings */

export const PANEL_URL = 'https://my.shecan.ir/panel/';
export const CHECK_URL = 'https://check.shecan.ir/';
export const CONNECTED_BODY = '2';
export const DDNS_PREFIX = 'https://ddns.shecan.ir/';

const STRINGS = {
    fa: {
        connected: 'متصل',
        disconnected: 'قطع',
        unknown: '…',
        refresh: 'بررسی دوباره',
        updateIp: 'به‌روزرسانی آی‌پی شکن',
        openPanel: 'باز کردن پنل شکن',
        settings: 'تنظیمات',
        statusTitle: 'وضعیت شکن',
        ipTitle: 'به‌روزرسانی آی‌پی شکن',
        ipUpdating: 'در حال به‌روزرسانی آی‌پی…',
        ipMissing: 'ابتدا لینک به‌روزرسانی آی‌پی را در تنظیمات وارد کنید.',
        ipSuccess: 'آی‌پی مجاز شد:',
        ipError: 'به‌روزرسانی ناموفق:',
    },
    en: {
        connected: 'Connected',
        disconnected: 'Disconnected',
        unknown: '…',
        refresh: 'Check again',
        updateIp: 'Update Shecan IP',
        openPanel: 'Open Shecan panel',
        settings: 'Settings',
        statusTitle: 'Shecan status',
        ipTitle: 'Shecan IP update',
        ipUpdating: 'Updating IP…',
        ipMissing: 'Set your IP update link in Settings first.',
        ipSuccess: 'IP authorized:',
        ipError: 'Update failed:',
    },
};

export function normalizeLang(lang) {
    return String(lang || 'fa').toLowerCase().startsWith('en') ? 'en' : 'fa';
}

export function t(lang, key) {
    const l = normalizeLang(lang);
    return STRINGS[l][key] || STRINGS.fa[key] || key;
}

export function isValidDdnsUrl(url) {
    if (!url || typeof url !== 'string')
        return false;
    const trimmed = url.trim();
    return trimmed.startsWith(DDNS_PREFIX);
}
