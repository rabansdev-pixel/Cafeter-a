// Re-render only the native widget when the site's theme changes.
(() => {
  const widget = document.querySelector('.access-captcha .g-recaptcha');
  if (!widget) return;
  let widgetId;
  let renderedTheme;
  window.renderAccessCaptcha = () => {
    const api = window.grecaptcha?.enterprise;
    if (!api) return;
    const theme = document.documentElement.dataset.homeTheme === 'light' ? 'light' : 'dark';
    if (theme === renderedTheme) return;
    if (widgetId !== undefined) api.reset(widgetId);
    widget.replaceChildren();
    widgetId = api.render(widget, {
      sitekey: widget.dataset.sitekey,
      theme,
      size: widget.parentElement.clientWidth >= 304 ? 'normal' : 'compact',
    });
    renderedTheme = theme;
  };
  window.resetAccessCaptcha = () => {
    if (widgetId !== undefined) window.grecaptcha.enterprise.reset(widgetId);
  };
  new MutationObserver(() => window.renderAccessCaptcha()).observe(document.documentElement, {
    attributes:true, attributeFilter:['data-home-theme'],
  });
})();
