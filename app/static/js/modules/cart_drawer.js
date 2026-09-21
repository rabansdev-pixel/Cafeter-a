/**
 * Módulo: CartDrawer
 * Carrito lateral flotante con recálculo dinámico en tiempo real y persistencia local.
 * Implementado con manipulación segura del DOM (sin innerHTML) para eliminar DOM-based XSS (Snyk CWE-79).
 */

function createEmptyCartNode() {
    const wrap = document.createElement('div');
    wrap.style.textAlign = 'center';
    wrap.style.padding = '3rem 1rem';
    wrap.style.color = 'var(--color-text-muted)';

    const icon = document.createElement('p');
    icon.style.fontSize = '2rem';
    icon.style.marginBottom = '0.5rem';
    icon.textContent = '☕';

    const title = document.createElement('p');
    title.textContent = 'Tu carrito de especialidad está vacío.';

    const sub = document.createElement('small');
    sub.textContent = 'Elige un microlote y experimenta notas únicas.';

    wrap.appendChild(icon);
    wrap.appendChild(title);
    wrap.appendChild(sub);
    return wrap;
}

function createCartItemNode(item) {
    const itemEl = document.createElement('div');
    itemEl.className = 'cart-item';

    // Sección izquierda (imagen y textos)
    const leftDiv = document.createElement('div');
    leftDiv.style.display = 'flex';
    leftDiv.style.gap = '0.75rem';
    leftDiv.style.alignItems = 'center';

    const img = document.createElement('img');
    img.src = String(item.image_url || '').replace(
        /^(\/static\/img\/products\/(?:geisha-huila|yirgacheffe|borbon-rosado|kenia-nyeri))\.svg$/, '$1.webp'
    );
    img.alt = String(item.name || '');
    img.style.width = '48px';
    img.style.height = '48px';
    img.style.objectFit = 'contain';

    const textDiv = document.createElement('div');
    const title = document.createElement('h4');
    title.style.fontSize = '0.9rem';
    title.style.fontFamily = 'var(--font-body)';
    title.textContent = String(item.name || '');

    const price = document.createElement('small');
    price.style.color = 'var(--color-accent-gold)';
    const numPrice = Number(item.price) || 0;
    price.textContent = `$${numPrice.toLocaleString('es-CO')}`;

    textDiv.appendChild(title);
    textDiv.appendChild(price);
    leftDiv.appendChild(img);
    leftDiv.appendChild(textDiv);

    // Sección derecha (botones de cantidad y eliminar)
    const rightDiv = document.createElement('div');
    rightDiv.style.display = 'flex';
    rightDiv.style.alignItems = 'center';
    rightDiv.style.gap = '0.5rem';

    const decBtn = document.createElement('button');
    decBtn.className = 'cart-qty-btn';
    decBtn.dataset.action = 'dec';
    decBtn.dataset.id = String(item.id);
    decBtn.style.background = 'var(--color-bg-surface)';
    decBtn.style.border = '1px solid var(--glass-border)';
    decBtn.style.color = '#fff';
    decBtn.style.width = '26px';
    decBtn.style.height = '26px';
    decBtn.style.borderRadius = '4px';
    decBtn.style.cursor = 'pointer';
    decBtn.textContent = '-';
    decBtn.setAttribute('aria-label', `Reducir cantidad de ${item.name}`);

    const qtySpan = document.createElement('span');
    qtySpan.style.fontWeight = '700';
    qtySpan.style.fontSize = '0.85rem';
    qtySpan.textContent = String(item.quantity || 1);

    const incBtn = document.createElement('button');
    incBtn.className = 'cart-qty-btn';
    incBtn.dataset.action = 'inc';
    incBtn.dataset.id = String(item.id);
    incBtn.style.background = 'var(--color-bg-surface)';
    incBtn.style.border = '1px solid var(--glass-border)';
    incBtn.style.color = '#fff';
    incBtn.style.width = '26px';
    incBtn.style.height = '26px';
    incBtn.style.borderRadius = '4px';
    incBtn.style.cursor = 'pointer';
    incBtn.textContent = '+';
    incBtn.setAttribute('aria-label', `Aumentar cantidad de ${item.name}`);

    const delBtn = document.createElement('button');
    delBtn.className = 'cart-del-btn';
    delBtn.dataset.id = String(item.id);
    delBtn.style.background = 'transparent';
    delBtn.style.border = 'none';
    delBtn.style.color = '#ff5555';
    delBtn.style.cursor = 'pointer';
    delBtn.style.marginLeft = '0.35rem';
    delBtn.textContent = '✕';
    delBtn.setAttribute('aria-label', `Eliminar ${item.name} del carrito`);

    rightDiv.appendChild(decBtn);
    rightDiv.appendChild(qtySpan);
    rightDiv.appendChild(incBtn);
    rightDiv.appendChild(delBtn);

    itemEl.appendChild(leftDiv);
    itemEl.appendChild(rightDiv);
    return itemEl;
}

export function initCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-overlay');
    const openBtns = document.querySelectorAll('.js-open-cart');
    const closeBtn = document.getElementById('cart-close-btn');
    const itemsList = document.getElementById('cart-items-container');
    const subtotalEl = document.getElementById('cart-subtotal-val');
    const shippingEl = document.getElementById('cart-shipping-val');
    const totalEl = document.getElementById('cart-total-val');
    const countBadges = document.querySelectorAll('.cart-badge');
    const progressFill = document.getElementById('shipping-progress-fill');
    const shippingStatusText = document.getElementById('shipping-status-text');

    let cart = JSON.parse(localStorage.getItem('artisan_cafe_cart') || '[]');
    let returnFocus;

    function saveCart() {
        localStorage.setItem('artisan_cafe_cart', JSON.stringify(cart));
    }

    function openDrawer() {
        if (drawer && overlay) {
            if (!drawer.classList.contains('active')) returnFocus = document.activeElement;
            drawer.removeAttribute('inert');
            drawer.setAttribute('aria-hidden', 'false');
            drawer.classList.add('active');
            overlay.classList.add('active');
            closeBtn?.focus();
        }
    }

    function closeDrawer() {
        if (drawer && overlay) {
            drawer.classList.remove('active');
            overlay.classList.remove('active');
            if (drawer.contains(document.activeElement)) returnFocus?.focus();
            drawer.setAttribute('aria-hidden', 'true');
            drawer.setAttribute('inert', '');
        }
    }

    function replaceCartItems(...nodes) {
        const active = document.activeElement;
        const restoreFocus = itemsList.contains(active);
        itemsList.replaceChildren(...nodes);
        if (restoreFocus) {
            const replacement = [...itemsList.querySelectorAll('button')].find(button =>
                button.dataset.id === active.dataset.id &&
                button.dataset.action === active.dataset.action &&
                button.className === active.className
            );
            (replacement || closeBtn)?.focus();
        }
    }

    async function syncAndRender() {
        saveCart();

        // Actualizar badges de conteo
        const totalCount = cart.reduce((acc, item) => acc + (Number(item.quantity) || 1), 0);
        countBadges.forEach(b => {
            b.textContent = String(totalCount);
        });

        if (cart.length === 0) {
            if (itemsList) {
                replaceCartItems(createEmptyCartNode());
            }
            if (subtotalEl) subtotalEl.textContent = '$0';
            if (shippingEl) shippingEl.textContent = '$0';
            if (totalEl) totalEl.textContent = '$0';
            if (progressFill) progressFill.style.width = '0%';
            if (shippingStatusText) {
                shippingStatusText.textContent = 'Envío gratis en compras mayores a $50.000';
            }
            return;
        }

        // Renderizar items de forma segura con nodos DOM (Cero innerHTML)
        if (itemsList) {
            const itemNodes = cart.map(createCartItemNode);
            replaceCartItems(...itemNodes);
        }

        // Llamar API de Flask para cálculo seguro de totales
        try {
            const res = await fetch('/api/cart/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({ items: cart })
            });
            const result = await res.json();
            if (!res.ok) {
                showToast(result.message || 'No se pudo calcular el carrito. Inténtalo de nuevo.');
                return;
            }
            if (result.status === 'success') {
                const data = result.data;
                if (subtotalEl) subtotalEl.textContent = String(data.formatted_subtotal);
                if (shippingEl) shippingEl.textContent = String(data.formatted_shipping);
                if (totalEl) totalEl.textContent = String(data.formatted_total);

                if (progressFill && shippingStatusText) {
                    if (data.is_free_shipping) {
                        progressFill.style.width = '100%';
                        const strong = document.createElement('strong');
                        strong.textContent = 'Envío Gratis';
                        shippingStatusText.replaceChildren(
                            document.createTextNode('✨ ¡Felicidades! Tienes '),
                            strong
                        );
                    } else {
                        const pct = Math.min(100, Math.round((data.subtotal / 50000) * 100));
                        progressFill.style.width = `${pct}%`;
                        const strong = document.createElement('strong');
                        const remaining = Number(data.free_shipping_remaining) || 0;
                        strong.textContent = `$${remaining.toLocaleString('es-CO')}`;
                        shippingStatusText.replaceChildren(
                            document.createTextNode('Agrega '),
                            strong,
                            document.createTextNode(' para Envío Gratis')
                        );
                    }
                }
            }
        } catch (err) {
            console.error('Error calculating cart:', err);
        }
    }

    // Attach open/close listeners
    openBtns.forEach(btn => btn.addEventListener('click', openDrawer));
    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    if (overlay) overlay.addEventListener('click', closeDrawer);
    drawer?.addEventListener('keydown', event => {
        if (event.key === 'Escape') closeDrawer();
        if (event.key !== 'Tab') return;
        const controls = [...drawer.querySelectorAll('button, a[href]')].filter(control => !control.disabled);
        const first = controls[0];
        const last = controls.at(-1);
        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
        }
    });

    // Quantity / delete delegation
    if (itemsList) {
        itemsList.addEventListener('click', (e) => {
            const target = e.target;
            const itemId = Number.parseInt(target.dataset.id, 10);
            if (!itemId) return;

            if (target.classList.contains('cart-qty-btn')) {
                const action = target.dataset.action;
                const item = cart.find(i => i.id === itemId);
                if (item) {
                    if (action === 'inc') item.quantity += 1;
                    if (action === 'dec') item.quantity = Math.max(1, item.quantity - 1);
                }
            } else if (target.classList.contains('cart-del-btn')) {
                cart = cart.filter(i => i.id !== itemId);
            }
            syncAndRender();
        });
    }

    // Add to cart buttons globally
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.js-add-to-cart');
        if (!btn) return;

        const id = Number.parseInt(btn.dataset.id, 10);
        const name = btn.dataset.name;
        const price = Number.parseFloat(btn.dataset.price);
        const image_url = btn.dataset.image;

        const existing = cart.find(i => i.id === id);
        if (existing) {
            existing.quantity += 1;
        } else {
            cart.push({ id, name, price, image_url, quantity: 1 });
        }

        syncAndRender();
        openDrawer();
        showToast(`☕ "${name}" añadido al carrito`);
    });

    // Simple toast helper
    function showToast(message) {
        const toastContainer = document.querySelector('.toast-container') || (() => {
            const el = document.createElement('div');
            el.className = 'toast-container';
            el.setAttribute('role', 'status');
            el.setAttribute('aria-live', 'polite');
            document.body.appendChild(el);
            return el;
        })();

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Checkout button listener
    const checkoutBtn = document.getElementById('cart-checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            if (cart.length === 0) {
                showToast('☕ Tu carrito está vacío.');
                return;
            }
            showToast('☕ Conectando pasarela de pago segura...');
        });
    }

    // Initial render
    syncAndRender();
}
