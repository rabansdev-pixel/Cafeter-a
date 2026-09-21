/* Presentation preference, shared across the public pages. */
(() => {
    const button = document.querySelector('.home-theme-toggle');
    if (!button) return;
    const root = document.documentElement;
    const preference = window.matchMedia('(prefers-color-scheme: light)');
    let explicit = false;
    try { explicit = ['light', 'dark'].includes(localStorage.getItem('zero-day-home-theme')); } catch (_) {}
    function render(theme) {
        root.dataset.homeTheme = theme;
        const light = theme === 'light';
        button.setAttribute('aria-pressed', String(light));
        button.setAttribute('aria-label', 'Tema claro');
        button.title = light ? 'Cambiar a tema oscuro' : 'Cambiar a tema claro';
        button.querySelector('[data-theme-label]').textContent = light ? 'Cambiar a tema oscuro' : 'Cambiar a tema claro';
    }
    render(root.dataset.homeTheme || 'dark');
    button.hidden = false;
    button.addEventListener('click', () => {
        const theme = root.dataset.homeTheme === 'light' ? 'dark' : 'light';
        explicit = true;
        render(theme);
        try { localStorage.setItem('zero-day-home-theme', theme); } catch (_) {}
    });
    preference.addEventListener('change', event => {
        if (!explicit) render(event.matches ? 'light' : 'dark');
    });
})();
