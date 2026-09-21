/** Versioned selection only. Prices and availability always come from the server. */
export const CART_KEY = 'zero-day:cafe-selection:v1';
export function normalizeLine(raw) {
    if (!raw || typeof raw !== 'object' || typeof raw.product_id !== 'string' || !raw.product_id || raw.product_id.length > 140) throw new Error('Selección inválida.');
    if (!Number.isInteger(raw.quantity) || raw.quantity < 1 || raw.quantity > 99) throw new Error('Elige una cantidad entre 1 y 99.');
    const clean = { product_id: raw.product_id, quantity: raw.quantity, options: {}, modifiers: {} };
    for (const kind of ['options', 'modifiers']) {
        const group = raw[kind] ?? {};
        if (!group || typeof group !== 'object' || Array.isArray(group) || Object.keys(group).length > 30) throw new Error('Opciones inválidas.');
        for (const key of Object.keys(group).sort((a, b) => a.localeCompare(b))) {
            if (['__proto__', 'constructor', 'prototype'].includes(key)) throw new Error('Opciones inválidas.');
            const value = group[key];
            if (kind === 'options') {
                if (typeof value !== 'string' || value.length > 140) throw new Error('Opción inválida.');
                if (value) clean[kind][key] = value;
            } else {
                if (!Array.isArray(value) || value.length > 30 || value.some(v => typeof v !== 'string' || v.length > 140)) throw new Error('Complementos inválidos.');
                if (value.length) clean[kind][key] = [...new Set(value)].sort((a, b) => a.localeCompare(b));
            }
        }
    }
    return clean;
}
export function lineKey(raw) {
    const { product_id, options, modifiers } = normalizeLine(raw);
    return JSON.stringify([product_id, options, modifiers]);
}
export function createCartStore(storage) {
    let lines = [], warning = '';
    const listeners = new Set();
    function read() {
        try {
            const saved = storage?.getItem(CART_KEY);
            if (!saved) { lines = []; return; }
            const data = JSON.parse(saved);
            if (data.version !== 1 || !Array.isArray(data.lines) || data.lines.length > 50) throw new Error();
            const parsed = data.lines.map(normalizeLine);
            if (new Set(parsed.map(lineKey)).size !== parsed.length) throw new Error();
            lines = parsed;
        } catch { lines = []; warning = 'No pudimos recuperar la selección guardada. Puedes empezar una nueva.'; }
    }
    const snapshot = () => lines.map(line => normalizeLine(line));
    function commit(next) {
        if (next.length > 50) throw new Error('Tu selección admite hasta 50 combinaciones.');
        lines = next.map(normalizeLine);
        try {
            if (!storage) throw new Error();
            storage.setItem(CART_KEY, JSON.stringify({ version: 1, lines }));
            warning = '';
        } catch { warning = 'La selección funciona en esta página, pero este navegador no permite guardarla.'; }
        listeners.forEach(fn => fn(snapshot()));
    }
    read();
    return {
        get: snapshot,
        warning: () => warning,
        subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
        sync() { read(); listeners.forEach(fn => fn(snapshot())); },
        add(raw, replaceKey = null) {
            const line = normalizeLine(raw);
            if (replaceKey && !lines.some(item => lineKey(item) === replaceKey)) throw new Error('Esta selección cambió. Vuelve al carrito para revisarla.');
            const next = lines.filter(item => !replaceKey || lineKey(item) !== replaceKey).map(normalizeLine);
            const existing = next.find(item => lineKey(item) === lineKey(line));
            if (existing) existing.quantity += line.quantity;
            else next.push(line);
            commit(next); // validate all quantities before accepting the new state
        },
        quantity(key, quantity) { commit(lines.map(line => lineKey(line) === key ? { ...line, quantity } : line)); },
        remove(key) { commit(lines.filter(line => lineKey(line) !== key)); },
        clear() { commit([]); },
    };
}
