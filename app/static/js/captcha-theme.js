// Set native widget options before Google's asynchronous script renders it.
(() => {
  const widget = document.querySelector('.access-captcha .g-recaptcha');
  if (!widget) return;
  widget.dataset.theme = document.documentElement.dataset.homeTheme === 'light' ? 'light' : 'dark';
  widget.dataset.size = widget.parentElement.clientWidth >= 304 ? 'normal' : 'compact';
})();
