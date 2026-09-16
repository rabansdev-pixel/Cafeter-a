"""Editorial content. Publish business details only after the café confirms them.

Media paths are relative to static/. Space media must depict the actual café.
Menu: [{"name": "confirmed category", "items": [{"name": "...", "description": "..."}]}].
Experiences: [{"title": "...", "description": "...", "image": "...", "alt": "..."}].
"""
CAFE = {
    'address': 'Ayacucho y 8va Norte', 'hours': ['8:00 a. m. — 8:00 p. m.'],
    'maps_url': None, 'instagram_url': 'https://www.instagram.com/',
    'social_is_example': True, 'menu_is_example': True,
    'email': None, 'phone': None, 'menu_url': '/catalogo',
    'space_image': None, 'space_alt': '', 'hero_video': None,
    'hero_poster': 'img/editorial/ritual-plantacion.webp',
    'experiences': [],
    # Starter menu requested by the owner. General categories inspired by:
    # https://www.starbucks.com/menu/coffee-espresso/hot-coffee-espresso
    # https://www.starbucks.com/menu?preview=true
    'menu': [
        {'name': 'Espresso', 'items': [
            {'name': 'Espresso', 'description': 'Corto, intenso, esencial.'},
            {'name': 'Americano', 'description': 'Espresso y agua caliente.'},
            {'name': 'Cappuccino', 'description': 'Espresso, leche y espuma.'},
            {'name': 'Latte', 'description': 'Espresso con leche vaporizada.'}]},
        {'name': 'Fríos', 'items': [
            {'name': 'Cold brew', 'description': 'Café de extracción en frío.'},
            {'name': 'Iced latte', 'description': 'Espresso, leche y hielo.'}]},
        {'name': 'Para acompañar', 'items': [
            {'name': 'Croissant', 'description': 'Hojaldre de mantequilla.'},
            {'name': 'Pan de banana', 'description': 'Una pausa dulce.'}]},
    ],
}
# These are supplied editorial objects, not stock or items for purchase.
OBJECTS = [
    {'asset': 'espresso', 'name': 'La precisión', 'category': '01 / PREPARAR', 'text': 'Una máquina. El principio de una taza.', 'alt': 'Modelo de una máquina espresso'},
    {'asset': 'ceramic', 'name': 'El momento', 'category': '02 / SERVIR', 'text': 'El café, la cerámica y el tiempo que te das.', 'alt': 'Taza de cerámica con café y plato'},
    {'asset': 'cappuccino', 'name': 'La pausa', 'category': '03 / SABOREAR', 'text': 'Un pequeño universo alrededor de una taza.', 'alt': 'Modelo de cappuccino con acompañamientos'},
    {'asset': 'beans', 'name': 'El origen', 'category': '04 / DESCUBRIR', 'text': 'Todo lo que sucede antes del primer sorbo.', 'alt': 'Granos de café tostados sobre papel'},
    {'asset': 'geisha-huila', 'name': 'Coffee Paper Bag', 'category': '05 / OBJETOS', 'text': 'Textura, papel y las huellas de lo cotidiano.', 'alt': 'Escaneo de una bolsa de café con su diseño original'},
    {'asset': 'yirgacheffe', 'name': 'Costa Coffee', 'category': '06 / MARCAS', 'text': 'Una identidad propia. Un objeto de nuestra selección editorial.', 'alt': 'Bolsa Costa Coffee con su identidad original'},
    {'asset': 'borbon-rosado', 'name': 'Coffee Packaging', 'category': '07 / DISEÑO', 'text': 'La forma también es parte del ritual.', 'alt': 'Envase de café con el diseño original'},
    {'asset': 'kenia-nyeri', 'name': 'Dunkin’', 'category': '08 / MARCAS', 'text': 'Color y carácter. Una mirada al universo del café.', 'alt': 'Modelo de café Dunkin con su marca original'},
    {'asset': 'takeaway', 'name': 'En movimiento', 'category': '09 / OBJETOS', 'text': 'Otra forma de acompañar el día.', 'alt': 'Vaso de café con su diseño original'},
    {'asset': 'cups', 'name': 'CC0ffee Cups', 'category': '10 / DISEÑO', 'text': 'Una colección de formas alrededor del café.', 'alt': 'Colección de vasos CC0ffee con su diseño original'},
]
