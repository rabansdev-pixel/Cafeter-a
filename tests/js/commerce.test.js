import { test } from 'node:test';
import assert from 'node:assert/strict';
import { setImmediate } from 'node:timers/promises';
import { JSDOM } from 'jsdom';
import { createCartStore, lineKey } from '../../app/static/js/modules/cart_store.js';

const line = (quantity = 1) => ({ product_id: 'coffee', quantity, options: {}, modifiers: {} });
const flush = async () => { await setImmediate(); await setImmediate(); };
const reply = (data, ok = true) => ({ ok, json: async () => data });
const priced = items => ({ lines: items.map(item => ({ name: 'Café', slug: 'coffee', image: '/coffee.jpg', available: true, selection_labels: ['Leche entera'], formatted_unit: '3.00 USD', formatted_total: `${(3 * item.quantity).toFixed(2)} USD` })), formatted_subtotal: `${items.reduce((sum, item) => sum + item.quantity * 3, 0).toFixed(2)} USD`, has_errors: false });
const product = `<h1>Café</h1><span data-product-price>3.00 USD</span><form class="product-order" data-product-id="coffee" data-base-price="3.00 USD"><input name="quantity" type="number" min="1" max="99" value="1"><fieldset data-kind="options" data-group="milk" data-required="true" data-max="1"><input type="radio" name="milk" value="whole" checked><input type="radio" name="milk" value="oat"></fieldset><fieldset data-kind="modifiers" data-group="extras" data-max="1"><input type="checkbox" value="shot"><input type="checkbox" value="cream"></fieldset><button data-add-button>Guardar</button><p data-order-feedback></p></form>`;
const cart = `<section data-cart-page><div data-cart-empty><a href="/menu">Tienda</a></div><div data-cart-filled><div data-cart-lines></div><button data-cart-clear>Vaciar</button><section data-cart-suggestions>${['coffee','a','b','c','d'].map(id => `<article data-suggestion-id="${id}"></article>`).join('')}</section><aside class="cart-summary"><strong data-cart-subtotal></strong><p data-cart-quote-note></p><button data-cart-whatsapp disabled>WhatsApp</button><div class="cart-coupon"><input id="coupon-code"><button data-coupon-preview>Aplicar</button><button data-coupon-redeem disabled hidden>Canjear</button><button data-coupon-recover>Recuperar</button><p data-coupon-feedback></p><a data-coupon-send hidden></a></div></aside></div><p data-cart-feedback></p><button data-cart-retry hidden>Reintentar</button><button data-cart-undo hidden>Deshacer</button><div data-mobile-checkout hidden><span data-mobile-total-label></span><strong data-mobile-total></strong><button data-mobile-whatsapp disabled>WhatsApp</button></div></section><dialog data-cart-editor><button data-editor-close>Cerrar</button><div data-editor-content></div></dialog>`;
let sequence = 0;
async function setup(t, markup, items = [], search = '') {
    const dom = new JSDOM(`<meta name="csrf-token" content="test-csrf">${markup}`, { url: 'https://cafe.example/' + search });
    for (const key of ['window', 'document', 'location', 'history', 'Event', 'DOMParser']) {
        const previous = Object.getOwnPropertyDescriptor(globalThis, key);
        Object.defineProperty(globalThis, key, { configurable: true, value: dom.window[key] });
        t.after(() => previous ? Object.defineProperty(globalThis, key, previous) : delete globalThis[key]);
    }
    const media = { matches: false, addEventListener(type, fn) { this.change = fn; } };
    const previous = Object.getOwnPropertyDescriptor(globalThis, 'matchMedia');
    Object.defineProperty(globalThis, 'matchMedia', { configurable: true, value: () => media });
    t.after(() => previous ? Object.defineProperty(globalThis, 'matchMedia', previous) : delete globalThis.matchMedia);
    dom.window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
    dom.window.HTMLDialogElement.prototype.close = function () { this.open = false; this.dispatchEvent(new dom.window.Event('close')); };
    const { cartStore } = await import('../../app/static/js/cart_indicator.js');
    const store = createCartStore(dom.window.localStorage);
    items.forEach(item => store.add(item));
    for (const method of Object.keys(store)) t.mock.method(cartStore, method, store[method]);
    const calls = [];
    const api = { handle: async (url, options) => reply(priced(JSON.parse(options.body).items)) };
    t.mock.method(globalThis, 'fetch', async (url, options) => { calls.push({ url, options }); return api.handle(url, options); });
    t.after(() => dom.window.close());
    return { store, api, calls, media, doc: dom.window.document,
        start: async () => { await import(`../../app/static/js/commerce.js?test=${++sequence}`); await flush(); },
        click: async selector => { dom.window.document.querySelector(selector).click(); await flush(); },
        change: async (selector, value) => { const node = dom.window.document.querySelector(selector); if (value !== undefined) node.value = value; node.dispatchEvent(new dom.window.Event('change', { bubbles: true })); await flush(); },
        submit: async () => { dom.window.document.querySelector('.product-order').dispatchEvent(new dom.window.Event('submit', { bubbles: true, cancelable: true })); await flush(); }
    };
}

test('quick add validates server price, sends CSRF, saves options and restores its label', async t => {
    const s = await setup(t, `<button data-quick-add="coffee" data-standard-options='{"milk":"oat"}'>Añadir</button><p data-commerce-feedback></p>`);
    const timers = [];
    const nativeTimeout = globalThis.setTimeout;
    t.mock.method(globalThis, 'setTimeout', (fn, delay, ...args) => {
        if (delay === 900) { timers.push(fn); return 0; }
        return nativeTimeout(fn, delay, ...args);
    });
    await s.start(); await s.click('button');
    assert.equal(s.store.get()[0].options.milk, 'oat');
    assert.equal(s.calls[0].options.headers['X-CSRFToken'], 'test-csrf');
    assert.equal(s.doc.querySelector('button').textContent, 'Añadido ✓');
    timers[0](); assert.equal(s.doc.querySelector('button').disabled, false);
    assert.equal(s.doc.querySelector('button').textContent, 'Añadir');
    assert.equal(s.doc.querySelector('[data-commerce-feedback] a').pathname, '/carrito');
});

for (const [name, handler, expected] of [
    ['network', async () => { throw new TypeError('offline'); }, /No pudimos conectar/],
    ['invalid JSON', async () => ({ ok: true, json: async () => { throw new Error(); } }), /comprobar/],
    ['HTTP error', async () => reply({ message: 'Agotado' }, false), /Agotado/],
    ['unavailable item', async () => reply({ lines: [{ available: false, error: 'Sin stock' }] }), /Sin stock/]
]) test(`quick add preserves the cart on ${name}`, async t => {
    const s = await setup(t, '<button data-quick-add="coffee">Añadir</button><p data-commerce-feedback></p>');
    s.api.handle = handler; await s.start(); await s.click('button');
    assert.deepEqual(s.store.get(), []);
    assert.match(s.doc.querySelector('[data-commerce-feedback]').textContent, expected);
    assert.equal(s.doc.querySelector('button').disabled, false);
});

test('product options validate, quote, submit and edit an existing selection', async t => {
    const saved = { ...line(2), options: { milk: 'oat' }, modifiers: { extras: ['shot'] } };
    const s = await setup(t, product, [saved], '?line=' + encodeURIComponent(lineKey(saved)));
    await s.start();
    assert.equal(s.doc.querySelector('[value="oat"]').checked, true);
    assert.equal(s.doc.querySelector('[data-add-button]').textContent, 'Guardar los cambios');
    await s.change('[name="quantity"]', '3');
    assert.equal(s.doc.querySelector('[data-product-price]').textContent, '9.00 USD');
    await s.submit(); assert.equal(s.store.get().length, 1); assert.equal(s.store.get()[0].quantity, 3);
    assert.equal(location.search, ''); assert.match(s.doc.querySelector('[data-order-feedback]').textContent, /Cambios guardados/);
    s.doc.querySelector('[value="oat"]').checked = false;
    await s.submit(); assert.match(s.doc.querySelector('[data-order-feedback]').textContent, /Elige las opciones/);
    s.doc.querySelector('[value="whole"]').checked = true;
    s.doc.querySelector('[value="cream"]').checked = true;
    await s.submit(); assert.match(s.doc.querySelector('[data-order-feedback]').textContent, /complementos/);
    assert.equal(s.store.get()[0].quantity, 3);
});

test('product handles missing edit keys and failed price updates without losing selections', async t => {
    const s = await setup(t, product, [], '?line=missing'); await s.start();
    assert.match(s.doc.querySelector('[data-order-feedback]').textContent, /ya no está/);
    s.api.handle = async () => { throw new TypeError('offline'); };
    await s.change('[name="quantity"]', '2'); await s.submit();
    assert.equal(s.doc.querySelector('[data-product-price]').textContent, '3.00 USD');
    assert.equal(s.doc.querySelector('[name="quantity"]').disabled, false);
    assert.match(s.doc.querySelector('[data-order-feedback]').textContent, /No pudimos conectar/);
});

test('cart quantities, removal, undo, empty state and responsive recommendations', async t => {
    const s = await setup(t, cart, [line(2)]); await s.start();
    assert.equal(s.doc.querySelector('[data-cart-subtotal]').textContent, '6.00 USD');
    assert.equal(s.doc.querySelectorAll('[data-suggestion-id]:not([hidden])').length, 3);
    s.doc.querySelector('[data-action="increase"]').focus();
    await s.click('[data-action="increase"]'); assert.equal(s.store.get()[0].quantity, 3);
    assert.equal(s.doc.activeElement.dataset.action, 'increase');
    await s.click('[data-action="decrease"]'); assert.equal(s.store.get()[0].quantity, 2);
    await s.change('[data-action="quantity"]', '0'); assert.equal(s.store.get()[0].quantity, 2);
    await s.change('[data-action="quantity"]', '99'); assert.equal(s.doc.querySelector('[data-action="increase"]').disabled, true);
    s.doc.querySelector('.cart-line img').dispatchEvent(new Event('error'));
    assert.equal(s.doc.querySelector('.cart-line-media').textContent, 'ZD');
    await s.click('[data-action="remove"]'); assert.equal(s.doc.querySelector('[data-cart-empty]').hidden, false);
    await s.click('[data-cart-undo]'); assert.equal(s.store.get()[0].quantity, 99);
    s.media.matches = true; s.media.change();
    assert.equal(s.doc.querySelector('.cart-summary').nextElementSibling.dataset.cartSuggestions, '');
    s.media.matches = false; s.media.change();
    t.mock.method(window, 'confirm', () => false); await s.click('[data-cart-clear]'); assert.equal(s.store.get().length, 1);
    t.mock.method(window, 'confirm', () => true); await s.click('[data-cart-clear]');
    assert.deepEqual(s.store.get(), []); assert.equal(s.doc.querySelector('[data-mobile-checkout]').hidden, true);
});

test('cart rejects unavailable quotes and recovers from network errors via retry', async t => {
    const s = await setup(t, cart, [line()]);
    s.api.handle = async () => { throw new TypeError('offline'); }; await s.start();
    assert.equal(s.doc.querySelector('[data-cart-retry]').hidden, false);
    assert.equal(s.doc.querySelector('[data-cart-whatsapp]').disabled, true);
    assert.equal(s.store.get().length, 1);
    s.api.handle = async () => reply({ ...priced([line()]), has_errors: true, lines: [{ name: '<img onerror=alert(1)>', available: false, error: 'Agotado' }] });
    await s.click('[data-cart-retry]'); assert.equal(s.doc.querySelector('h2 img'), null);
    assert.match(s.doc.querySelector('[data-cart-quote-note]').textContent, /solo las selecciones disponibles/);
    s.api.handle = async () => reply(priced([line()]));
    window.dispatchEvent(new Event('online')); await flush();
    assert.equal(s.doc.querySelector('[data-cart-whatsapp]').disabled, false);
});

test('coupons preview, redeem, recover and send a receipt through WhatsApp', async t => {
    const s = await setup(t, cart, [line()]); await s.start();
    const receipt = { label: 'Oferta', discount: '1 USD', total: '2 USD', redemption: 'R-123', code: 'CAFE', lines: [{ name: 'Café', quantity: 1, options: ['Entera'], total: '3 USD' }] };
    s.api.handle = async url => reply(url.endsWith('preview') ? { ...receipt, redemption: null } : receipt);
    await s.click('[data-coupon-preview]'); assert.equal(s.doc.querySelector('[data-coupon-redeem]').hidden, false);
    await s.click('[data-coupon-redeem]'); assert.equal(s.doc.querySelector('[data-coupon-send]').hidden, false);
    assert.equal(s.doc.querySelector('[data-mobile-total]').textContent, '2 USD');
    assert.match(s.doc.querySelector('[data-coupon-feedback]').textContent, /R-123/);
    s.api.handle = async () => reply({ url: 'https://wa.me/593988357638', reference: 'ZD-123' });
    let destination; const tab = { opener: {}, location: { replace(url) { destination = url; } }, close() {} };
    t.mock.method(window, 'open', () => tab);
    await s.click('[data-mobile-whatsapp]');
    assert.equal(destination, 'https://wa.me/593988357638'); assert.equal(tab.opener, null);
    assert.deepEqual(JSON.parse(s.calls.at(-1).options.body), { redemption: 'R-123' });
    s.doc.querySelector('#coupon-code').dispatchEvent(new Event('input'));
    assert.equal(s.doc.querySelector('[data-coupon-send]').hidden, true);
    s.api.handle = async () => reply(receipt); await s.click('[data-coupon-recover]');
    assert.equal(s.doc.querySelector('[data-coupon-send]').dataset.redemption, 'R-123');
});

test('coupon errors and popup blocking provide recoverable feedback', async t => {
    const s = await setup(t, cart, [line()]); await s.start();
    s.api.handle = async () => reply({ message: 'Cupón agotado' }, false);
    await s.click('[data-coupon-preview]'); assert.match(s.doc.querySelector('[data-coupon-feedback]').textContent, /agotado/);
    assert.equal(s.doc.querySelector('[data-coupon-preview]').disabled, false);
    t.mock.method(window, 'open', () => null);
    s.api.handle = async () => reply({ url: 'https://wa.me/593988357638', reference: 'ZD-42' });
    await s.click('[data-cart-whatsapp]'); assert.match(s.doc.querySelector('[data-cart-feedback] a').textContent, /ZD-42/);
    assert.deepEqual(JSON.parse(s.calls.at(-1).options.body), { items: s.store.get() });
    let closed = false; t.mock.method(window, 'open', () => ({ close() { closed = true; } }));
    s.api.handle = async () => reply({}, false); await s.click('[data-cart-whatsapp]');
    assert.equal(closed, true); assert.match(s.doc.querySelector('[data-cart-feedback]').textContent, /guardar la consulta/);
});

test('cart editor loads existing options and saves in place, with failure feedback', async t => {
    const s = await setup(t, cart, [line()]); await s.start();
    s.api.handle = async (url, options) => options ? reply(priced(JSON.parse(options.body).items)) : { ok: true, text: async () => product };
    await s.click('.cart-edit'); assert.equal(s.doc.querySelector('dialog').open, true);
    s.doc.querySelector('[value="whole"]').checked = true;
    await s.submit(); assert.equal(s.doc.querySelector('dialog').open, false);
    s.api.handle = async () => ({ ok: false }); await s.click('.cart-edit');
    assert.match(s.doc.querySelector('[data-editor-content]').textContent, /abrir las opciones/);
    await s.click('[data-editor-close]'); assert.equal(s.doc.querySelector('dialog').open, false);
});

test('shop customizer uses defaults, saves and offers fallback on failure', async t => {
    const s = await setup(t, `<a data-customize href="/producto/coffee" data-standard-options='{"milk":"oat"}'>Personalizar</a><p data-commerce-feedback></p><dialog data-shop-customizer><button data-customizer-close>Cerrar</button><div data-customizer-content></div></dialog>`);
    s.api.handle = async (url, options) => options?.method === 'POST' ? reply(priced(JSON.parse(options.body).items)) : { ok: true, text: async () => product };
    await s.start(); await s.click('[data-customize]'); assert.equal(s.doc.querySelector('[value="oat"]').checked, true);
    await s.submit(); assert.equal(s.store.get()[0].options.milk, 'oat'); assert.equal(s.doc.querySelector('dialog').open, false);
    assert.equal(s.doc.querySelector('[data-commerce-feedback] a').pathname, '/carrito');
    s.api.handle = async () => ({ ok: true, text: async () => '<p>No disponible</p>' });
    await s.click('[data-customize]'); assert.equal(s.doc.querySelector('[data-customizer-content] a').pathname, '/producto/coffee');
    await s.click('[data-customizer-close]'); assert.equal(s.doc.querySelector('dialog').open, false);
});

test('category navigation follows visible sections only', async t => {
    const s = await setup(t, '<nav class="menu-category-nav"><a href="#a">A</a><a href="#b">B</a></nav><section class="menu-chapter" id="a"></section><section class="menu-chapter" id="b"></section>');
    let notify; window.IntersectionObserver = class { constructor(fn) { notify = fn; } observe() {} };
    const old = Object.getOwnPropertyDescriptor(globalThis, 'IntersectionObserver');
    Object.defineProperty(globalThis, 'IntersectionObserver', { configurable: true, value: window.IntersectionObserver });
    t.after(() => old ? Object.defineProperty(globalThis, 'IntersectionObserver', old) : delete globalThis.IntersectionObserver);
    await s.start(); notify(); assert.equal(s.doc.querySelector('[href="#b"]').getAttribute('aria-current'), 'location');
    s.doc.querySelector('#b').hidden = true; notify(); assert.equal(s.doc.querySelector('[href="#a"]').getAttribute('aria-current'), 'location');
});

test('WhatsApp popup errors show feedback and allow retrying the inquiry', async t => {
    const s = await setup(t, cart, [line()]);
    await s.start();
    t.mock.method(window, 'open', () => { throw new Error('No se pudo abrir la ventana'); });
    await s.click('[data-cart-whatsapp]');
    assert.match(s.doc.querySelector('[data-cart-feedback]').textContent, /No se pudo abrir la ventana/);
    assert.equal(s.calls.filter(call => call.url === '/api/inquiries').length, 0);
    t.mock.method(window, 'open', () => null);
    s.api.handle = async () => reply({ url: 'https://wa.me/123', reference: 'TEST' });
    await s.click('[data-cart-whatsapp]');
    assert.equal(s.calls.filter(call => call.url === '/api/inquiries').length, 1);
    assert.equal(s.doc.querySelector('[data-cart-feedback] a').href, 'https://wa.me/123');
});
