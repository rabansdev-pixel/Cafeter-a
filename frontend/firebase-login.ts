import { initializeApp } from 'firebase/app';
import { getAuth, FacebookAuthProvider, GoogleAuthProvider, inMemoryPersistence, setPersistence, signInWithPopup, signOut } from 'firebase/auth';

const root = document.querySelector<HTMLElement>('[data-firebase-login]');
if (root) {
  const buttons = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-google-login], [data-facebook-login]')); 
  const message = root.querySelector<HTMLElement>('[data-firebase-message]')!;
  const labels: Record<string,string> = {
    'auth/unauthorized-domain': 'Este dominio no está autorizado en Firebase. Añádelo en Authentication → Configuración → Dominios autorizados.',
    'auth/operation-not-allowed': 'Este proveedor todavía no está habilitado en Firebase.',
    'auth/popup-blocked': 'Permite las ventanas emergentes de esta página y vuelve a intentarlo.',
    'auth/popup-closed-by-user': 'Se cerró la ventana de acceso. Puedes volver a intentarlo.',
    'auth/cancelled-popup-request': 'Ya hay una ventana de acceso abierta.',
    'auth/network-request-failed': 'No se pudo conectar con el proveedor. Revisa tu conexión.',
    'auth/invalid-api-key': 'La configuración de Firebase necesita revisión.',
    'auth/account-exists-with-different-credential': 'Ese correo utiliza otro método de acceso. Usa el método con el que creaste tu cuenta.',
  };
  try {
    const config = JSON.parse(root.dataset.firebaseLogin!);
    const auth = getAuth(initializeApp(config));
    auth.languageCode = 'es';

    setPersistence(auth, inMemoryPersistence).then(() => { buttons.forEach(item => { item.disabled = false; }); }).catch(() => {
      message.textContent = 'No se pudo preparar el acceso social. Recarga la página.';
    });
    buttons.forEach(button => button.addEventListener('click', async () => {
      const isFacebook = button.hasAttribute('data-facebook-login');
      const provider = isFacebook ? new FacebookAuthProvider() : new GoogleAuthProvider();
      if (isFacebook) provider.addScope('email');
      else provider.setCustomParameters({prompt: 'select_account'});
      const captcha = document.querySelector<HTMLTextAreaElement>('[name="g-recaptcha-response"]');
      const captchaToken = captcha?.value || '';
      if (document.querySelector('.g-recaptcha') && !captchaToken) {
        message.textContent = 'Completa el captcha antes de continuar.';
        document.querySelector<HTMLElement>('.g-recaptcha')?.scrollIntoView({block: 'center'});
        return;
      }
      buttons.forEach(item => { item.disabled = true; });
      button.setAttribute('aria-busy', 'true');
      message.textContent = isFacebook ? 'Abriendo Facebook…' : 'Abriendo Google…';
      try {
        const credential = await signInWithPopup(auth, provider);
        message.textContent = 'Comprobando tu cuenta…';
        const token = await credential.user.getIdToken();
        const password = document.querySelector<HTMLInputElement>('#access-password')?.value || '';
        const csrf = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content || '';
        const response = await fetch(root.dataset.sessionUrl!, {
          method: 'POST', credentials: 'same-origin',
          headers: {'Content-Type':'application/json', 'X-CSRFToken':csrf},
          body: JSON.stringify({id_token:token, refresh_token:credential.user.refreshToken, legacy_password:password, captcha_token:captchaToken}),
        });
        const data = await response.json();
        if (!response.ok) {
          message.textContent = data.message || 'No se pudo iniciar sesión. Recarga la página e inténtalo de nuevo.';
          if (data.code === 'LINK_REQUIRED') document.querySelector<HTMLInputElement>('#access-password')?.focus();
          return;
        }
        await signOut(auth);
        if (data.redirect === '/admin') {
          window.location.assign('/admin');
        } else if (data.redirect === '/cuenta') {
          window.location.assign('/cuenta');
        } else {
          throw new Error('Invalid redirect');
        }
      } catch (error) {
        const code = (error as {code?:string}).code || '';
        message.textContent = labels[code] || 'No se pudo completar el acceso social. Inténtalo otra vez.';
      } finally {
        // Firebase credentials live only in memory; PostgreSQL owns the website session.
        await signOut(auth).catch(() => {});
        (window as unknown as {resetAccessCaptcha?: () => void}).resetAccessCaptcha?.();
        buttons.forEach(item => { item.disabled = false; });
        button.removeAttribute('aria-busy');
      }
    }));
  } catch {
    message.textContent = 'La configuración de Firebase necesita revisión.';
  }
}
