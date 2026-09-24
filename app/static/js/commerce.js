import { cartStore } from './cart_indicator.js';
import { lineKey } from './modules/cart_store.js';

async function quote(items, signal) {
    const response = await fetch('/api/order/quote', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || '' },
        body: JSON.stringify({ items }), signal,
    });
    let data;
    try { data = await response.json(); } catch { throw new Error('No pudimos comprobar tu selección. Inténtalo de nuevo.'); }
    if (!response.ok) throw new Error(data.message || 'No pudimos comprobar tu selección.');
    return data;
}
function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}
function action(text, name, key, label) {
    const button = el('button', 'text-control', text);
    button.type = 'button'; button.dataset.action = name; button.dataset.key = key;
    if (label) button.setAttribute('aria-label', label);
    return button;
}
function validLine(result) {
    if (!result.lines[0]?.available) throw new Error(result.lines[0]?.error || 'Selección no disponible.');
}
function errorText(error) { return error instanceof TypeError ? 'No pudimos conectar. Tu selección sigue guardada; inténtalo de nuevo.' : error.message; }

function initQuickAdd() {
    const feedback = document.querySelector('[data-commerce-feedback]');
    document.querySelectorAll('[data-quick-add]').forEach(button => button.addEventListener('click', async () => {
        const line = { product_id: button.dataset.quickAdd, quantity: 1, options: {}, modifiers: {} };
        button.disabled = true;
        if (feedback) feedback.textContent = 'Comprobando tu selección…';
        try {
            const result = await quote([line]); validLine(result); cartStore.add(line);
            if (feedback) {
                feedback.replaceChildren(document.createTextNode(`${result.lines[0].name} añadido. ${cartStore.warning()} `));
                const link = el('a', 'cafe-link', 'Ver mi selección ↗'); link.href = '/carrito'; feedback.append(link);
            }
        } catch (error) { if (feedback) feedback.textContent = errorText(error); }
        finally { button.disabled = false; }
    }));
    if (feedback && cartStore.warning()) feedback.textContent = cartStore.warning();
}
function initProduct() {
    const form = document.querySelector('.product-order');
    if (!form) return;
    const feedback = form.querySelector('[data-order-feedback]');
    const button = form.querySelector('[data-add-button]');
    const price = document.querySelector('[data-product-price]');
    let editKey = new URLSearchParams(location.search).get('line');
    let pending = false, generation = 0;
    const stored = editKey && cartStore.get().find(line => lineKey(line) === editKey && line.product_id === form.dataset.productId);
    if (stored) {
        form.elements.quantity.value = stored.quantity;
        form.querySelectorAll('fieldset').forEach(group => {
            const value = stored[group.dataset.kind]?.[group.dataset.group];
            group.querySelectorAll('input').forEach(input => { input.checked = Array.isArray(value) ? value.includes(input.value) : (value || '') === input.value; });
        });
        button.textContent = 'Guardar los cambios ↗';
    } else if (editKey) { editKey = null; feedback.textContent = 'Esta selección ya no está en el carrito. Puedes añadirla de nuevo.'; }
    function read() {
        const line = { product_id: form.dataset.productId, quantity: Number(form.elements.quantity.value), options: {}, modifiers: {} };
        form.querySelectorAll('fieldset').forEach(group => {
            const values = [...group.querySelectorAll('input:checked')].map(input => input.value).filter(Boolean);
            if (group.dataset.required === 'true' && !values.length) throw new Error('Elige las opciones de tu selección.');
            if (values.length > Number(group.dataset.max)) throw new Error('Revisa la cantidad de complementos elegidos.');
            if (values.length) line[group.dataset.kind][group.dataset.group] = group.dataset.kind === 'options' ? values[0] : values;
        });
        return line;
    }
    form.addEventListener('change', async () => {
        if (pending) return;
        const ticket = ++generation;
        try {
            const result = await quote([read()]);
            if (ticket !== generation) return;
            validLine(result); price.textContent = result.lines[0].formatted_total; feedback.textContent = '';
        } catch (error) { if (ticket === generation) { price.textContent = form.dataset.basePrice; feedback.textContent = errorText(error); } }
    });
    form.addEventListener('submit', async event => {
        event.preventDefault(); if (pending || !form.reportValidity()) return;
        ++generation; pending = true; button.disabled = true;
        try {
            const line = read();
            form.querySelectorAll('fieldset').forEach(group => { group.disabled = true; });
            form.elements.quantity.disabled = true;
            const result = await quote([line]); validLine(result);
            cartStore.add(line, editKey); const edited = !!editKey; editKey = null;
            const url = new URL(location.href); url.searchParams.delete('line'); history.replaceState(null, '', url);
            feedback.textContent = `${edited ? 'Cambios guardados.' : 'Añadido a tu selección.'} ${cartStore.warning()}`;
            price.textContent = result.lines[0].formatted_total;
            button.textContent = 'Añadir otra selección ↗';
        } catch (error) { feedback.textContent = errorText(error); }
        finally {
            pending = false; button.disabled = false;
            form.querySelectorAll('fieldset').forEach(group => { group.disabled = false; });
            form.elements.quantity.disabled = false;
        }
    });
    if (stored) form.dispatchEvent(new Event('change'));
}
function initCart() {
    const root = document.querySelector('[data-cart-page]');
    if (!root) return;
    const list = root.querySelector('[data-cart-lines]');
    const subtotal = root.querySelector('[data-cart-subtotal]');
    const feedback = root.querySelector('[data-cart-feedback]');
    const note = root.querySelector('[data-cart-quote-note]');
    const retry = root.querySelector('[data-cart-retry]');
    let controller, generation = 0;
    const resolvedRows = new Map();
    function lineView(stored, row) {
        const key = lineKey(stored);
        const article = el('article', 'cart-line'); article.dataset.lineKey = key;
        const media = el('div', 'cart-line-media');
        if (row.image) {
            const image = el('img');
            image.src = row.slug === 'cold-brew' ? '/static/img/home/cold-brew-800.webp' : row.image;
            image.alt = ''; image.width = 160; image.height = 160; image.loading = 'lazy'; image.decoding = 'async';
            image.addEventListener('error', () => { image.remove(); media.textContent = 'ZD'; }, { once: true });
            media.append(image);
        } else { media.textContent = 'ZD'; }
        article.append(media);
        const copy = el('div', 'cart-line-copy');
        const title = el('h2', '', row.name);
        if (row.slug) { const link = el('a', '', row.name); link.href = `/producto/${encodeURIComponent(row.slug)}`; title.replaceChildren(link); }
        copy.append(title);
        if (row.selection_labels?.length) copy.append(el('p', 'cart-line-options', row.selection_labels.join(' · ')));
        if (!row.available) copy.append(el('p', 'cart-line-error', row.error || 'Comprobando disponibilidad…'));
        if (row.slug) {
            const edit = el('a', 'cart-edit', 'Editar selección ↗'); edit.href = `/producto/${encodeURIComponent(row.slug)}?line=${encodeURIComponent(key)}`; copy.append(edit);
        }
        const controls = el('div', 'cart-line-controls');
        const quantity = el('div', 'quantity-control');
        const minus = action('−', 'decrease', key, `Reducir cantidad de ${row.name}`); minus.disabled = stored.quantity <= 1;
        const plus = action('+', 'increase', key, `Aumentar cantidad de ${row.name}`); plus.disabled = stored.quantity >= 99;
        const input = el('input'); input.type = 'number'; input.min = '1'; input.max = '99'; input.inputMode = 'numeric'; input.value = stored.quantity;
        input.dataset.key = key; input.dataset.action = 'quantity'; input.setAttribute('aria-label', `Cantidad de ${row.name}`);
        quantity.append(minus, input, plus); controls.append(quantity, action('Quitar', 'remove', key, `Quitar ${row.name}`));
        const amount = el('div', 'cart-line-price', row.available ? row.formatted_total : '—');
        if (row.available) amount.append(el('small', '', `${row.formatted_unit} / unidad`));
        article.append(copy, controls, amount); return article;
    }
    async function render() {
        const ticket = ++generation; controller?.abort(); controller = new AbortController();
        const lines = cartStore.get();
        root.querySelector('[data-cart-empty]').hidden = lines.length > 0;
        root.querySelector('[data-cart-filled]').hidden = lines.length === 0;
        retry.hidden = true; feedback.textContent = cartStore.warning(); subtotal.textContent = '—';
        if (!lines.length) { list.replaceChildren(); resolvedRows.clear(); list.removeAttribute('aria-busy'); return; }
        list.setAttribute('aria-busy', 'true'); note.textContent = 'Comprobando tu selección…';
        // Keep quantities/removal available offline, without displaying stale prices.
        const previous = new Map([...list.children].map(node => [node.dataset.lineKey, node.querySelector('h2')?.textContent]));
        const focused = document.activeElement?.dataset;
        const focusKey = focused?.key, focusAction = focused?.action;
        const existing = new Map([...list.children].map(node => [node.dataset.lineKey, node]));
        const pending = lines.map(line => {
            const key = lineKey(line);
            const node = existing.get(key);
            if (!node) return lineView(line, { ...resolvedRows.get(key), name: resolvedRows.get(key)?.name || previous.get(key) || 'Tu selección', available: false, error: 'Comprobando disponibilidad…' });
            node.querySelector('[data-action="quantity"]').value = line.quantity;
            node.querySelector('[data-action="decrease"]').disabled = line.quantity <= 1;
            node.querySelector('[data-action="increase"]').disabled = line.quantity >= 99;
            node.querySelector('.cart-line-price').textContent = '—';
            return node;
        });
        [...list.children].forEach(node => { if (!pending.includes(node)) node.remove(); });
        pending.forEach((node, index) => { if (list.children[index] !== node) list.insertBefore(node, list.children[index] || null); });
        function restoreFocus() {
            if (!focusKey) return;
            const candidates = [...list.querySelectorAll('[data-key]')];
            (candidates.find(el => el.dataset.key === focusKey && el.dataset.action === focusAction) || candidates[0] || root.querySelector('[data-cart-clear]')).focus();
        }
        restoreFocus();
        try {
            const result = await quote(lines, controller.signal);
            if (ticket !== generation) return;
            lines.forEach((line, i) => resolvedRows.set(lineKey(line), result.lines[i]));
            list.replaceChildren(...lines.map((line, i) => lineView(line, result.lines[i])));
            subtotal.textContent = result.formatted_subtotal || '—';
            note.textContent = result.has_errors ? 'El subtotal incluye solo las selecciones disponibles. Revisa los elementos señalados.' : 'Opciones y cantidades incluidas.';
            if (list.contains(document.activeElement) || document.activeElement === document.body) restoreFocus();
        } catch (error) {
            if (error.name !== 'AbortError' && ticket === generation) {
                feedback.textContent = errorText(error); note.textContent = 'No se pudo actualizar el subtotal.'; retry.hidden = false;
                list.querySelectorAll('.cart-line-error').forEach(node => { node.textContent = 'No se pudo comprobar la disponibilidad.'; });
            }
        } finally { if (ticket === generation) list.removeAttribute('aria-busy'); }
    }
    function change(event) {
        const control = event.target.closest('[data-action]'); if (!control) return;
        const action = control.dataset.action;
        if ((action === 'quantity') !== (event.type === 'change')) return;
        const key = control.dataset.key, line = cartStore.get().find(line => lineKey(line) === key);
        if (!line) return;
        try {
            if (action === 'remove') cartStore.remove(key);
            else cartStore.quantity(key, action === 'quantity' ? Number(control.value) : line.quantity + (action === 'increase' ? 1 : -1));
        } catch (error) { feedback.textContent = errorText(error); if (action === 'quantity') control.value = line.quantity; }
    }
    list.addEventListener('click', change); list.addEventListener('change', change);
    root.querySelector('[data-cart-clear]').addEventListener('click', () => { cartStore.clear(); root.querySelector('[data-cart-empty] a').focus(); });
    retry.addEventListener('click', render);
    cartStore.subscribe(render); window.addEventListener('online', render);
    render();
}
function initCategoryNavigation() {
    const links = [...document.querySelectorAll('.menu-category-nav a[href^="#"]')];
    if (!links.length || !window.IntersectionObserver) return;
    const sections = [...document.querySelectorAll('.menu-chapter')];
    const observer = new IntersectionObserver(() => {
        // Observer entries are only the changed sections, not every visible section.
        const available = sections.filter(section => !section.hidden);
        const current = available.filter(section => section.getBoundingClientRect().top <= window.innerHeight * .45).at(-1) || available[0];
        links.forEach(link => {
            if (current && link.hash === `#${current.id}`) link.setAttribute('aria-current', 'location');
            else link.removeAttribute('aria-current');
        });
    }, { rootMargin: '-15% 0px -55% 0px' });
    sections.forEach(section => observer.observe(section));
}
initQuickAdd(); initProduct(); initCart(); initCategoryNavigation();
