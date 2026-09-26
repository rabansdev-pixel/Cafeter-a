# Acceso con Firebase Authentication

Firebase controla la identidad; PostgreSQL conserva los productos, datos locales y permisos. No se ha activado Analytics ni se ha trasladado el catálogo a Firestore.

## Configuración

`.env` local ya contiene la configuración pública de la app web proporcionada por el propietario. En el servicio web de Railway añade las mismas variables, sin sustituir DATABASE_URL ni SECRET_KEY:

```dotenv
AUTH_PROVIDER=firebase
FIREBASE_API_KEY=valor_de_tu_app_web
FIREBASE_PROJECT_ID=zeroday-35ccc
FIREBASE_AUTH_DOMAIN=zeroday-35ccc.firebaseapp.com
FIREBASE_APP_ID=valor_de_tu_app_web
```

En Firebase → Authentication:

1. En Método de acceso, habilita Google y guarda el correo de asistencia. Puedes poner ZERO DAY como nombre público.
2. Habilita Correo electrónico/contraseña si también quieres usar los formularios de registro, acceso y recuperación.
3. En Configuración → Dominios autorizados añade `localhost`, `127.0.0.1` y el dominio del sitio en Railway (sin protocolo ni puerto). Si accedes por otro hostname, también debe estar autorizado.

La configuración web no es una cuenta de servicio. No hace falta descargar claves privadas para esta implementación: Google verifica sus credenciales y el backend valida tokens firmados con los certificados públicos del proyecto.

## Flujo

- Google: el SDK abre la ventana de Google, envía el ID token al endpoint CSRF protegido `/api/auth/firebase/session` y elimina su sesión en memoria tras el intercambio. El backend valida firma, audiencia, emisor, caducidad, proveedor y acceso reciente; consulta además si la cuenta está deshabilitada o revocada.
- Contraseña: el formulario envía las credenciales al backend y este autentica mediante la API REST oficial de Firebase. No se guarda la contraseña ni se registra en logs.
- Registro público: siempre asigna `customer`. El navegador no puede seleccionar ni enviar roles administrativos.
- Recuperación: Firebase envía el enlace a petición del usuario. No se envían correos durante la instalación. El resultado mostrado no revela si el correo existe.
- Cierre: elimina la sesión almacenada en PostgreSQL y la cookie de sesión de Flask.

## Tu administrador existente

Selecciona en Google **el mismo correo** con el que creaste el administrador. Para vincularlo por primera vez, escribe la contraseña anterior de ZERO DAY en el campo Contraseña y pulsa Continuar con Google. El backend comprueba esa contraseña antes de conservar el rol. Coincidir en el correo, por sí solo, no concede permisos.

Si usas correo/contraseña y la cuenta aún no existe en Firebase, el primer acceso correcto con la contraseña antigua la crea y vincula automáticamente. Si ya existe en Firebase con otra contraseña, usa el acceso con Google y la contraseña antigua para demostrar que controlas ambos accesos. No se sobrescriben cuentas ajenas ni contraseñas Firebase existentes.

Tras vincular, se elimina el hash de la contraseña local y Firebase pasa a ser la autoridad de acceso. `reset-password` ya no cambia contraseñas de cuentas vinculadas; usa Recuperar acceso/Firebase. `create-admin` sigue permitiendo crear un administrador local inicial que se vincula en su primer acceso.

## Sesiones y base de datos

- `usuarios.firebase_uid`: identificador único Firebase; no reemplaza el ID local ni los roles.
- `sesiones_firebase`: tokens cifrados en servidor con una clave derivada de SECRET_KEY; la cookie solo contiene identificadores, nunca el token de Firebase.
- Duración máxima: una hora (caducidad del ID token). Después se requiere iniciar sesión nuevamente. No se almacenan refresh tokens.
- Cada cinco minutos se revalida la sesión con Firebase para detectar revocaciones/bajas. Entre esas comprobaciones se valida en PostgreSQL; no se contacta con Google en cada navegación.
- Las bajas/cambios de roles locales se aplican con `session_version` inmediatamente. Una indisponibilidad de Firebase no concede acceso saltándose la comprobación.
- Las sesiones caducadas se purgan al iniciar una nueva sesión. Rotar SECRET_KEY invalida los tokens cifrados y las cookies anteriores.

Migración: `20260925_firebase_auth`. Instalación o despliegue:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/flask --app run:app db upgrade
```

El SDK web ya estaba instalado en el proyecto. El archivo servido por Flask se genera con `npm run build:auth`; el compilado está en `app/static/js/firebase-login.js`. No se requieren CDNs de módulos ni ejecutar React para el login.

No se ejecutaron pruebas, ni se creó una cuenta de ejemplo, ni se completó una sesión de Google en nombre del propietario. Para completar el acceso interactivo, el propietario debe guardar el proveedor en Firebase y elegir su cuenta en la ventana de Google.

Referencias oficiales: [Google en la web](https://firebase.google.com/docs/auth/web/google-signin), [validación de ID tokens](https://firebase.google.com/docs/auth/admin/verify-id-tokens), [API REST de Authentication](https://firebase.google.com/docs/reference/rest/auth).
