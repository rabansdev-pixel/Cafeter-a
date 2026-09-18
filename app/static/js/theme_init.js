/* Blocking, same-origin initialization: runs before styles and first paint.
   External file is required by the site's script-src 'self' CSP. */
(() => {
    let theme = 'dark';
    try {
        const saved = localStorage.getItem('zero-day-home-theme');
        theme = saved === 'light' || saved === 'dark'
            ? saved : (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    } catch (_) {}
    document.documentElement.dataset.homeTheme = theme;
})();
