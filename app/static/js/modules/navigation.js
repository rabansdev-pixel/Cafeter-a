export function initNavigation() {
    const header = document.querySelector('.site-header');
    const toggle = header?.querySelector('.menu-toggle');
    if (!toggle) return;
    header.classList.add('menu-ready');
    const close = () => {
        header.classList.remove('menu-open');
        toggle.setAttribute('aria-expanded', 'false');
    };
    toggle.addEventListener('click', () => {
        const open = header.classList.toggle('menu-open');
        toggle.setAttribute('aria-expanded', String(open));
    });
    header.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            close();
            toggle.focus();
        }
    });
    header.querySelectorAll('a, .js-open-cart').forEach(link => link.addEventListener('click', close));
    header.addEventListener('focusout', event => {
        if (!header.contains(event.relatedTarget)) close();
    });
}
