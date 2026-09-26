# PostgreSQL y cuentas de ZERO DAY

La aplicación utiliza exclusivamente `DATABASE_URL`. En local `.env` contiene la URL pública de Railway; en el servicio web de Railway debe usarse la referencia a la URL interna del mismo PostgreSQL. DBeaver y la aplicación consultan los mismos datos.

Configura también `SECRET_KEY` aleatoria y estable (mínimo 32 caracteres). Se generó una clave local en `.env`, sin publicarla. Configura una clave propia en las variables del servicio web de Railway. No publiques `.env` ni pases contraseñas como argumentos del shell.

## Instalación y despliegue

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/flask --app run:app db upgrade
.venv/bin/flask --app run:app seed-menu
.venv/bin/flask --app run:app create-admin
```

El último comando solicita correo, nombre y contraseña oculta con confirmación. No existen usuarios administrativos ni contraseñas predeterminados. El comando no promueve cuentas ya registradas; un administrador puede cambiar su rol desde el panel.

En Railway: `APP_ENV=production`, `SECRET_KEY` estable y `DATABASE_URL` interna. Ejecuta `flask --app run:app db upgrade` antes de arrancar el nuevo código (comando de predeploy); usa `flask --app run:app seed-menu` una vez para una base nueva. No se crean tablas ni productos automáticamente al iniciar un worker. Despliega los archivos del proyecto para activar estos cambios en el sitio alojado.

## Datos

- `productos`: conserva los cuatro productos antiguos. La tienda identifica sus productos con `menu_id` estable; los 24 existentes conservan sus identificadores `zd-*`, fotos, precios y opciones.
- Campos compatibles: `image_url` es la imagen (`image` en API), `is_active` es el estado (`active` en API), `category_id` enlaza `categorias`. Precio `NUMERIC(12,2)`; `created_at` y `updated_at`.
- `details` conserva porción, alérgenos, variantes y suplementos. Los precios del carrito se calculan en servidor, no con importes enviados por el navegador.
- Stock `NULL`: sin registrar, no implica una cantidad inventada. Stock 0: agotado. La cotización valida la suma de cantidades por producto, incluso entre variantes. No reserva ni descuenta stock: todavía no hay pedidos/pagos.
- `usuarios`: contraseñas con hash scrypt, roles `customer`, `staff`, `admin`. Registro público exclusivamente de clientes. Sesiones firmadas con validación de usuario activo y versión de sesión en base de datos.
- `registro_actividad`: cambios de productos, permisos y carga inicial. `intentos_acceso`: límite de intentos compartido entre procesos, con claves hash y ventana de 15 minutos.

`seed-menu` solamente inserta productos faltantes. No restaura precios ni sobrescribe cambios del administrador. La migración adopta las tablas antiguas y conserva sus registros; no hay downgrade destructivo automático.

## Acceso y CRUD

`/registro`, `/login`, `/cuenta`, `/admin`. Las antiguas rutas de vista previa también requieren autenticación. Personal y administradores pueden crear/editar/desactivar productos; únicamente administradores ven usuarios, cambian roles y consultan actividad. Desactivar equivale a baja lógica: conserva el registro y permite reactivarlo. El último administrador no puede quedar deshabilitado.

API:

- `GET /api/products`: productos publicados de la tienda.
- `GET /api/products/<slug>`: ficha pública.
- `GET /api/products/manage`: listado administrativo, incluidos inactivos.
- `POST /api/products`: crear.
- `GET|PUT|PATCH|DELETE /api/products/<id>`: consulta administrativa, edición o baja lógica.

Las escrituras requieren sesión de personal/administrador y CSRF. Enviar la cookie de sesión y `X-CSRFToken` con el token de la etiqueta meta de una página. Campos aceptados: `name`, `slug`, `description`, `tagline`, `price`, `category_id`, `image`, `stock`, `active` (booleano). No se permite asignación arbitraria de campos.

La recuperación por correo queda pendiente del servicio de correo. El carrito sigue guardándose en este dispositivo; las cuentas no crean un historial de pedidos ficticio.

## Pruebas existentes

No se ejecutaron suites ni navegador en esta ronda. Las fixtures antiguas borran tablas; el entorno `testing` queda bloqueado salvo que `DATABASE_URL` apunte explícitamente a una base desechable con nombre terminado en `_test` y `ALLOW_DATABASE_TESTS=1`. Nunca usar la base real para esas fixtures. Los tests anteriores deberán adaptarse a PostgreSQL y a los nuevos endpoints antes de ejecutarlos.

## Archivos de esta implementación

- `.env.example`
- `README.md`
- `app/__init__.py`
- `app/cli.py`
- `app/controllers/api/cart_api.py`
- `app/controllers/api/products_api.py`
- `app/controllers/web/account_controller.py`
- `app/controllers/web/main_controller.py`
- `app/core/config.py`
- `app/core/extensions.py`
- `app/models/__init__.py`
- `app/models/identity.py`
- `app/models/product.py`
- `app/repositories/product_repository.py`
- `app/services/auth_service.py`
- `app/services/menu_service.py`
- `app/services/store_service.py`
- `app/static/css/account.css`
- `app/static/js/account_preview.js`
- `app/static/js/commerce.js`
- `app/templates/components/navbar.html`
- `app/templates/layouts/account.html`
- `app/templates/pages/access.html`
- `app/templates/pages/account_preview.html`
- `app/templates/pages/admin_preview.html`
- `app/templates/pages/admin_product.html`
- `app/templates/pages/home.html`
- `app/templates/pages/menu.html`
- `docs/postgresql-accounts.md`
- `migrations/alembic.ini`
- `migrations/env.py`
- `migrations/script.py.mako`
- `migrations/versions/20260925_store_accounts.py`
- `requirements.txt`

También se generó `SECRET_KEY` en el `.env` local, excluido de Git.

## Actualización: Firebase

El acceso con Google/correo, la vinculación del administrador y la recuperación
están documentados en [Firebase Authentication](firebase-login.md). Una cuenta
vinculada ya no utiliza ni conserva su hash local de contraseña.
