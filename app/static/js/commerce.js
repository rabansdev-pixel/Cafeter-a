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
        const line = { product_id: button.dataset.quickAdd, quantity: 1, options: JSON.parse(button.dataset.standardOptions || '{}'), modifiers: {} };
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
function initProduct(scope = document, initialKey = null, onSaved = null) {
    const form = scope.querySelector('.product-order');
    if (!form) return;
    const feedback = form.querySelector('[data-order-feedback]');
    const button = form.querySelector('[data-add-button]');
    const price = scope.querySelector('[data-product-price]') || el('span');
    let editKey = initialKey || new URLSearchParams(location.search).get('line');
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
            if (onSaved) { onSaved(); return; }
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
    const whatsapp = root.querySelector('[data-cart-whatsapp]');
    const undo = root.querySelector('[data-cart-undo]');
    const editor = document.querySelector('[data-cart-editor]');
    let removed = null, message = '';
    editor.querySelector('[data-editor-close]').addEventListener('click', () => editor.close());
    list.addEventListener('click', async event => {
        const edit = event.target.closest('.cart-edit');
        if (!edit) return;
        event.preventDefault();
        const content = editor.querySelector('[data-editor-content]');
        content.textContent = 'Cargando…';
        editor.showModal();
        try {
            const response = await fetch(edit.href);
            if (!response.ok) throw new Error('No pudimos abrir las opciones.');
            const page = new DOMParser().parseFromString(await response.text(), 'text/html');
            const form = page.querySelector('.product-order');
            if (!form) throw new Error('Opciones no disponibles.');
            content.replaceChildren(el('h2', '', edit.closest('.cart-line').querySelector('h2').textContent), form);
            initProduct(content, new URL(edit.href).searchParams.get('line'), () => editor.close());
        } catch (error) { content.textContent = errorText(error); }
    });
    let inquiryPending = false;
    async function sendInquiry(redemption = null) {
        if (inquiryPending) return;
        inquiryPending = true;
        const tab = window.open('about:blank', '_blank');
        if (tab) tab.opener = null;
        try {
            const response = await fetch('/api/inquiries', {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('meta[name="csrf-token"]').content}, body:JSON.stringify(redemption ? {redemption} : {items:cartStore.get()})});
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'No pudimos guardar la consulta.');
            if (tab) tab.location.replace(data.url);
            else {
                const link = el('a', 'cafe-link', 'Abrir WhatsApp · ' + data.reference);
                link.href = data.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
                feedback.replaceChildren(link);
            }
        } catch (error) { tab?.close(); feedback.textContent = errorText(error); }
        finally { inquiryPending = false; }
    }
    whatsapp.addEventListener('click', () => {
        if (!couponSend.hidden && couponSend.dataset.redemption) sendInquiry(couponSend.dataset.redemption);
        else if (message && !whatsapp.disabled) sendInquiry();
    });
    undo.addEventListener('click', () => {
        if (!removed) return;
        try { cartStore.add(removed); removed = null; undo.hidden = true; }
        catch (error) { feedback.textContent = errorText(error); }
    });
    let controller, generation = 0;
    const couponCode = root.querySelector('#coupon-code');
    const couponFeedback = root.querySelector('[data-coupon-feedback]');
    const redeem = root.querySelector('[data-coupon-redeem]');
    const couponSend = root.querySelector('[data-coupon-send]');
    couponSend.addEventListener('click', event => { event.preventDefault(); if (couponSend.dataset.redemption) sendInquiry(couponSend.dataset.redemption); });
    const mobileBar = root.querySelector('[data-mobile-checkout]');
    const mobileButton = root.querySelector('[data-mobile-whatsapp]');
    const mobileTotal = root.querySelector('[data-mobile-total]');
    let redeemedTotal = '';
    function syncMobileCheckout() {
        const receipt = !couponSend.hidden && !!redeemedTotal;
        mobileBar.hidden = cartStore.get().length === 0 && !receipt;
        mobileTotal.textContent = receipt ? redeemedTotal : subtotal.textContent;
        root.querySelector('[data-mobile-total-label]').textContent = receipt ? 'Total del canje' : 'Total estimado';
        mobileButton.disabled = !receipt && whatsapp.disabled;
        mobileButton.textContent = receipt ? 'Enviar canje por WhatsApp' : 'Consultar por WhatsApp';
    }
    mobileButton.addEventListener('click', () => {
        if (!couponSend.hidden && redeemedTotal) couponSend.click();
        else whatsapp.click();
    });
    const suggestionsBlock = root.querySelector('[data-cart-suggestions]');
    const suggestionsPosition = document.createComment('suggestions position');
    suggestionsBlock.before(suggestionsPosition);
    const mobileMedia = matchMedia('(max-width:767px)');
    const positionSuggestions = () => {
        if (mobileMedia.matches) root.querySelector('.cart-summary').after(suggestionsBlock);
        else suggestionsPosition.after(suggestionsBlock);
    };
    mobileMedia.addEventListener('change', positionSuggestions);
    positionSuggestions();
    let couponVersion = 0, couponPending = false;
    function resetCoupon() {
        couponVersion++; redeem.disabled = true;
        couponFeedback.textContent = ''; couponSend.hidden = true; delete couponSend.dataset.redemption; redeemedTotal = ''; syncMobileCheckout();
    }
    couponCode.addEventListener('input', resetCoupon);
    async function couponAction(action) {
        if (couponPending) return;
        const version = couponVersion;
        couponPending = true;
        root.querySelectorAll('.cart-coupon button').forEach(button => button.disabled = true);
        try {
            const response = await fetch('/api/coupons/' + action, { method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('meta[name="csrf-token"]').content}, body:JSON.stringify({code:couponCode.value,items:cartStore.get()}) });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'No se pudo aplicar el cupón.');
            if (version !== couponVersion && !data.redemption) return;
            couponFeedback.textContent = `${data.label}: −${data.discount}. Total: ${data.total}.`;
            if (data.redemption) {
                couponFeedback.textContent += ` Canje: ${data.redemption}. El comprobante corresponde al carrito guardado al canjear.`;
                const text = ['Hola ZERO DAY, quiero consultar mi canje ' + data.redemption, ...data.lines.map(line => `${line.quantity} × ${line.name} (${line.options.join(', ')}) — ${line.total}`), `Cupón: ${data.code} · ${data.label}`, `Descuento: ${data.discount}`, `Total: ${data.total}`, 'Pendiente de confirmar disponibilidad.'].join('\n');
                couponSend.href = 'https://wa.me/593988357638?text=' + encodeURIComponent(text);
                couponSend.dataset.redemption = data.redemption;
                couponSend.hidden = false; redeemedTotal = data.total; syncMobileCheckout();
            } else redeem.disabled = false;
        } catch (error) { couponFeedback.textContent = errorText(error); }
        finally {
            couponPending = false;
            root.querySelector('[data-coupon-preview]').disabled = false;
            root.querySelector('[data-coupon-recover]').disabled = false;
        }
    }
    root.querySelector('[data-coupon-preview]').addEventListener('click', () => couponAction('preview'));
    redeem.addEventListener('click', () => couponAction('redeem'));
    root.querySelector('[data-coupon-recover]').addEventListener('click', () => couponAction('receipt'));
    const resolvedRows = new Map();
    function lineView(stored, row) {
        const key = lineKey(stored);
        const article = el('article', 'cart-line'); article.dataset.lineKey = key;
        const media = el('div', 'cart-line-media');
        if (row.image) {
            const image = el('img');
            image.src = row.image;
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
        quantity.append(minus, input, plus); controls.append(quantity);
        const links = el('div', 'cart-line-actions');
        const editLink = copy.querySelector('.cart-edit');
        if (editLink) links.append(editLink);
        links.append(action('× Quitar', 'remove', key, `Quitar ${row.name}`));
        copy.append(links);
        const amount = el('div', 'cart-line-price', row.available ? row.formatted_total : '—');
        if (row.available) amount.append(el('small', '', `${row.formatted_unit} / unidad`));
        article.append(copy, controls, amount); return article;
    }
    async function render() {
        resetCoupon();
        message = ''; whatsapp.disabled = true;
        const ticket = ++generation; controller?.abort(); controller = new AbortController();
        const lines = cartStore.get();
        const selectedIds = new Set(lines.map(line => String(line.product_id)));
        let shown = 0;
        root.querySelectorAll('[data-suggestion-id]').forEach(card => {
            card.hidden = selectedIds.has(card.dataset.suggestionId) || shown >= 3;
            if (!card.hidden) shown++;
        });
        const suggestions = root.querySelector('[data-cart-suggestions]');
        if (suggestions) suggestions.hidden = shown === 0;
        root.querySelector('[data-cart-empty]').hidden = lines.length > 0;
        root.querySelector('[data-cart-filled]').hidden = lines.length === 0;
        retry.hidden = true; feedback.textContent = cartStore.warning(); subtotal.textContent = '—'; syncMobileCheckout();
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
            if (!result.has_errors && result.lines.every(row => row.available)) {
                message = ['Hola ZERO DAY, quisiera consultar disponibilidad de:', ...result.lines.map((row, i) => `${lines[i].quantity} × ${row.name}${row.selection_labels?.length ? ' (' + row.selection_labels.join(', ') + ')' : ''} — ${row.formatted_total}`), `Subtotal estimado: ${result.formatted_subtotal}`, '¿Me confirman disponibilidad y total?'].join('\n');
                whatsapp.disabled = false; syncMobileCheckout();
            }
            note.textContent = result.has_errors ? 'El subtotal incluye solo las selecciones disponibles. Revisa los elementos señalados.' : '';
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
            if (action === 'remove') { removed = line; undo.hidden = false; cartStore.remove(key); }
            else cartStore.quantity(key, action === 'quantity' ? Number(control.value) : line.quantity + (action === 'increase' ? 1 : -1));
        } catch (error) { feedback.textContent = errorText(error); if (action === 'quantity') control.value = line.quantity; }
    }
    list.addEventListener('click', change); list.addEventListener('change', change);
    root.querySelector('[data-cart-clear]').addEventListener('click', () => { if (!window.confirm('¿Vaciar todo tu carrito?')) return; removed = null; undo.hidden = true; cartStore.clear(); root.querySelector('[data-cart-empty] a').focus(); });
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

function initShopCustomizer() {
    const dialog = document.querySelector('[data-shop-customizer]');
    if (!dialog) return;
    const content = dialog.querySelector('[data-customizer-content]');
    let controller;
    dialog.querySelector('[data-customizer-close]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => controller?.abort());
    document.querySelectorAll('[data-customize]').forEach(link => link.addEventListener('click', async event => {
        event.preventDefault();
        controller?.abort(); controller = new AbortController();
        content.replaceChildren(el('h2', '', 'Personaliza tu bebida'));
        content.firstChild.id = 'shop-customizer-title';
        content.append(el('p', '', 'Cargando opciones…'));
        dialog.showModal();
        try {
            const response = await fetch(link.href, {signal:controller.signal});
            if (!response.ok) throw new Error('No pudimos cargar las opciones. Inténtalo otra vez.');
            const page = new DOMParser().parseFromString(await response.text(), 'text/html');
            const form = page.querySelector('.product-order');
            if (!form) throw new Error('Este producto no está disponible.');
            const title = el('h2', '', page.querySelector('h1')?.textContent || 'Personaliza tu selección');
            title.id = 'shop-customizer-title';
            const price = el('p', 'shop-customizer-price', form.dataset.basePrice);
            price.dataset.productPrice = '';
            const defaults = JSON.parse(link.dataset.standardOptions || '{}');
            form.querySelectorAll('fieldset[data-kind="options"]').forEach(group => {
                group.querySelectorAll('input').forEach(input => {
                    if (!input.disabled && defaults[group.dataset.group] === input.value) input.checked = true;
                });
            });
            content.replaceChildren(title, price, form);
            initProduct(content, null, () => {
                dialog.close();
                const feedback = document.querySelector('[data-commerce-feedback]');
                if (feedback) {
                    const cartLink = el('a', 'cafe-link', 'Ver carrito ↗'); cartLink.href = '/carrito';
                    feedback.replaceChildren(document.createTextNode('Añadido a tu carrito. ' + cartStore.warning() + ' '), cartLink);
                }
            });
        } catch (error) {
            if (error.name !== 'AbortError') {
                content.replaceChildren(el('h2', '', 'No pudimos abrir las opciones'), el('p', '', errorText(error)));
                content.firstChild.id = 'shop-customizer-title';
                const fallback = el('a', 'cafe-link', 'Abrir producto ↗'); fallback.href = link.href; content.append(fallback);
            }
        }
    }));
}
initShopCustomizer();
