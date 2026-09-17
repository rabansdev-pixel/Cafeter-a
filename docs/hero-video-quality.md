# Calidad y entrega del hero ZERO DAY

Se optimizó únicamente el hero aprobado. El master `app/static/img/products/hero.mp4`
se conserva intacto (SHA-256 comprobado). No se cambió layout, tipografía, encuadre
responsive, ni otras secciones. No se ejecutaron suites de pruebas.

## Fuente inspeccionada con ffprobe

| Propiedad | Original |
| --- | --- |
| Resolución / proporción | 2560 × 1440 / 16:9 |
| Códec | H.264 High |
| Bitrate del video | 5.389 Mb/s |
| Bitrate total | 5.509 Mb/s |
| Fotogramas | 24 fps nominales; 23.9 fps promedio, 239 fotogramas |
| Duración | Video: 10 s; contenedor: 10.020334 s |
| Píxeles | yuvj420p, rango completo, primarias y matriz BT.709, transferencia sRGB |
| Audio | AAC estéreo, aproximadamente 128 kb/s |
| Tamaño | 6,900,591 bytes |

## Cambios

- H.264 CRF 17, preset slow, yuv420p y faststart a resolución nativa.
- VP9 CRF 24, calidad constante (`-b:v 0`), deadline good, cpu-used 2,
  row-mt; también a resolución nativa.
- MP4 móvil 1280 × 720, Lanczos, CRF 19 y preset slow.
- Todos los derivados eliminan audio. Conversión explícita de rango completo a
  limitado antes de codificar; no se limita a cambiar etiquetas de color.
- Póster WebP de calidad 95, 2560 × 1440, extraído del primer fotograma:
  coincide con el arranque y usa exactamente el mismo recorte y superposiciones.
- `preload="metadata"`, mute, loop y reproducción inline. Las fuentes se seleccionan
  al iniciar reproducción según pantalla y códec soportado. Los `source[data-src]`
  se mantienen diferidos para evitar descargas de escritorio en móviles y respetar
  ahorro de datos y movimiento reducido. No se cambia de fuente durante reproducción.
- Grano reducido de 0.045 a 0.015, conservando soft-light. Usar 0.08–0.15 aquí
  habría aumentado el ruido existente, contrario al objetivo.
- Degradado superior de 20 % a 8 % de negro, eliminación del oscurecimiento
  intermedio y extremo inferior de aproximadamente 67 % a 45 %.
- `filter: none`, `transform: none`, `backdrop-filter: none`. No sharpening,
  saturación ni contraste artificiales. La opacidad llega a 1 tras el fundido inicial.

| Derivado | Resolución | Bytes | Bitrate total |
| --- | --- | ---: | ---: |
| hero-v1-web.mp4 | 2560 × 1440 | 3,947,393 | 3.171 Mb/s |
| hero-v1-web.webm | 2560 × 1440 | 1,357,759 | 1.091 Mb/s |
| hero-v1-mobile.mp4 | 1280 × 720 | 1,059,998 | 0.852 Mb/s |

Los derivados tienen 24 fps y aproximadamente 9.959 s: la codificación normaliza
los timestamps iniciales del original. El master y los tres derivados permanecen
 disponibles para comparación.

## Escalado real en Chromium

`cover` usa `max(anchoContenedor/anchoFuente, altoContenedor/altoFuente)`.
Valores medidos con DPR 1, idénticos antes y después:

| Ventana | Área del video | Escala | Recorte vertical aproximado |
| --- | --- | ---: | ---: |
| 1366 × 768 | 1318 × 720 | 0.515× | 2.9 % |
| 1920 × 1080 | 1872 × 1032 | 0.731× | 2.0 % |
| 2560 × 1440 | 2512 × 1152 | 0.981× | 18.5 % |
| 3840 × 2160 | 3792 × 1152 | 1.481× | 46.0 % |

El máximo de altura existente de 1200 px hace el hero más panorámico en pantallas
grandes. El ancho determina el escalado: ampliar la altura a 16:9 reduciría el
recorte vertical, pero no la escala y sí cambiaría el layout aprobado. Por eso
se conserva. En móvil se conserva `object-position: 35% center`; centrarlo
cambiaría la composición existente.

Con ventana 2560 × 1440 y DPR 2 se midió una escala física de 1.963×. No hay
resolución suficiente para detalle nativo en todos esos píxeles. CSS o una
recodificación convencional no pueden recuperar detalle ausente.

## Comparación visual

Se capturó la implementación anterior y la optimizada en las cuatro resoluciones,
y se compararon detalles de taza, vapor y madera a 2560 × 1440 con el video
completamente opaco. La mejora visible procede principalmente de retirar parte
del velo oscuro, mostrando mejor la mesa y la taza. El fondo desenfocado pertenece
al propio original; no se intentó eliminarlo.

MP4 y WebM conservan una apariencia muy próxima al master en los detalles revisados;
no se observó una ventaja visual clara que justificara descargar el archivo mayor.
Se prioriza WebM compatible (aproximadamente 80 % menos bytes que el original),
con MP4 como alternativa de compatibilidad y MP4 ligero en móvil.
Esto es una valoración visual localizada, no una medición perceptual exhaustiva.

La variante C ampliada a 1440p **no aplica**: el master ya es 1440p. Crear
`hero-v1-1440p-test.mp4` sería otra recodificación de la misma resolución, sin
comparar escalado del navegador frente a preescalado. No se generó un duplicado
que sugiriese una mejora inexistente.

Capturas, implementación anterior y mediciones: `/tmp/hero-quality/`.
Se revisó la selección móvil y DPR 2 en Chromium; no se revisaron físicamente
pantallas Retina ni otros navegadores. Los archivos se sirven como assets estáticos,
sin base64; la política de caché del despliegue no se modificó.
