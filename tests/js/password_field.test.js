import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';

const field = '<input id="access-password" type="password">';
const button = '<button class="password-toggle" hidden aria-label="Mostrar contraseña" aria-pressed="false"><span class="password-eye-slash" hidden></span></button>';
const guidance = '<div id="password-guidance"><div class="password-meter"><span></span><span></span><span></span></div><p data-password-status></p><p data-password-minimum></p></div>';
let sequence = 0;
async function setup(t, markup) {
    const dom = new JSDOM(markup);
    for (const key of ['window', 'document']) {
        const descriptor = Object.getOwnPropertyDescriptor(globalThis, key);
        Object.defineProperty(globalThis, key, { configurable: true, value: dom.window[key] });
        t.after(() => descriptor ? Object.defineProperty(globalThis, key, descriptor) : delete globalThis[key]);
    }
    t.after(() => dom.window.close());
    await import(`../../app/static/js/password-field.js?passwordTest=${++sequence}`);
    return { doc: dom.window.document, window: dom.window };
}

for (const [name, markup] of [['input', button], ['toggle', field]]) {
    test(`password enhancement leaves the page unchanged without ${name}`, async t => {
        const s = await setup(t, markup);
        assert.equal(s.doc.body.children.length, 1);
        if (name === 'input') assert.equal(s.doc.querySelector('button').hidden, true);
        else assert.equal(s.doc.querySelector('input').type, 'password');
    });
}

test('password visibility works without guidance and is reset on pagehide', async t => {
    const s = await setup(t, field + button);
    const input = s.doc.querySelector('input');
    const toggle = s.doc.querySelector('button');
    const slash = toggle.querySelector('span');
    assert.equal(toggle.hidden, false);
    toggle.click();
    assert.equal(input.type, 'text');
    assert.equal(toggle.getAttribute('aria-label'), 'Ocultar contraseña');
    assert.equal(toggle.getAttribute('aria-pressed'), 'true');
    assert.equal(slash.hidden, false);
    toggle.click();
    const assertHidden = () => {
        assert.equal(input.type, 'password');
        assert.equal(toggle.getAttribute('aria-label'), 'Mostrar contraseña');
        assert.equal(toggle.getAttribute('aria-pressed'), 'false');
        assert.equal(slash.hidden, true);
    };
    assertHidden();
    toggle.click();
    s.window.dispatchEvent(new s.window.Event('pagehide'));
    assertHidden();
});

test('password guidance enforces length boundaries, counts Unicode and refreshes on input/change/pageshow', async t => {
    const s = await setup(t, field + button + guidance);
    const input = s.doc.querySelector('input');
    const label = s.doc.querySelector('[data-password-status]');
    const minimum = s.doc.querySelector('[data-password-minimum]');
    const emptyStatus = 'Usa al menos 12 caracteres.';
    assert.equal(label.textContent, emptyStatus);
    assert.equal(input.validationMessage, '');
    assert.equal(s.doc.querySelectorAll('.is-filled').length, 0);
    const cases = [
        ['', 0, false, emptyStatus],
        ['a'.repeat(11), 1, false, 'Todavía es demasiado corta.'],
        ['a'.repeat(12), 2, true, 'Cumple el mínimo. Puedes hacerla más larga.'],
        ['a'.repeat(15), 2, true, 'Cumple el mínimo. Puedes hacerla más larga.'],
        ['a'.repeat(16), 3, true, 'Buena longitud. Asegúrate de que sea única.'],
        ['a'.repeat(256), 3, true, 'Buena longitud. Asegúrate de que sea única.'],
        ['a'.repeat(257), 3, false, 'Máximo: 256 caracteres.'],
        ['🔒'.repeat(11), 1, false, 'Todavía es demasiado corta.'],
        ['🔒'.repeat(12), 2, true, 'Cumple el mínimo. Puedes hacerla más larga.'],
        ['', 0, false, emptyStatus],
    ];
    for (const [index, [value, level, meets, status]] of cases.entries()) {
        input.value = value;
        if (index % 3 === 0) s.window.dispatchEvent(new s.window.Event('pageshow'));
        else input.dispatchEvent(new s.window.Event(index % 3 === 1 ? 'input' : 'change'));
        assert.equal(label.textContent, status);
        assert.equal(s.doc.querySelectorAll('.is-filled').length, level);
        assert.equal(minimum.dataset.met, String(meets));
        assert.equal(minimum.textContent, meets ? '✓ Mínimo de 12 caracteres cumplido.' : 'Mínimo obligatorio: 12 caracteres.');
        assert.equal(input.validationMessage, value && !meets ? 'Usa entre 12 y 256 caracteres.' : '');
    }
});
