# Administración: React y fotografías reales

La referencia principal es el componente `dashboard-with-collapsible-sidebar` aportado por el usuario: navegación lateral plegable, cuatro indicadores y actividad con columna auxiliar. Se conserva Almarai, los temas y el acento de ZERO DAY. El patrón de formularios y foco sigue la guía craft-details de Refero Design; la consulta de Refero MCP no estuvo disponible por suscripción. No se inventan ventas, pedidos, usuarios, porcentajes ni imágenes.

El proyecto sigue usando Flask/Jinja. React se monta únicamente en la barra lateral administrativa y el resumen; productos, permisos, sesiones y formularios continúan en el backend existente. Los datos se serializan desde consultas autorizadas de PostgreSQL. El registro de actividad y el conteo de clientes solo se entregan a administradores.

## Estructura y compilación

- `components/ui/dashboard-with-collapsible-sidebar.tsx`: adaptación del componente con props tipadas, sin datos de demostración.
- `frontend/admin.tsx`: montaje de React.
- `frontend/admin.css`: Tailwind con prefijo `tw`, sin preflight global, y estilos limitados al panel.
- `components.json`, `tsconfig.json`, `lib/utils.ts`: estructura y alias compatibles con shadcn. `components/ui` permite mantener los componentes separados de plantillas y usar el alias `@/components/ui`; no es una exigencia de Flask.
- `app/static/admin/`: archivos compilados servidos por Flask, incluidos en el repositorio para despliegues Python sin Node.

Para recompilar cambios del componente:

```bash
npm ci
npm run build:admin
```

No hace falta convertir el sitio a Next.js ni ejecutar `shadcn init` sobre los estilos existentes. React, React DOM, lucide-react, TypeScript, esbuild y Tailwind ya están configurados en package.json.

## Fotografías

En Crear/Editar producto, “Seleccionar imagen” abre el explorador de archivos. Admite JPG, PNG y WebP, hasta 8 MB y 24 megapíxeles. La vista previa local se marca pendiente; solo se guarda al enviar el formulario. Una foto seleccionada tiene prioridad sobre la URL; sin una selección nueva se conserva la actual.

El servidor verifica y decodifica el contenido, rechaza animaciones e imágenes inválidas, corrige orientación y genera WebP de hasta 2000 px, sin metadatos. La foto se guarda en `imagenes_productos.data` (BYTEA) dentro de la misma transacción que el producto: un error de validación revierte ambos. La URL inmutable queda en `productos.image_url`. Las fotos anteriores se conservan; no se eliminan archivos ni datos automáticamente.

Este almacenamiento persiste en Railway sin depender del disco efímero del servicio web. Para un catálogo muy grande convendrá migrar los binarios a almacenamiento de objetos; el catálogo actual no necesita otro servicio configurado.

Migración requerida en nuevas instalaciones/despliegues:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/flask --app run:app db upgrade
```

Fuentes técnicas: [Pillow Image](https://pillow.readthedocs.io/en/stable/reference/Image.html), [Tailwind CLI](https://tailwindcss.com/docs/installation/tailwind-cli).

No se ejecutaron pruebas ni se abrió un navegador. La compilación genera los archivos necesarios para servir el componente.
