document.querySelectorAll('[data-profile-photo]').forEach(image => {
    const fallback = () => image.remove();
    image.addEventListener('error', fallback, {once:true});
    if (image.complete && !image.naturalWidth) fallback();
});
document.addEventListener('click', event => {
    document.querySelectorAll('.account-profile[open]').forEach(menu => { if (!menu.contains(event.target)) menu.open = false; });
});
document.addEventListener('keydown', event => {
    if (event.key === 'Escape') document.querySelectorAll('.account-profile[open]').forEach(menu => { menu.open = false; menu.querySelector('summary').focus(); });
});
