import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';

let sequence = 0;
async function setup(t, { observer = true, reduced = false, query = '', empty = false } = {}) {
    const dom = new JSDOM(empty ? '' : `<form data-shop-search><input id="menu-search"></form><nav class="menu-category-nav"><a href="#coffee">Café</a><a href="#tea">Té</a></nav><p data-menu-results></p><p data-menu-empty hidden>Sin resultados</p>${['coffee', 'tea'].map((id, i) => `<section class="menu-chapter" id="${id}"><h2>${id}</h2><div data-rail-controls><button data-rail-prev>Anterior</button><button data-rail-next>Siguiente</button></div><div data-product-rail><article data-menu-entry data-search="${i ? 'Té verde' : 'Café con leche'}"></article></div></section>`).join('')}<section class="menu-chapter"></section>`, { url: `https://cafe.example/menu?keep=1${query}` });
    for (const key of ['window', 'document']) {
        const descriptor = Object.getOwnPropertyDescriptor(globalThis, key);
        Object.defineProperty(globalThis, key, { configurable: true, value: dom.window[key] });
        t.after(() => descriptor ? Object.defineProperty(globalThis, key, descriptor) : delete globalThis[key]);
    }
    t.after(() => dom.window.close());
    const { document: doc } = dom.window;
    const scrolls = [];
    dom.window.matchMedia = () => ({ matches: reduced });
    dom.window.HTMLElement.prototype.scrollIntoView = function (options) { scrolls.push({ node: this, ...options }); };
    const callbacks = [];
    if (observer) dom.window.ResizeObserver = class {
        constructor(callback) { callbacks.push(callback); }
        observe(node) { assert.ok(node.matches('[data-product-rail]')); }
    };
    const rails = [...doc.querySelectorAll('[data-product-rail]')];
    for (const rail of rails) {
        Object.defineProperty(rail, 'clientWidth', { configurable: true, value: 100 });
        Object.defineProperty(rail, 'scrollWidth', { configurable: true, value: 300 });
        rail.scrollTo = options => { rail.scrollLeft = options.left; };
        rail.scrollBy = options => { scrolls.push(options); rail.scrollLeft += options.left; rail.dispatchEvent(new dom.window.Event('scroll')); };
    }
    await import(`../../app/static/js/menu_filter.js?menuTest=${++sequence}`);
    const search = value => { doc.querySelector('input').value = value; doc.querySelector('input').dispatchEvent(new dom.window.Event('input')); };
    return { doc, window: dom.window, search, rails, scrolls, callbacks };
}

test('menu search normalizes accents and all terms, updates counts, categories and URL', async t => {
    const s = await setup(t, { query: '&q=CAFE' });
    assert.equal(s.doc.querySelector('input').value, 'CAFE');
    assert.match(s.doc.querySelector('[data-menu-results]').textContent, /^1 producto ·/);
    assert.equal(s.doc.querySelector('#tea').hidden, true);
    s.doc.querySelector('a').setAttribute('aria-current', 'location');
    s.search('  VERDE té  ');
    assert.equal(s.doc.querySelector('#coffee').hidden, true);
    assert.equal(s.doc.querySelector('a').hasAttribute('aria-current'), false);
    assert.equal(new URL(s.window.location.href).searchParams.get('q'), 'VERDE té');
    s.search('cafe verde');
    assert.equal(s.doc.querySelector('[data-menu-empty]').hidden, false);
    assert.match(s.doc.querySelector('[data-menu-results]').textContent, /^0 productos/);
    s.search('');
    assert.match(s.doc.querySelector('[data-menu-results]').textContent, /^2 productos/);
    assert.equal(s.doc.querySelector('[data-menu-empty]').hidden, true);
    assert.equal(s.window.location.search, '?keep=1');
});

test('category navigation clears filters and submit focuses results or empty state', async t => {
    const s = await setup(t, { reduced: true });
    s.search('verde');
    const links = [...s.doc.querySelectorAll('a')];
    links.forEach(link => link.addEventListener('click', event => event.preventDefault()));
    links[0].click();
    assert.equal(s.doc.querySelector('input').value, '');
    assert.equal(links[0].getAttribute('aria-current'), 'location');
    links[1].click();
    assert.equal(links[0].hasAttribute('aria-current'), false);
    for (const [term, selector] of [['cafe', '#coffee h2'], ['missing', '[data-menu-empty]']]) {
        s.search(term);
        const event = new s.window.Event('submit', { cancelable: true });
        s.doc.querySelector('form').dispatchEvent(event);
        assert.equal(event.defaultPrevented, true);
        assert.equal(s.doc.activeElement, s.doc.querySelector(selector));
        assert.equal(s.scrolls.at(-1).behavior, 'instant');
    }
});

for (const observer of [true, false]) test(`rails update scrolling boundaries and resizing (observer=${observer})`, async t => {
    const s = await setup(t, { observer });
    const rail = s.rails[0];
    const previous = s.doc.querySelector('[data-rail-prev]');
    const next = s.doc.querySelector('[data-rail-next]');
    assert.equal(previous.disabled, true);
    assert.equal(next.disabled, false);
    assert.equal(rail.tabIndex, 0);
    next.click();
    assert.equal(rail.scrollLeft, 85);
    assert.equal(s.scrolls.at(-1).behavior, 'smooth');
    previous.click();
    assert.equal(rail.scrollLeft, 0);
    rail.scrollLeft = 200;
    rail.dispatchEvent(new s.window.Event('scroll'));
    assert.equal(next.disabled, true);
    s.search('cafe');
    assert.equal(rail.scrollLeft, 0);
    Object.defineProperty(rail, 'scrollWidth', { configurable: true, value: 100 });
    if (observer) s.callbacks.forEach(callback => callback());
    else s.window.dispatchEvent(new s.window.Event('resize'));
    assert.equal(rail.tabIndex, -1);
    assert.equal(s.doc.querySelector('[data-rail-controls]').hidden, true);
});

test('pages without menu search remain untouched', async t => {
    const s = await setup(t, { empty: true });
    assert.equal(s.doc.body.innerHTML, '');
});
