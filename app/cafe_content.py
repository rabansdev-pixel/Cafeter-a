"""Editorial content. Publish business details only after the café confirms them.

Media paths are relative to static/. Space media must depict the actual café.
The 24-item menu proposal lives in app/menu_content.py; pricing research is in docs/menu-machala.md.
Experiences: [{"title": "...", "description": "...", "image": "...", "alt": "..."}].
"""
from app.menu_content import MENU

CAFE = {
    'address': 'Ayacucho y 8va Norte, Machala, Ecuador', 'hours': ['8:00 a. m. — 8:00 p. m.'],
    'maps_url': 'https://www.google.com/maps/search/?api=1&query=Ayacucho+y+8va+Norte+Machala+Ecuador', 'instagram_url': None,
    'social_is_example': True, 'menu_is_example': False,
    'email': None, 'phone': None, 'menu_url': '/menu', 'currency': 'USD',
    'space_gallery': [], 'policies': [], 'space_image': None, 'space_alt': '', 'hero_video': 'img/products/hero.mp4',
    'coffee_video': 'img/products/coffe.mp4',
    'coffee_poster': 'img/editorial/coffee-poster.webp',
    'hero_poster': 'img/editorial/hero-v1-poster.webp',
    # Same approved shot. Deferred sources avoid downloading desktop media on mobile.
    'hero_sources': [
        {'path': 'img/products/hero-v1-mobile.mp4', 'type': 'video/mp4', 'media': '(max-width: 767px)'},
        {'path': 'img/products/hero-v1-web.webm', 'type': 'video/webm', 'media': ''},
        {'path': 'img/products/hero-v1-web.mp4', 'type': 'video/mp4', 'media': ''},
    ],
    'experiences': [],
    'menu': MENU,
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
