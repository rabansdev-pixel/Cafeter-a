import { CART_KEY, createCartStore } from './modules/cart_store.js';
let storage;
try { storage = window.localStorage; } catch { /* Storage may be disabled. */ }
export const cartStore = createCartStore(storage);
const paint = () => {
    const count = cartStore.get().reduce((sum, line) => sum + line.quantity, 0);
    document.querySelectorAll('[data-cart-nav]').forEach(el => { el.hidden = count === 0; });
    document.querySelectorAll('[data-cart-count]').forEach(el => { el.textContent = String(count); });
};
cartStore.subscribe(paint);
window.addEventListener('storage', event => { if (event.key === CART_KEY || event.key === null) cartStore.sync(); });
window.addEventListener('pageshow', () => { cartStore.sync(); paint(); });
paint();
