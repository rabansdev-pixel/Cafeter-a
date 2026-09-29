import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { initCafe } from '../../app/static/js/modules/cafe.js';

function setup(t, markup, home = false) {
    const dom = new JSDOM(markup);
    const win = dom.window;
    const observers = [];
    const frames = new Map();
    let serial = 0;
    const media = { matches: false, addEventListener(type, fn) { this.callback = fn; }, removeEventListener() { this.callback = null; } };
    win.matchMedia = () => media;
    win.IntersectionObserver = class {
        constructor(callback) { this.callback = callback; this.targets = new Set(); observers.push(this); }
        observe(target) { this.targets.add(target); }
        unobserve(target) { this.targets.delete(target); }
        disconnect() { this.targets.clear(); }
    };
    win.requestAnimationFrame = fn => { frames.set(++serial, fn); return serial; };
    win.cancelAnimationFrame = id => frames.delete(id);
    for (const [key, value] of Object.entries({ window: win, document: win.document, innerHeight: win.innerHeight,
        IntersectionObserver: win.IntersectionObserver, requestAnimationFrame: win.requestAnimationFrame,
        cancelAnimationFrame: win.cancelAnimationFrame })) {
        const previous = Object.getOwnPropertyDescriptor(globalThis, key);
        Object.defineProperty(globalThis, key, { configurable: true, value });
        t.after(() => previous ? Object.defineProperty(globalThis, key, previous) : delete globalThis[key]);
    }
    t.after(() => win.close());
    if (home) win.document.body.classList.add('zero-home');
    return { win, doc: win.document, media, observers, frames,
        tick() { const pending = [...frames.values()]; frames.clear(); pending.forEach(fn => fn()); },
        emit(observer, target, visible = true) { observer.callback([{ target, isIntersecting: visible }]); } };
}

test('reading reveal preserves text and responds to scroll, resize and reduced motion', t => {
    const s = setup(t, '<h2 data-words>Un café <em>para ti</em></h2><article data-cafe-reveal>Detalle</article>');
    const heading = s.doc.querySelector('h2');
    let top = 2000;
    heading.getBoundingClientRect = () => ({ top });
    initCafe();
    assert.equal(heading.textContent, 'Un café para ti');
    assert.equal(heading.querySelectorAll('.word-reveal').length, 4);
    assert.equal(heading.querySelectorAll('.read').length, 0);
    top = 0;
    s.win.dispatchEvent(new s.win.Event('scroll'));
    s.win.dispatchEvent(new s.win.Event('resize'));
    assert.equal(s.frames.size, 1); s.tick();
    assert.equal(heading.querySelectorAll('.read').length, 4);
    const card = s.doc.querySelector('article');
    s.emit(s.observers[0], card, false); assert.ok(card.classList.contains('pending'));
    s.emit(s.observers[0], card); assert.ok(!card.classList.contains('pending'));
    assert.equal(s.observers[0].targets.size, 0);
    top = 2000; s.media.matches = true; s.media.callback(); s.tick();
    assert.equal(heading.querySelectorAll('.read').length, 4);
    s.win.dispatchEvent(new s.win.Event('pagehide'));
    s.win.dispatchEvent(new s.win.Event('scroll'));
    assert.equal(s.frames.size, 0); assert.equal(s.media.callback, null);
});

test('interior pages without headings and with reduced motion remain readable', t => {
    const s = setup(t, '<article data-cafe-reveal>Visible</article>');
    s.media.matches = true; initCafe();
    assert.equal(s.observers.length, 0);
    assert.ok(!s.doc.querySelector('article').classList.contains('pending'));
    s.win.dispatchEvent(new s.win.Event('resize')); s.tick();
    s.win.dispatchEvent(new s.win.Event('pagehide'));
    assert.equal(s.frames.size, 0);
});

test('home entrances preserve accessible text and animate only visible content', t => {
    const s = setup(t, '<h1 data-home-pull>Un café <em>para compartir hoy aquí contigo</em></h1><article data-home-card>Uno</article><article data-home-card>Dos</article><p data-home-letters>Tu próxima pausa</p>', true);
    const heading = s.doc.querySelector('h1'), paragraph = s.doc.querySelector('p');
    let top = 2000;
    paragraph.getBoundingClientRect = () => ({ top, height: 100 });
    initCafe();
    assert.equal(heading.querySelector('.home-sr').textContent, 'Un café para compartir hoy aquí contigo');
    assert.equal(paragraph.querySelector('.home-sr').textContent, 'Tu próxima pausa');
    assert.equal(heading.querySelectorAll('.home-word-mask').length, 7);
    assert.ok([...heading.querySelectorAll('.home-word-mask')].every(el => el.getAttribute('aria-hidden') === 'true'));
    const letter = [...paragraph.querySelectorAll('.home-copy-letter')].at(-1);
    assert.equal(letter.style.getPropertyValue('--letter-opacity'), '0.25');
    s.win.dispatchEvent(new s.win.Event('scroll')); assert.equal(s.frames.size, 0);
    const observer = s.observers[0];
    s.emit(observer, heading, false); assert.ok(!heading.classList.contains('home-in-view'));
    s.emit(observer, heading); assert.ok(heading.classList.contains('home-in-view'));
    assert.ok(!observer.targets.has(heading));
    assert.equal(s.doc.querySelectorAll('article')[1].style.getPropertyValue('--card-delay'), '0.12s');
    top = -200;
    s.emit(observer, paragraph); s.win.dispatchEvent(new s.win.Event('resize'));
    assert.equal(s.frames.size, 1); s.tick();
    assert.equal(letter.style.getPropertyValue('--letter-opacity'), '1');
    s.emit(observer, paragraph, false); s.win.dispatchEvent(new s.win.Event('scroll'));
    assert.equal(s.frames.size, 0);
    s.media.matches = true; s.media.callback();
    assert.ok(!heading.classList.contains('home-ready'));
    assert.equal(letter.style.getPropertyValue('--letter-opacity'), '');
    s.media.matches = false; s.media.callback();
    assert.equal(heading.querySelectorAll('.home-sr').length, 1);
    s.win.dispatchEvent(new s.win.Event('pagehide'));
    assert.equal(s.observers.at(-1).targets.size, 0);
    const page = new s.win.Event('pageshow'); Object.defineProperty(page, 'persisted', { value: true });
    s.win.dispatchEvent(page);
    assert.ok(s.observers.at(-1).targets.has(paragraph));
    assert.equal(paragraph.querySelectorAll('.home-sr').length, 1);
});

test('home supports initial reduced motion, missing paragraphs and unavailable observers', t => {
    const s = setup(t, '<h1 data-home-pull>ZERO DAY</h1>', true);
    s.media.matches = true; initCafe();
    assert.equal(s.doc.querySelector('.home-word-mask'), null);
    s.media.matches = false; s.media.callback();
    assert.equal(s.doc.querySelectorAll('.home-word-mask').length, 2);
    s.win.dispatchEvent(new s.win.Event('scroll')); assert.equal(s.frames.size, 0);
    s.win.dispatchEvent(new s.win.Event('pagehide'));
    delete s.win.IntersectionObserver;
    initCafe(); assert.equal(s.doc.querySelectorAll('.home-word-mask').length, 2);
    s.doc.body.classList.remove('zero-home'); initCafe();
});

test('exhibition handles arrows, direct selection and ignores unrelated keys', t => {
    const s = setup(t, '<div class="object-slide">A</div><div class="object-slide">B</div><div class="exhibition-controls"><button class="object-prev">Anterior</button><button class="object-next">Siguiente</button><button data-object-index="0">A</button><button data-object-index="1">B</button></div>');
    delete s.win.matchMedia; initCafe();
    const controls = s.doc.querySelector('.exhibition-controls');
    const key = value => controls.dispatchEvent(new s.win.KeyboardEvent('keydown', { key: value, bubbles: true }));
    key('ArrowRight'); assert.equal(s.doc.activeElement.dataset.objectIndex, '1');
    key('ArrowLeft'); assert.equal(s.doc.activeElement.dataset.objectIndex, '0');
    key('Escape'); assert.equal(s.doc.activeElement.dataset.objectIndex, '0');
    s.doc.querySelector('[data-object-index="1"]').click();
    assert.equal(s.doc.querySelectorAll('.object-slide')[1].hidden, false);
});
