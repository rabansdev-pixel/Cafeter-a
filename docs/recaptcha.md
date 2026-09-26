# Captcha de acceso

Se utiliza el checkbox de reCAPTCHA Enterprise en acceso, registro y recuperación, incluido el acceso con Google. El backend verifica cada token mediante assessments, su validez y el hostname. Los tokens caducados o reutilizados se rechazan. Los checkbox no usan la comparación expectedAction ni un umbral de score propio de claves basadas en puntuación.

Variables en .env y Railway:

- RECAPTCHA_SITE_KEY: clave pública de tipo checkbox.
- RECAPTCHA_PROJECT_ID: proyecto Google Cloud propietario de esa clave. Confirmar que sea zeroday-35ccc.
- RECAPTCHA_API_KEY: credencial del servidor, restringida a reCAPTCHA Enterprise API. No usar automáticamente la clave pública de Firebase. Habilitar esa API en el proyecto.
- RECAPTCHA_ALLOWED_HOSTS: hostnames exactos separados por comas, sin esquema ni puerto. También autorizarlos en la configuración de la clave de Google.

Con SITE_KEY configurada, la verificación es obligatoria: si falta la credencial del servidor se rechaza el acceso. Reiniciar la aplicación después de configurar las variables. No se requieren migraciones. App Check es una integración distinta.
