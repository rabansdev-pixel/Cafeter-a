import { test } from 'node:test';
import assert from 'node:assert/strict';
import { setImmediate } from 'node:timers/promises';
import { JSDOM } from 'jsdom';
import { initAtmosphereVideo } from '../../app/static/js/modules/atmosphere_video.js';

async function setup(t, { observer = true, button = true, source = '<source data-src="/movie.mp4" type="video/mp4">', connection = true, media = true } = {}) {
    const dom = new JSDOM(`<div data-video-container><video>${source}</video>${button ? '<button class="media-toggle"></button>' : ''}</div>`, { pretendToBeVisual: true });
    const win = dom.window;
    const reduced = new win.EventTarget(); reduced.matches = false;
    const net = new win.EventTarget(); net.saveData = false; net.effectiveType = '4g';
    if (connection) Object.defineProperty(win.navigator, 'connection', { value: net });
    if (media) win.matchMedia = query => query.includes('prefers-reduced') ? reduced : { matches: query !== 'unmatched' };
    let observerCallback;
    let observes = 0, disconnects = 0;
    if (observer) win.IntersectionObserver = class {
        constructor(callback) { observerCallback = callback; }
        observe() { observes++; }
        disconnect() { disconnects++; }
    };
    for (const [key, value] of Object.entries({ window: win, document: win.document, navigator: win.navigator, IntersectionObserver: win.IntersectionObserver })) {
        const descriptor = Object.getOwnPropertyDescriptor(globalThis, key);
        Object.defineProperty(globalThis, key, { configurable: true, value });
        t.after(() => descriptor ? Object.defineProperty(globalThis, key, descriptor) : delete globalThis[key]);
    }
    t.after(() => win.close());
    const video = win.document.querySelector('video');
    let paused = true, calls = 0;
    const playback = { run: async () => {} };
    Object.defineProperty(video, 'paused', { get: () => paused });
    video.canPlayType = type => type === 'video/mp4' ? 'probably' : '';
    video.play = async () => { calls++; await playback.run(); paused = false; video.dispatchEvent(new win.Event('playing')); };
    video.pause = () => { paused = true; video.dispatchEvent(new win.Event('pause')); };
    const dispatch = async (target, type) => { target.dispatchEvent(new win.Event(type)); await setImmediate(); };
    initAtmosphereVideo(); await setImmediate();
    return { win, video, reduced, net, playback, button: win.document.querySelector('button'), dispatch,
        visible: async value => { observerCallback([{ isIntersecting: value }]); await setImmediate(); },
        calls: () => calls, observes: () => observes, disconnects: () => disconnects };
}

test('video follows visibility, manual pause and bfcache restoration', async t => {
    const s = await setup(t);
    await s.visible(true);
    assert.equal(s.video.getAttribute('src'), '/movie.mp4');
    assert.equal(s.video.muted, true);
    assert.equal(s.video.autoplay, false);
    assert.equal(s.button.getAttribute('aria-pressed'), 'true');
    await s.dispatch(s.button, 'click');
    assert.equal(s.video.paused, true);
    await s.visible(true);
    assert.equal(s.calls(), 1);
    await s.dispatch(s.button, 'click');
    assert.equal(s.video.paused, false);
    await s.visible(false);
    assert.equal(s.video.paused, true);
    await s.dispatch(s.button, 'click');
    assert.equal(s.video.paused, true);
    await s.visible(true);
    await s.dispatch(s.win, 'pagehide');
    assert.equal(s.disconnects(), 1);
    await s.visible(true);
    assert.equal(s.video.paused, true);
    s.win.dispatchEvent(new s.win.PageTransitionEvent('pageshow', { persisted: false }));
    assert.equal(s.observes(), 1);
    s.win.dispatchEvent(new s.win.PageTransitionEvent('pageshow', { persisted: true }));
    await setImmediate();
    assert.equal(s.observes(), 2);
    assert.equal(s.video.paused, false);
});

test('motion, data and document constraints pause video while explicit playback overrides motion', async t => {
    const s = await setup(t);
    for (const change of [() => { s.reduced.matches = true; }, () => { s.reduced.matches = false; s.net.saveData = true; }, () => { s.net.saveData = false; s.net.effectiveType = '2g'; }]) {
        change(); await s.dispatch(s.net, 'change'); await s.visible(true);
        assert.equal(s.video.paused, true);
    }
    await s.dispatch(s.button, 'click'); assert.equal(s.video.paused, false);
    s.net.effectiveType = '4g';
    Object.defineProperty(s.win.document, 'hidden', { configurable: true, value: true });
    await s.dispatch(s.win.document, 'visibilitychange');
    await s.dispatch(s.button, 'click');
    assert.equal(s.video.paused, true);
    Object.defineProperty(s.win.document, 'hidden', { configurable: true, value: false });
    await s.dispatch(s.reduced, 'change'); assert.equal(s.video.paused, false);
});

test('source selection skips unmatched and unsupported sources and loads only once', async t => {
    const s = await setup(t, { observer: false, connection: false, source: '<source data-src="/wrong.mp4" media="unmatched" type="video/mp4"><source data-src="/wrong.webm" type="unsupported"><source data-src="/right.mp4" media="matched" type="video/mp4">' });
    assert.equal(s.video.getAttribute('src'), '/right.mp4');
    await s.dispatch(s.button, 'click'); await s.dispatch(s.button, 'click');
    assert.equal(s.video.getAttribute('src'), '/right.mp4');
});

for (const button of [true, false]) test(`play rejection and media errors preserve poster (button=${button})`, async t => {
    const s = await setup(t, { button, source: '' });
    s.video.dataset.videoSrc = '/fallback.mp4';
    s.playback.run = async () => { throw new Error('Autoplay denied'); };
    await s.visible(true);
    assert.equal(s.video.getAttribute('src'), '/fallback.mp4');
    assert.equal(s.video.classList.contains('is-playing'), false);
    await s.dispatch(s.video, 'error');
    if (button) assert.equal(s.button.hidden, true);
    const calls = s.calls(); await s.visible(true); assert.equal(s.calls(), calls);
});

test('missing media API leaves video alone; missing sources cause no source assignment', async t => {
    const s = await setup(t, { media: false });
    assert.equal(s.calls(), 0);
    assert.equal(s.video.hasAttribute('src'), false);
});

test('pending playback is paused when the page exits', async t => {
    const s = await setup(t, { source: '' });
    let finish;
    s.playback.run = () => new Promise(resolve => { finish = resolve; });
    await s.visible(true);
    await s.dispatch(s.win, 'pagehide');
    finish(); await setImmediate();
    assert.equal(s.video.paused, true);
    assert.equal(s.video.hasAttribute('src'), false);
});
