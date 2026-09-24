// Progressive enhancement: all products and category links work without this module.
export function initMenuDiscovery(root = document) {
    const search = root.querySelector('#menu-search');
    if (!search) return;
    const entries = [...root.querySelectorAll('[data-menu-entry]')];
    const chapters = [...root.querySelectorAll('.menu-chapter')];
    const links = [...root.querySelectorAll('.menu-category-nav a[href^="#"]')];
    const normal = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
    const searchable = new Map(entries.map(entry => [entry, normal(entry.dataset.search)]));
    const behavior = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth';
    const railUpdates = [];

    chapters.forEach(chapter => {
        const rail = chapter.querySelector('[data-product-rail]');
        const controls = chapter.querySelector('[data-rail-controls]');
        if (!rail || !controls) return;
        const previous = controls.querySelector('[data-rail-prev]');
        const next = controls.querySelector('[data-rail-next]');
        const updateRail = () => {
            const end = rail.scrollWidth - rail.clientWidth;
            const overflowing = !chapter.hidden && end > 2;
            controls.hidden = !overflowing;
            previous.disabled = rail.scrollLeft <= 2;
            next.disabled = rail.scrollLeft >= end - 2;
            rail.tabIndex = overflowing ? 0 : -1;
        };
        previous.addEventListener('click', () => rail.scrollBy({ left: -rail.clientWidth * .85, behavior: behavior() }));
        next.addEventListener('click', () => rail.scrollBy({ left: rail.clientWidth * .85, behavior: behavior() }));
        rail.addEventListener('scroll', updateRail, { passive: true });
        if (window.ResizeObserver) {
            const observer = new window.ResizeObserver(updateRail);
            observer.observe(rail);
        } else {
            window.addEventListener('resize', updateRail, { passive: true });
        }
        railUpdates.push(updateRail);
        updateRail();
    });

    const update = () => {
        const terms = normal(search.value).split(/\s+/).filter(Boolean);
        let count = 0;
        entries.forEach(entry => {
            const match = terms.every(term => searchable.get(entry).includes(term));
            entry.hidden = !match;
            if (match) count++;
        });
        chapters.forEach(chapter => {
            chapter.hidden = ![...chapter.querySelectorAll('[data-menu-entry]')].some(entry => !entry.hidden);
            chapter.querySelector('[data-product-rail]')?.scrollTo({ left: 0, behavior: 'instant' });
        });
        root.querySelector('[data-menu-results]').textContent = `${count} ${count === 1 ? 'producto' : 'productos'} · Precios en USD`;
        root.querySelector('[data-menu-empty]').hidden = count > 0;
        links.forEach(link => {
            if (root.querySelector(link.hash)?.hidden) link.removeAttribute('aria-current');
        });
        const url = new URL(window.location.href);
        if (search.value.trim()) url.searchParams.set('q', search.value.trim());
        else url.searchParams.delete('q');
        window.history.replaceState(null, '', url);
        railUpdates.forEach(refresh => refresh());
    };
    search.addEventListener('input', update);
    links.forEach(link => {
        link.addEventListener('click', () => {
            search.value = '';
            update();
            links.forEach(other => other.removeAttribute('aria-current'));
            link.setAttribute('aria-current', 'location');
        });
    });
    root.querySelector('[data-shop-search]')?.addEventListener('submit', event => {
        event.preventDefault();
        update();
        const destination = root.querySelector('.menu-chapter:not([hidden]) h2') || root.querySelector('[data-menu-empty]');
        destination.tabIndex = -1;
        destination.focus({ preventScroll: true });
        destination.scrollIntoView({ behavior: behavior(), block: 'center' });
    });
    search.value = new URL(window.location.href).searchParams.get('q') || search.value;
    update();
}

initMenuDiscovery();
