export function initNavigation() {
    const header = document.querySelector('.site-header');
    const toggle = header?.querySelector('.menu-toggle');
    if (!toggle) return;
    const nav = header.querySelector('.site-nav');
    const actions = document.querySelector('.header-actions');
    const anchor = document.createComment('header actions');
    actions?.before(anchor);
    const mobile = matchMedia('(max-width: 767px)');
    const main = document.querySelector('main');
    const footer = document.querySelector('.site-footer');
    header.classList.add('menu-ready');
    const close = () => {
        header.classList.remove('menu-open');
        document.body.classList.remove('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-label', 'Abrir menú');
        if (main) main.inert = false;
        if (footer) footer.inert = false;
    };
    const relocate = () => {
        close();
        if (actions) mobile.matches ? nav.append(actions) : anchor.after(actions);
    };
    relocate();
    mobile.addEventListener('change', relocate);
    toggle.addEventListener('click', () => {
        if (header.classList.contains('menu-open')) return close();
        header.classList.add('menu-open');
        toggle.setAttribute('aria-expanded', 'true');
        toggle.setAttribute('aria-label', 'Cerrar menú');
        if (mobile.matches) {
            document.body.classList.add('mobile-nav-open');
            if (main) main.inert = true;
            if (footer) footer.inert = true;
        }
    });
    header.addEventListener('keydown', event => {
        if (event.key === 'Escape') { close(); toggle.focus(); }
        if (event.key === 'Tab' && mobile.matches && header.classList.contains('menu-open')) {
            const items = [...header.querySelectorAll('a,button,summary')].filter(el => el.getClientRects().length && !el.hidden);
            const first = items[0], last = items[items.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
        }
    });
    document.addEventListener('click', event => {
        if (header.classList.contains('menu-open') && !header.contains(event.target)) close();
        else if (event.target === header) close();
    });
    header.querySelectorAll('a').forEach(link => link.addEventListener('click', close));
    header.addEventListener('focusout', event => {
        if (!header.contains(event.relatedTarget)) close();
    });
}
