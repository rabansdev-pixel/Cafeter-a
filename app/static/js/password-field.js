(() => {
  const input = document.querySelector('#access-password');
  const toggle = document.querySelector('.password-toggle');
  if (!input || !toggle) return;
  toggle.hidden = false;
  const hide = () => {
    input.type = 'password';
    toggle.setAttribute('aria-label', 'Mostrar contraseña');
    toggle.setAttribute('aria-pressed', 'false');
    toggle.querySelector('.password-eye-slash').setAttribute('hidden', '');
  };
  toggle.addEventListener('click', () => {
    if (input.type === 'text') { hide(); return; }
    input.type = 'text';
    toggle.setAttribute('aria-label', 'Ocultar contraseña');
    toggle.setAttribute('aria-pressed', 'true');
    toggle.querySelector('.password-eye-slash').removeAttribute('hidden');
  });
  window.addEventListener('pagehide', hide);
  const guidance = document.querySelector('#password-guidance');
  if (!guidance) return;
  const update = () => {
    const length = Array.from(input.value).length;
    const meets = length >= 12 && length <= 256;
    const level = length === 0 ? 0 : length < 12 ? 1 : length < 16 ? 2 : 3;
    guidance.querySelectorAll('.password-meter span').forEach((bar, index) => {
      bar.classList.toggle('is-filled', index < level);
    });
    const status = length === 0 ? 'Usa al menos 12 caracteres.' : !meets
      ? (length > 256 ? 'Máximo: 256 caracteres.' : 'Todavía es demasiado corta.')
      : length < 16 ? 'Cumple el mínimo. Puedes hacerla más larga.' : 'Buena longitud. Asegúrate de que sea única.';
    const label = guidance.querySelector('[data-password-status]');
    if (label.textContent !== status) label.textContent = status;
    const minimum = guidance.querySelector('[data-password-minimum]');
    minimum.dataset.met = String(meets);
    minimum.textContent = meets ? '✓ Mínimo de 12 caracteres cumplido.' : 'Mínimo obligatorio: 12 caracteres.';
    input.setCustomValidity(length && !meets ? 'Usa entre 12 y 256 caracteres.' : '');
  };
  input.addEventListener('input', update);
  input.addEventListener('change', update);
  window.addEventListener('pageshow', update);
  update();
})();
