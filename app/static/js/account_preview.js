// Presentation only: no credentials, sessions or mutations are handled here.
const search = document.querySelector('[data-admin-search]');
const category = document.querySelector('[data-admin-category]');
if (search && category) {
    const rows = [...document.querySelectorAll('[data-admin-row]')];
    const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const update = () => {
        const terms = normalize(search.value).trim().split(/\s+/).filter(Boolean);
        let count = 0;
        rows.forEach(row => {
            const matches = (!category.value || row.dataset.category === category.value)
                && terms.every(term => normalize(row.dataset.search).includes(term));
            row.hidden = !matches;
            if (matches) count++;
        });
        document.querySelector('[data-admin-count]').textContent = `${count} ${count === 1 ? 'producto' : 'productos'}`;
        document.querySelector('[data-admin-empty]').hidden = count > 0;
    };
    search.addEventListener('input', update);
    category.addEventListener('change', update);
}
