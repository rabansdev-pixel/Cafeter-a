# Cafeter-a
Proyecto de cafetería

## Pruebas y cobertura

Con el entorno Python activado y Node.js 24 instalado:

```bash
python -m pip install -r requirements.txt
npm ci
pytest
pytest --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --junitxml=test-report.xml
npm run test:coverage
```

Sonar importa `coverage.xml` (Python) y `coverage-js/lcov.info` (JavaScript).
Los tests JavaScript usan el DOM de jsdom y el runner de Node; c8 genera LCOV.
Estas herramientas son dependencias de desarrollo, no del frontend servido.

## CSRF

Flask-WTF protege las peticiones POST, PUT, PATCH y DELETE en todos los entornos,
incluidas las pruebas. No hay rutas exentas. El carrito lee el token de la
etiqueta `meta[name="csrf-token"]` y lo envía mediante `X-CSRFToken`.
Los clientes externos deben obtener el token de una página y conservar su cookie
de sesión. Los futuros formularios POST deben incluir un campo oculto
`csrf_token` con el valor de `{{ csrf_token() }}`.

En producción se exige `SECRET_KEY` en el entorno: debe ser aleatoria, estable
y compartida entre los workers. No uses las claves de ejemplo de Docker/.env.
Un token caducado o inválido devuelve HTTP 400; el carrito indica que se recargue
la página. Tras estos cambios, revisa el flujo del carrito también en el navegador
con HTTPS y la configuración real del proxy.
