import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { JSDOM } from 'jsdom';
import { initProductScene } from '../../app/static/js/modules/product_scene.js';

function fixture(t) {
    let stop;
    t.after(() => stop?.());
    const dom = new JSDOM('<section class="opening"><div class="opening-product" data-model="/bag.glb"><img alt="Coffee"></div></section>');
    for (const name of ['window', 'document']) {
        const old = Object.getOwnPropertyDescriptor(globalThis, name);
        Object.defineProperty(globalThis, name, { configurable: true, value: dom.window[name] });
        t.after(() => old ? Object.defineProperty(globalThis, name, old) : delete globalThis[name]);
    }
    Object.defineProperty(document, 'hidden', { value: false });
    let callback, frame;
    const media = {};
    window.matchMedia = q => media[q] ||= { matches: q.includes('min-width'),
        addEventListener(_, fn) { this.change = fn; }, removeEventListener() {} };
    window.IntersectionObserver = class {
        constructor(fn) { callback = fn; }
        observe() {}
        disconnect() {}
    };
    window.requestAnimationFrame = fn => { frame = fn; return 1; };
    window.cancelAnimationFrame = () => { frame = undefined; };
    const host = document.querySelector('.opening-product');
    host.parentElement.getBoundingClientRect = () => ({ top: -200, height: 2000 });
    const renders = [];
    let disposals = 0, loads = 0;
    const scene = { render: p => renders.push(p), dispose: () => disposals++ };
    const loader = async () => { loads++; return { createProductScene: async () => scene }; };
    t.after(() => dom.window.close());
    return { host, media, renders, scene, loader,
        start(load = loader) { stop = initProductScene(load); return stop; },
        visible(value) { callback([{ isIntersecting: value }]); },
        render() { const fn = frame; frame = undefined; fn?.(); },
        get loads() { return loads; }, get disposals() { return disposals; }
    };
}

test('3D loads once on intersection, renders on demand and pauses offscreen', async t => {
    const f = fixture(t); f.start();
    assert.equal(f.loads, 0);
    f.visible(true); f.visible(true); await setImmediate();
    assert.equal(f.loads, 1);
    assert.ok(f.host.classList.contains('model-ready'));
    assert.equal(f.renders.length, 1);
    window.dispatchEvent(new window.Event('scroll')); f.render();
    assert.equal(f.renders.length, 2);
    f.visible(false);
    window.dispatchEvent(new window.Event('scroll')); f.render();
    assert.equal(f.renders.length, 2);
    f.visible(true); await setImmediate(); f.render();
    assert.equal(f.loads, 1);
    const lost = new window.Event('webglcontextlost', { cancelable: true });
    f.host.dispatchEvent(lost);
    assert.ok(lost.defaultPrevented);
    assert.equal(f.disposals, 1);
    assert.ok(!f.host.classList.contains('model-ready'));
});

test('reduced motion and mobile keep fallback and do not download Three', async t => {
    const f = fixture(t); f.start();
    const reduced = f.media['(prefers-reduced-motion: reduce)'];
    reduced.matches = true; f.visible(true); await setImmediate();
    assert.equal(f.loads, 0);
    reduced.matches = false;
    const desktop = f.media['(min-width: 1024px)']; desktop.matches = false;
    desktop.change(); await setImmediate(); assert.equal(f.loads, 0);
    desktop.matches = true; desktop.change(); await setImmediate();
    assert.equal(f.loads, 1);
    reduced.matches = true; reduced.change();
    assert.equal(f.disposals, 1);
    assert.ok(!f.host.classList.contains('model-ready'));
});

test('failed GLB leaves static image and does not repeatedly retry', async t => {
    const f = fixture(t); let loads = 0;
    f.start(async () => { loads++; throw new Error('offline'); });
    f.visible(true); await setImmediate(); f.visible(true); await setImmediate();
    assert.equal(loads, 1);
    assert.ok(!f.host.classList.contains('model-ready'));
    assert.ok(f.host.querySelector('img'));
});

test('cleanup during loading aborts the request and disposes late results', async t => {
    const f = fixture(t); let resolve, signal;
    const stop = f.start(async () => ({ createProductScene: (_, s) => {
        signal = s; return new Promise(done => { resolve = done; });
    } }));
    f.visible(true); await setImmediate(); stop();
    assert.ok(signal.aborted);
    resolve(f.scene); await setImmediate();
    assert.equal(f.disposals, 1);
    assert.ok(!f.host.classList.contains('model-ready'));
});

test('reinitialization replaces an existing scene and save-data prevents loading', async t => {
    const f = fixture(t); f.start(); f.visible(true); await setImmediate();
    Object.defineProperty(window.navigator, 'connection', { value: { saveData: true, addEventListener() {}, removeEventListener() {} } });
    f.start(); assert.equal(f.disposals, 1);
    f.visible(true); await setImmediate(); assert.equal(f.loads, 1);
});

test('real GLB parses without textures; renderer frames, resizes and releases the scene', async t => {
    const f = fixture(t);
    const { readFile } = await import('node:fs/promises');
    const { createProductScene } = await import('../../app/static/js/modules/product_scene_renderer.js');
    const bytes = await readFile(new URL('../../app/static/img/products/zero-day-bag.glb', import.meta.url));
    const text = [];
    t.mock.method(window.HTMLCanvasElement.prototype, 'getContext', () => ({
        fillRect() {}, fillText(value) { text.push(value); }
    }));
    Object.assign(f.host.dataset, { variety: 'Geisha', origin: 'Huila · Colombia' });
    Object.defineProperty(f.host, 'clientWidth', { value: 400 });
    Object.defineProperty(f.host, 'clientHeight', { value: 550 });
    Object.defineProperty(window, 'devicePixelRatio', { value: 3 });
    const calls = [];
    let disposed = false;
    class Renderer {
        setPixelRatio(dpr) { assert.equal(dpr, 2); }
        setSize(w, h) { assert.deepEqual([w, h], [400, 550]); }
        render(scene, camera) { calls.push({ scene, camera }); }
        dispose() { disposed = true; }
    }
    const request = t.mock.method(globalThis, 'fetch', async () => ({ ok: true,
        arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength)
    }));
    const scene = await createProductScene(f.host, new AbortController().signal, Renderer);
    scene.render(0); scene.render(1);
    assert.equal(request.mock.calls.length, 1);
    assert.deepEqual(text.slice(0, 2), ['ZERO-DAY', 'C O F F E E']);
    assert.ok(text.includes('GEISHA'));
    assert.equal(calls.length, 2);
    assert.equal(calls[0].camera.aspect, 400 / 550);
    assert.equal(f.host.querySelectorAll('canvas').length, 1);
    let meshes = 0;
    calls[0].scene.traverse(object => { if (object.isMesh) { meshes++; assert.equal(object.material.metalness, 0); } });
    assert.equal(meshes, 2);
    scene.dispose();
    assert.ok(disposed);
    assert.equal(f.host.querySelectorAll('canvas').length, 0);
    disposed = false;
    t.mock.method(globalThis, 'fetch', async () => ({ ok: false }));
    await assert.rejects(createProductScene(f.host, new AbortController().signal, Renderer), /unavailable/);
    assert.ok(disposed);
});
