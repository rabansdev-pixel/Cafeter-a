# ZERO DAY · Carta de 24 productos y ampliación editorial

Propuesta creada por encargo del propietario, 16 de septiembre de 2026. Los precios
son una propuesta en USD para Machala, no precios históricos de ZERO DAY ni una
confirmación de costos, recetas, inventario o márgenes del negocio.

## Referencias de mercado

Se consultaron cartas públicas de establecimientos con presencia en Machala:

- [Juan Valdez, Machala](https://www.ubereats.com/ec/store/juan-valdez-machala/nBuGflEoWK26J_SxKd74ug):
  americano mediano $2,50, cappuccino mediano $3,30 y latte grande $3,91.
- [Juan Valdez, Paseo Shopping Machala](https://www.ubereats.com/ec-en/store/juan-valdez-paseo-shopping-machala/ifIcF3mnVTabALX2vWnYHA):
  matcha con fruta mediano $4,10, croissant de jamón y queso $3,99 y sándwich de pollo $5,10.
- [Dunkin, Machala](https://www.ubereats.com/ec/brand-city/machala-el-oro/dunkin-donuts):
  iced latte extra grande $4,75 y mocaccino grande $3,55.

Son referencias de delivery consultadas en la fecha indicada: pueden incorporar
recargos y tamaños diferentes. No se copiaron recetas, nombres de marca ni descripciones.
Se propuso un escalón accesible de entrada, clásicos próximos al mercado y un
precio superior para matcha con fruta y brunch. El tamaño está indicado por producto.
Antes de vender, el negocio deberá contrastar costos por receta y el precio final
aplicable; no se añadieron impuestos, servicio ni gastos de entrega no confirmados.

Matcha y bebidas frutales tienen presencia local en la carta citada. Como señal
internacional complementaria, las cartas de 2026 incorporan pistacho, matcha y
cold brew: [Starbucks, invierno de 2026](https://about.starbucks.com/stories/2026/ring-in-2026-with-new-starbucks-drinks-caramel-protein-dubai-chocolate-and-pistachio/)
y [Peet's, propuesta de invierno de 2026](https://assets.ctfassets.net/69yuuzkbsv57/38LrswIC6tGmzgzmtnCax5/b91b49966faae127c30be16342e38fce/PEET-S_COFFEE_RINGS_IN_2026_WITH_A_PURPOSEFUL_WINTER_MENU_BLENDING_FLAVOR__FUNCTION__AND_A_FRESH_NEW_LOOK.pdf).
Esto orienta la selección; no demuestra volúmenes de venta locales ni que todos
los productos sean tendencias. La carta combina novedades con clásicos estables.

## La carta

| Categoría | Producto | Porción | USD |
| --- | --- | --- | ---: |
| Café, sin prisa | Espresso | 30 ml | 1,75 |
| Café, sin prisa | Americano | 240 ml | 2,25 |
| Café, sin prisa | Cappuccino | 240 ml | 2,90 |
| Café, sin prisa | Flat white | 180 ml | 3,25 |
| Café, sin prisa | Latte | 300 ml | 3,10 |
| Café, sin prisa | Mocha cacao | 300 ml | 3,60 |
| Sobre hielo | Cold brew | 350 ml | 3,25 |
| Sobre hielo | Iced latte | 350 ml | 3,50 |
| Sobre hielo | Iced vanilla latte | 350 ml | 3,95 |
| Sobre hielo | Espresso tonic | 350 ml | 3,75 |
| Sobre hielo | Iced americano | 350 ml | 2,60 |
| Sobre hielo | Affogato | 1 porción | 3,95 |
| Matcha & otras pausas | Matcha latte | 300 ml | 3,75 |
| Matcha & otras pausas | Iced matcha latte | 350 ml | 3,95 |
| Matcha & otras pausas | Strawberry matcha | 350 ml | 4,50 |
| Matcha & otras pausas | Chai latte | 300 ml | 3,60 |
| Del horno | Croissant de mantequilla | 1 unidad | 2,50 |
| Del horno | Roll de canela | 1 unidad | 3,25 |
| Del horno | Cookie de chocolate | 1 unidad | 2,25 |
| Del horno | Brownie de chocolate | 1 porción | 3,00 |
| Del horno | Banana bread & pistacho | 1 porción | 3,50 |
| Algo salado | Avocado toast | 1 tostada | 5,75 |
| Algo salado | Croissant de jamón y queso | 1 unidad | 4,25 |
| Algo salado | Grilled cheese | 1 sándwich | 4,75 |

Opciones en bebidas seleccionadas: leche entera incluida, deslactosada +$0,25,
bebida de avena +$0,75. Shot adicional +$0,60 cuando está configurado.
Los ingredientes y alérgenos describen la receta propuesta, no una certificación
alimentaria. Deben ajustarse a los insumos y procedimientos reales.

## Implementación

- `app/menu_content.py`: única definición de los 24 productos, precios decimales,
  identificadores estables, descripciones, porciones, fotografías y personalización.
- `app/cafe_content.py`: importa la carta, habilita su visualización y configura USD.
  La selección y cotización usan los servicios existentes; no se habilitó pago ni
  envío de pedidos. No fue necesario sembrar la base de datos de granos heredada.
- Menú: fotografías, categorías, búsqueda por nombre/descripción, estados sin
  resultados y acceso al detalle. Sigue siendo legible sin JavaScript.
- Fichas: imagen responsive, porción, notas, ingredientes y opciones existentes.
- Inicio: tres productos destacados, fotografía del ritual y cierre dedicado a Machala.
- Espacio: moodboard explícitamente identificado como inspiración, tres maneras
  de disfrutar la pausa y una composición de materiales.
- Experiencia: guía sensorial, tres combinaciones de sabores y fotografía de filtrado.
- Visítanos: dirección completada con Machala, búsqueda en Google Maps (sin pin
  inventado), imagen editorial y preguntas frecuentes. No se inventaron teléfono,
  redes sociales, días de apertura, servicios o reseñas.
- Catálogo: nueva transición visual del objeto a la taza; se conserva la exposición 3D.
- Carrito: fotografía en el estado vacío; no se cambió su lógica de compra.
- `editorial-update.css`: composiciones y adaptaciones móviles de estas secciones.
  La barra, el hero y sus videos conservan el diseño aprobado.

## Imágenes

24 fotografías de productos y cuatro fotografías editoriales, con variantes de
800 y 1600 píxeles, descargadas localmente. `srcset`, `sizes` y carga diferida
reducen el peso de las imágenes fuera de pantalla. No hay hotlinks en la interfaz.
Se sustituyeron referencias que mostraban otra bebida o marcas ajenas muy visibles.

Fuentes individuales: `app/static/img/photo-sources.json`.
Créditos públicos: `/static/img/photo-credits.html`, enlazados desde el pie.
Licencias: [Pexels](https://www.pexels.com/license/) y [Unsplash](https://unsplash.com/license/).
Las imágenes son ilustrativas; la página Espacio no las presenta como fotos del
local, y el menú indica que la presentación puede variar.

No se ejecutaron suites de pruebas ni verificaciones automatizadas de navegador,
por indicación del usuario. Se revisaron el código y fotografías seleccionadas.
Reiniciar Flask si el servidor actual no recarga módulos Python automáticamente.
