import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CART_KEY, createCartStore, lineKey, normalizeLine } from '../../app/static/js/modules/cart_store.js';
const item = { product_id: 'test', quantity: 1, options: {}, modifiers: {} };
function memory() { const data = new Map(); return { getItem: key => data.get(key), setItem: (key, value) => data.set(key, value) }; }
test('cart merges identical configurations and persists without client prices', () => {
    const storage = memory(), store = createCartStore(storage);
    store.add({ ...item, price: .01 }); store.add(item);
    assert.equal(store.get()[0].quantity, 2);
    assert.equal(createCartStore(storage).get()[0].quantity, 2);
    assert.ok(!storage.getItem(CART_KEY).includes('price'));
    store.add({ ...item, options: { size: 'large' } });
    assert.equal(store.get().length, 2);
});
test('option ordering is canonical and editing merges without losing the selection', () => {
    const a = { ...item, modifiers: { extra: ['a', 'b'] }, options: { x: 'a', y: 'b' } };
    const b = { ...item, modifiers: { extra: ['b', 'a'] }, options: { y: 'b', x: 'a' } };
    assert.equal(lineKey(a), lineKey(b));
    const store = createCartStore(memory()); store.add(item); store.add(a);
    store.add({ ...a, quantity: 2 }, lineKey(item));
    assert.equal(store.get().length, 1); assert.equal(store.get()[0].quantity, 3);
    assert.throws(() => store.add(item, 'no-longer-present'));
});
test('invalid or excessive quantity is rejected atomically', () => {
    const store = createCartStore(memory()); store.add({ ...item, quantity: 99 });
    assert.throws(() => store.add(item)); assert.equal(store.get()[0].quantity, 99);
    for (const quantity of [0, -1, 100, 1.2, NaN, Infinity, true, '1']) assert.throws(() => store.quantity(lineKey(item), quantity));
    assert.equal(store.get()[0].quantity, 99);
});
test('remove, clear, external synchronization and snapshot isolation', () => {
    const storage = memory(), store = createCartStore(storage); let calls = 0;
    const stop = store.subscribe(() => calls++); store.add(item);
    const copy = store.get(); copy[0].quantity = 70;
    assert.equal(store.get()[0].quantity, 1);
    const second = createCartStore(storage); second.quantity(lineKey(item), 3); store.sync();
    assert.equal(store.get()[0].quantity, 3); store.remove(lineKey(item)); assert.equal(store.get().length, 0);
    store.add(item); store.clear(); assert.equal(createCartStore(storage).get().length, 0);
    stop(); assert.equal(calls, 5);
});
test('corrupted and blocked storage do not crash and give a useful warning', () => {
    for (const saved of ['bad json', '{"version":2}', '{"version":1,"lines":[null]}']) {
        const storage = memory(); storage.setItem(CART_KEY, saved);
        const store = createCartStore(storage); assert.deepEqual(store.get(), []); assert.ok(store.warning());
    }
    const store = createCartStore({ getItem() { throw new Error(); }, setItem() { throw new Error(); } });
    store.add(item); assert.equal(store.get().length, 1); assert.ok(store.warning());
});
test('malformed option payloads and prototype keys are rejected', () => {
    assert.throws(() => normalizeLine({ ...item, options: { size: [] } }));
    assert.throws(() => normalizeLine({ ...item, modifiers: { size: 'large' } }));
    assert.throws(() => normalizeLine({ ...item, options: JSON.parse('{"__proto__":"bad"}') }));
});
