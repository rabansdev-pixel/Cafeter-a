// Native POST is preserved. Feedback only, with no stored credentials.
(() => {
  const form = document.querySelector('[data-access-form]');
  const button = form?.querySelector('button[type="submit"]');
  if (!button) return;
  const label = button.textContent;
  let submitting = false;
  form.addEventListener('submit', event => {
    if (submitting) { event.preventDefault(); return; }
    submitting = true;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    button.textContent = label.trim() === 'Entrar' ? 'Entrando…' : 'Enviando…';
  });
  window.addEventListener('pageshow', () => {
    submitting = false;
    button.disabled = false;
    button.removeAttribute('aria-busy');
    button.textContent = label;
  });
})();
