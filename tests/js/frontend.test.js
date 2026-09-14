import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { setImmediate } from 'node:timers/promises';
import { test } from 'node:test';
import { JSDOM } from 'jsdom';
import { initCartDrawer } from '../../app/static/js/modules/cart_drawer.js';
import { initHeroProduct } from '../../app/static/js/modules/hero_product.js';
import { initTastingRadar } from '../../app/static/js/modules/tasting_radar.js';

const cartMarkup = readFileSync(new URL('../../app/templates/components/cart_drawer.html', import.meta.url), 'utf8');
const product = { id: 12, name: '<img src=x onerror=alert(1)>', price: 25000.5, quantity: 1, image_url: '/coffee.svg' };

function setup(t, markup = '') {
    const dom = new JSDOM(`<meta name="csrf-token" content="signed-session-token">${markup}`, { url: 'https://cafe.example' });
    for (const key of ['window', 'document', 'localStorage']) {
        const previous = Object.getOwnPropertyDescriptor(globalThis, key);
        Object.defineProperty(globalThis, key, { configurable: true, value: dom.window[key] });
        t.after(() => previous ? Object.defineProperty(globalThis, key, previous) : delete globalThis[key]);
    }
    t.after(() => dom.window.close());
    return dom.window.document;
}

function setupCart(t, items = []) {
    const doc = setup(t, `${cartMarkup}<button class="js-open-cart"></button><span class="cart-badge"></span><button class="js-add-to-cart"><span>Agregar</span></button>`);
    Object.assign(doc.querySelector('.js-add-to-cart').dataset, {
        id: '12', name: product.name, price: '25000.5', image: product.image_url
    });
    localStorage.setItem('artisan_cafe_cart', JSON.stringify(items));
    const timers = [];
    const nativeTimeout = globalThis.setTimeout;
    t.mock.method(globalThis, 'setTimeout', (callback, delay, ...args) => {
        if (delay === 3000 || delay === 300) {
            timers.push(callback);
            return timers.length;
        }
        return nativeTimeout(callback, delay, ...args);
    });
    const requests = [];
    t.mock.method(globalThis, 'fetch', async (url, options) => {
        requests.push({ url, options });
        const items = JSON.parse(options.body).items;
        const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
        const free = subtotal >= 50000;
        return { ok: true, json: async () => ({ status: 'success', data: {
            subtotal, is_free_shipping: free, free_shipping_remaining: 50000 - subtotal,
            formatted_subtotal: `$${subtotal}`, formatted_shipping: free ? 'Gratis' : '$8500',
            formatted_total: `$${subtotal + (free ? 0 : 8500)}`
        } }) };
    });
    return { doc, timers, requests };
}

test('empty cart, drawer controls and checkout feedback', t => {
    const { doc, requests, timers } = setupCart(t);
    initCartDrawer();
    assert.match(doc.querySelector('#cart-items-container').textContent, /vacío/);
    assert.equal(doc.querySelector('#cart-total-val').textContent, '$0');
    assert.equal(requests.length, 0);
    doc.querySelector('.js-open-cart').click();
    assert.ok(doc.querySelector('#cart-drawer').classList.contains('active'));
    doc.querySelector('#cart-close-btn').click();
    assert.ok(!doc.querySelector('#cart-drawer').classList.contains('active'));
    doc.querySelector('.js-open-cart').click();
    doc.querySelector('#cart-overlay').click();
    assert.ok(!doc.querySelector('#cart-overlay').classList.contains('active'));
    doc.querySelector('#cart-checkout-btn').click();
    assert.match(doc.querySelector('.toast').textContent, /vacío/);
    timers.shift()();
    assert.equal(doc.querySelector('.toast').style.opacity, '0');
    timers.shift()();
    assert.equal(doc.querySelector('.toast'), null);
});

test('add, increment, decrement and delete preserve numeric values and CSRF', async t => {
    const { doc, requests } = setupCart(t);
    initCartDrawer();
    doc.querySelector('.js-add-to-cart span').click();
    await setImmediate();
    assert.deepEqual(JSON.parse(localStorage.getItem('artisan_cafe_cart')), [product]);
    assert.equal(requests[0].url, '/api/cart/calculate');
    assert.equal(requests[0].options.method, 'POST');
    assert.equal(requests[0].options.headers['X-CSRFToken'], 'signed-session-token');
    assert.equal(doc.querySelector('.cart-item h4').textContent, product.name);
    assert.equal(doc.querySelector('.cart-item h4 img'), null);
    assert.equal(doc.querySelector('#shipping-progress-fill').style.width, '50%');
    assert.match(doc.querySelector('#shipping-status-text').textContent, /Agrega/);
    doc.querySelector('.js-add-to-cart').click();
    await setImmediate();
    assert.equal(doc.querySelector('.cart-badge').textContent, '2');
    assert.equal(doc.querySelector('#cart-shipping-val').textContent, 'Gratis');
    assert.equal(doc.querySelector('#shipping-progress-fill').style.width, '100%');
    doc.querySelector('[data-action="inc"]').click();
    await setImmediate();
    assert.equal(doc.querySelector('.cart-badge').textContent, '3');
    for (let i = 0; i < 3; i++) {
        doc.querySelector('[data-action="dec"]').click();
        await setImmediate();
    }
    assert.equal(doc.querySelector('.cart-badge').textContent, '1');
    doc.querySelector('#cart-checkout-btn').click();
    assert.match(doc.querySelector('.toast-container').textContent, /pasarela/);
    doc.querySelector('.cart-del-btn').click();
    assert.deepEqual(JSON.parse(localStorage.getItem('artisan_cafe_cart')), []);
    assert.equal(doc.querySelector('#cart-total-val').textContent, '$0');
});

test('restores persisted cart and ignores unrelated clicks', async t => {
    const { doc, requests } = setupCart(t, [product]);
    initCartDrawer();
    await setImmediate();
    assert.equal(doc.querySelector('#cart-total-val').textContent, '$33500.5');
    doc.querySelector('.cart-item h4').click();
    assert.equal(requests.length, 1);
    assert.equal(doc.querySelector('.cart-badge').textContent, '1');
});

test('API rejection explains how to recover and preserves the cart', async t => {
    const { doc } = setupCart(t, [product]);
    t.mock.method(globalThis, 'fetch', async () => ({ ok: false, json: async () => ({ message: 'Recarga la página.' }) }));
    initCartDrawer();
    await setImmediate();
    assert.match(doc.querySelector('.toast').textContent, /Recarga/);
    assert.deepEqual(JSON.parse(localStorage.getItem('artisan_cafe_cart')), [product]);
});

test('network errors are reported without removing persisted items', async t => {
    setupCart(t, [product]);
    t.mock.method(globalThis, 'fetch', async () => { throw new Error('offline'); });
    const errors = t.mock.method(console, 'error', () => {});
    initCartDrawer();
    await setImmediate();
    assert.equal(errors.mock.calls.length, 1);
    assert.deepEqual(JSON.parse(localStorage.getItem('artisan_cafe_cart')), [product]);
});

test('hero responds to mouse motion, resize and reset', t => {
    const doc = setup(t, '<div class="hero-product-stage"></div><div class="hero-coffee-bag"></div><div class="hero-visual-backdrop"></div>');
    const stage = doc.querySelector('.hero-product-stage');
    let width = 100;
    stage.getBoundingClientRect = () => ({ left: 0, top: 0, width, height: 100 });
    initHeroProduct();
    stage.dispatchEvent(new window.MouseEvent('mousemove', { clientX: 100, clientY: 0 }));
    assert.match(doc.querySelector('.hero-coffee-bag').style.transform, /rotateX\(12deg\) rotateY\(15deg\)/);
    assert.equal(doc.querySelector('.hero-visual-backdrop').style.transform, 'translate(18px, -18px)');
    width = 200;
    window.dispatchEvent(new window.Event('resize'));
    stage.dispatchEvent(new window.MouseEvent('mousemove', { clientX: 100, clientY: 50 }));
    assert.match(doc.querySelector('.hero-coffee-bag').style.transform, /rotateY\(0deg\)/);
    stage.dispatchEvent(new window.MouseEvent('mouseleave'));
    assert.equal(doc.querySelector('.hero-visual-backdrop').style.transform, 'translate(0px, 0px)');
    assert.match(doc.querySelector('.hero-coffee-bag').style.transform, /scale\(1\)/);
});

test('radar switches products, draws metrics and renders notes as text', async t => {
    const dots = ['acidity', 'sweetness', 'aroma', 'body', 'roast'].map(key => `<circle id="radar-dot-${key}"/>`).join('');
    const doc = setup(t, `<svg id="sensory-radar-svg"><polygon id="radar-polygon"/>${dots}</svg><div id="radar-notes-list"></div><span id="radar-roast-val"></span><span id="radar-altitude-val"></span><span id="radar-process-val"></span><button class="radar-tab-btn active" data-product-id="1" data-altitude="2000 msnm" data-process="Natural"></button><button class="radar-tab-btn" data-product-id="2"></button>`);
    let roast = 'Claro';
    const fetchMock = t.mock.method(globalThis, 'fetch', async () => ({ json: async () => ({ status: 'success', data: { radar: {
        roast_level: roast, acidity: 10, sweetness: 8, aroma: 9, body: 6, notes: ['<script>alert(1)</script>']
    } } }) }));
    initTastingRadar();
    await setImmediate();
    assert.equal(fetchMock.mock.calls[0].arguments[0], '/api/products/1/radar');
    assert.equal(doc.querySelector('#radar-dot-acidity').getAttribute('cy'), '60');
    assert.equal(doc.querySelector('#radar-polygon').getAttribute('points').split(' ').length, 5);
    assert.equal(doc.querySelector('#radar-notes-list').textContent, '<script>alert(1)</script>');
    assert.equal(doc.querySelector('#radar-notes-list script'), null);
    assert.equal(doc.querySelector('#radar-altitude-val').textContent, '2000 msnm');
    const second = doc.querySelectorAll('.radar-tab-btn')[1];
    for (const level of ['Medio', 'Oscuro']) {
        roast = level;
        second.click();
        await setImmediate();
        assert.equal(doc.querySelector('#radar-roast-val').textContent, level);
    }
    assert.ok(second.classList.contains('active'));
    assert.equal(doc.querySelector('#radar-process-val').textContent, 'Lavado');
    t.mock.method(globalThis, 'fetch', async () => { throw new Error('offline'); });
    const errors = t.mock.method(console, 'error', () => {});
    second.click();
    await setImmediate();
    assert.equal(errors.mock.calls.length, 1);
    assert.equal(doc.querySelector('#radar-roast-val').textContent, 'Oscuro');
});

test('main initializes modules on pages without hero or radar', async t => {
    const { doc } = setupCart(t);
    t.mock.method(console, 'log', () => {});
    await import('../../app/static/js/main.js');
    doc.dispatchEvent(new window.Event('DOMContentLoaded'));
    assert.match(doc.querySelector('#cart-items-container').textContent, /vacío/);
    doc.querySelector('.js-open-cart').click();
    assert.ok(doc.querySelector('#cart-drawer').classList.contains('active'));
});

test('cart traps keyboard focus, closes with Escape and restores the trigger', async t => {
    const { doc } = setupCart(t, [product]);
    initCartDrawer();
    const trigger = doc.querySelector('.js-open-cart');
    trigger.focus();
    trigger.click();
    const drawer = doc.querySelector('#cart-drawer');
    const close = doc.querySelector('#cart-close-btn');
    const checkout = doc.querySelector('#cart-checkout-btn');
    assert.equal(doc.activeElement, close);
    assert.equal(drawer.getAttribute('aria-hidden'), 'false');
    const increment = doc.querySelector('[data-action="inc"]');
    increment.focus();
    increment.click();
    assert.equal(doc.activeElement, doc.querySelector('[data-action="inc"]'));
    const remove = doc.querySelector('.cart-del-btn');
    remove.focus();
    remove.click();
    assert.equal(doc.activeElement, close);
    close.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true, cancelable: true }));
    assert.equal(doc.activeElement, checkout);
    checkout.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }));
    assert.equal(doc.activeElement, close);
    close.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    assert.equal(doc.activeElement, trigger);
    assert.equal(drawer.getAttribute('aria-hidden'), 'true');
    assert.ok(drawer.hasAttribute('inert'));
    await setImmediate();
});

test('mobile menu exposes expanded state, closes on Escape and link navigation', async t => {
    const { initNavigation } = await import('../../app/static/js/modules/navigation.js');
    const doc = setup(t, '<header class="site-header"><button class="menu-toggle" aria-expanded="false">Menú</button><a href="/">Inicio</a></header>');
    initNavigation();
    const toggle = doc.querySelector('button');
    toggle.click();
    assert.equal(toggle.getAttribute('aria-expanded'), 'true');
    toggle.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    assert.equal(toggle.getAttribute('aria-expanded'), 'false');
    assert.equal(doc.activeElement, toggle);
    toggle.click();
    doc.querySelector('a').click();
    assert.equal(toggle.getAttribute('aria-expanded'), 'false');
    toggle.click();
    toggle.dispatchEvent(new window.FocusEvent('focusout', { relatedTarget: doc.body, bubbles: true }));
    assert.equal(toggle.getAttribute('aria-expanded'), 'false');
});

test('scroll story changes chapters and reduced motion restores every chapter', async t => {
    const { initHomeAnimations } = await import('../../app/static/js/modules/home_animations.js');
    const doc = setup(t, '<div class="opening"><h1 class="opening-word">Atelier</h1><div class="opening-product"></div></div><section class="coffee-story"><div class="story-chapter">Variedad</div><div class="story-chapter">Altura</div><div class="story-chapter">Proceso</div></section><h2 data-reveal>Origen</h2>');
    const media = {};
    window.matchMedia = query => media[query] = { matches: query.includes('min-width'), addEventListener(name, callback) { this.change = callback; }, removeEventListener() {} };
    let pending;
    window.requestAnimationFrame = callback => { pending = callback; return 1; };
    window.cancelAnimationFrame = () => {};
    let intersection;
    let disconnected = 0;
    window.IntersectionObserver = class {
        constructor(callback) { intersection = callback; }
        observe() {}
        unobserve() {}
        disconnect() { disconnected++; }
    };
    const story = doc.querySelector('.coffee-story');
    let top = 100;
    story.getBoundingClientRect = () => ({ top, height: window.innerHeight * 3 });
    doc.querySelector('.opening').getBoundingClientRect = () => ({ top: -100 });
    const cleanup = initHomeAnimations();
    pending();
    const chapters = [...doc.querySelectorAll('.story-chapter')];
    assert.ok(story.classList.contains('is-pinned'));
    assert.equal(chapters[0].getAttribute('aria-hidden'), 'false');
    top = -window.innerHeight;
    window.dispatchEvent(new window.Event('scroll'));
    pending();
    assert.equal(chapters[1].getAttribute('aria-hidden'), 'false');
    top = -window.innerHeight * 2;
    window.dispatchEvent(new window.Event('scroll'));
    pending();
    assert.equal(chapters[2].getAttribute('aria-hidden'), 'false');
    intersection([{ isIntersecting: true, target: doc.querySelector('[data-reveal]').parentElement }]);
    assert.ok(doc.querySelector('[data-reveal]').classList.contains('is-revealed'));
    const reduced = media['(prefers-reduced-motion: reduce)'];
    reduced.matches = true;
    reduced.change();
    assert.ok(!story.classList.contains('is-pinned'));
    assert.ok(chapters.every(chapter => !chapter.hasAttribute('aria-hidden')));
    assert.equal(doc.querySelector('.opening-word').style.translate, '');
    assert.ok(!doc.querySelector('[data-reveal]').classList.contains('reveal-ready'));
    cleanup();
    assert.ok(disconnected > 0);
});
