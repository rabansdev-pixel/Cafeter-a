# Tablas en DBeaver

En el esquema `public`, actualiza con F5 después de aplicar la migración.

| Tabla | Contenido |
|---|---|
| `productos` | Productos, precios, existencias y estado de publicación. |
| `categorias` | Grupos de la carta: cafés, bebidas frías, alimentos, etc. |
| `usuarios` | Cuentas de clientes y personal, roles y contraseñas protegidas con hash. |
| `imagenes_productos` | Fotografías subidas desde administración. |
| `registro_actividad` | Historial de cambios de productos y cuentas. |
| `intentos_acceso` | Contadores de intentos de acceso para limitar abusos. |
| `origenes` | País, región y finca de los cuatro cafés del catálogo antiguo. |
| `perfiles_cata` | Tueste y características sensoriales de esos cafés. |
| `alembic_version` | Versión técnica de la base de datos. No editar manualmente. |

Se renombran las tablas sin copiar ni eliminar registros. Las columnas, rutas web y contratos JSON se conservan para mantener compatibilidad. Reinicia el backend tras migrar; cualquier otro despliegue conectado a esta misma base debe recibir también los modelos actualizados.

```bash
.venv/bin/flask --app run:app db upgrade
```

Los nombres ingleses en las migraciones anteriores describen la estructura histórica y deben conservarse.

`sesiones_firebase` conserva las sesiones de acceso Firebase cifradas en servidor.
`usuarios.firebase_uid` identifica la cuenta vinculada sin cambiar su rol local.
