// Search enhances the complete, server-rendered menu; no JavaScript is required to browse.
const search = document.querySelector('#menu-search');
if (search) {
    const entries = [...document.querySelectorAll('[data-menu-entry]')];
    const chapters = [...document.querySelectorAll('.menu-chapter')];
    const normal = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
    const update = () => {
        const terms = normal(search.value).split(/\s+/).filter(Boolean);
        let count = 0;
        entries.forEach(entry => {
            const match = terms.every(term => normal(entry.dataset.search).includes(term));
            entry.hidden = !match;
            if (match) count++;
        });
        chapters.forEach(chapter => { chapter.hidden = ![...chapter.querySelectorAll('[data-menu-entry]')].some(entry => !entry.hidden); });
        document.querySelector('[data-menu-results]').textContent = `${count} ${count === 1 ? 'producto' : 'productos'} · Precios en USD`;
        document.querySelector('[data-menu-empty]').hidden = count > 0;
    };
    search.addEventListener('input', update);
    document.querySelectorAll('.menu-category-nav a[href^="#"]').forEach(link => {
        link.addEventListener('click', () => { search.value = ''; update(); });
    });
}
