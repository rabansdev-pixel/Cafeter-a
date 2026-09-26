const input = document.querySelector('[data-product-photo]');
if (input) {
    const preview = document.querySelector('[data-photo-preview]');
    const status = document.querySelector('[data-photo-status]');
    const original = preview.getAttribute('src');
    let objectURL;
    input.addEventListener('change', () => {
        if (objectURL) URL.revokeObjectURL(objectURL);
        input.setCustomValidity('');
        const file = input.files[0];
        preview.hidden = !original;
        if (original) preview.src = original;
        status.textContent = '';
        if (!file) return;
        if (file.size > 8 * 1024 * 1024 || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
            input.setCustomValidity('Selecciona una imagen JPG, PNG o WebP de hasta 8 MB.');
            status.textContent = input.validationMessage;
            return;
        }
        objectURL = URL.createObjectURL(file);
        preview.src = objectURL;
        preview.hidden = false;
        status.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB · Pendiente de guardar`;
    });
    window.addEventListener('pagehide', () => { if (objectURL) URL.revokeObjectURL(objectURL); });
}
