import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { initCafe } from '../../app/static/js/modules/cafe.js';

test('exhibition supports selection, wrapping and keyboard focus with one visible object', t => {
    const dom = new JSDOM(`<article class="object-slide">First</article><article class="object-slide">Second</article><div class="exhibition-controls" hidden><button class="object-prev">Previous</button><button data-object-index="0">01</button><button data-object-index="1">02</button><button class="object-next">Next</button></div>`);
    const originals = {};
    for (const name of ['window', 'document']) {
        originals[name] = Object.getOwnPropertyDescriptor(globalThis, name);
        Object.defineProperty(globalThis, name, { configurable: true, value: dom.window[name] });
    }
    t.after(() => {
        for (const name of ['window', 'document']) {
            if (originals[name]) Object.defineProperty(globalThis, name, originals[name]);
            else delete globalThis[name];
        }
        dom.window.close();
    });
    initCafe();
    const active = () => document.querySelectorAll('.object-slide:not([hidden])');
    assert.equal(active().length, 1);
    assert.equal(active()[0].textContent, 'First');
    document.querySelector('.object-prev').click();
    assert.equal(active()[0].textContent, 'Second');
    assert.equal(document.querySelector('[data-object-index="1"]').getAttribute('aria-pressed'), 'true');
    document.querySelector('.object-next').click();
    assert.equal(active()[0].textContent, 'First');
    document.querySelector('.exhibition-controls').dispatchEvent(new window.KeyboardEvent('keydown', { key: 'End', bubbles: true }));
    assert.equal(active()[0].textContent, 'Second');
    assert.equal(document.activeElement.dataset.objectIndex, '1');
    document.querySelector('.exhibition-controls').dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Home', bubbles: true }));
    assert.equal(active()[0].textContent, 'First');
    assert.equal(document.activeElement.dataset.objectIndex, '0');
});
