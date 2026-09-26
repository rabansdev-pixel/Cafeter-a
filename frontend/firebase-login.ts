import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, inMemoryPersistence, setPersistence, signInWithPopup, signOut } from 'firebase/auth';

const root = document.querySelector<HTMLElement>('[data-firebase-login]');
if (root) {
  const button = root.querySelector<HTMLButtonElement>('[data-google-login]')!;
  const message = root.querySelector<HTMLElement>('[data-firebase-message]')!;
  const labels: Record<string,string> = {
    'auth/unauthorized-domain': 'Este dominio no está autorizado en Firebase. Añádelo en Authentication → Configuración → Dominios autorizados.',
    'auth/operation-not-allowed': 'El acceso con Google todavía no está habilitado en Firebase.',
    'auth/popup-blocked': 'Permite las ventanas emergentes de esta página y vuelve a intentarlo.',
    'auth/popup-closed-by-user': 'Se cerró la ventana de Google. Puedes volver a intentarlo.',
    'auth/cancelled-popup-request': 'Ya hay una ventana de acceso abierta.',
    'auth/network-request-failed': 'No se pudo conectar con Google. Revisa tu conexión.',
    'auth/invalid-api-key': 'La configuración de Firebase necesita revisión.',
    'auth/account-exists-with-different-credential': 'Ese correo utiliza otro método de acceso. Inicia sesión con tu contraseña.',
  };
  try {
    const config = JSON.parse(root.dataset.firebaseLogin!);
    const auth = getAuth(initializeApp(config));
    auth.languageCode = 'es';
    const provider = new GoogleAuthProvider();
    provider.setCustomParameters({prompt: 'select_account'});
    setPersistence(auth, inMemoryPersistence).then(() => { button.disabled = false; }).catch(() => {
      message.textContent = 'No se pudo preparar el acceso con Google. Recarga la página.';
    });
    button.addEventListener('click', async () => {
      const captcha = document.querySelector<HTMLTextAreaElement>('[name="g-recaptcha-response"]');
      const captchaToken = captcha?.value || '';
      if (document.querySelector('.g-recaptcha') && !captchaToken) {
        message.textContent = 'Completa el captcha antes de continuar con Google.';
        document.querySelector<HTMLElement>('.g-recaptcha')?.scrollIntoView({block: 'center'});
        return;
      }
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      message.textContent = 'Abriendo Google…';
      try {
        const credential = await signInWithPopup(auth, provider);
        message.textContent = 'Comprobando tu cuenta…';
        const token = await credential.user.getIdToken();
        const password = document.querySelector<HTMLInputElement>('#access-password')?.value || '';
        const csrf = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content || '';
        const response = await fetch(root.dataset.sessionUrl!, {
          method: 'POST', credentials: 'same-origin',
          headers: {'Content-Type':'application/json', 'X-CSRFToken':csrf},
          body: JSON.stringify({id_token:token, legacy_password:password, captcha_token:captchaToken}),
        });
        const data = await response.json();
        if (!response.ok) {
          message.textContent = data.message || 'No se pudo iniciar sesión. Recarga la página e inténtalo de nuevo.';
          if (data.code === 'LINK_REQUIRED') document.querySelector<HTMLInputElement>('#access-password')?.focus();
          return;
        }
        const target = new URL(data.redirect, window.location.origin);
        if (target.origin !== window.location.origin) throw new Error('Invalid redirect');
        await signOut(auth);
        window.location.assign(target.href);
      } catch (error) {
        const code = (error as {code?:string}).code || '';
        message.textContent = labels[code] || 'No se pudo completar el acceso con Google. Inténtalo otra vez.';
      } finally {
        // Firebase credentials live only in memory; PostgreSQL owns the website session.
        await signOut(auth).catch(() => {});
        const recaptcha = (window as unknown as {grecaptcha?: {enterprise?: {reset: () => void}}}).grecaptcha;
        recaptcha?.enterprise?.reset();
        button.disabled = false;
        button.removeAttribute('aria-busy');
      }
    });
  } catch {
    message.textContent = 'La configuración de Firebase necesita revisión.';
  }
}
