"""ZERO DAY's 24-item opening proposal, USD. Sources and pricing rationale in docs/menu-machala.md."""
from copy import deepcopy

MILK = {'id': 'leche', 'label': 'Tu leche', 'required': True, 'choices': [
    {'id': 'entera', 'label': 'Entera', 'price_delta': '0.00'},
    {'id': 'deslactosada', 'label': 'Deslactosada', 'price_delta': '0.25'},
    {'id': 'avena', 'label': 'Bebida de avena', 'price_delta': '0.75'},
]}
SHOT = {'id': 'extra', 'label': 'Un poco más de café', 'required': False, 'max_choices': 1,
        'choices': [{'id': 'espresso', 'label': 'Shot de espresso', 'price_delta': '0.60'}]}


def product(slug, name, price, photo, description, story, portion, notes, allergens='', featured=False, milk=False, shot=False):
    return dict(id=f'zd-{slug}', slug=slug, name=name, price=price, published=True,
                availability='available', image=f'/static/img/menu/{photo}-1600.jpg',
                image_small=f'/static/img/menu/{photo}-800.jpg',
                short_description=description, long_description=story, portion=portion,
                tasting_notes=notes, allergens=allergens, featured=featured,
                options=[deepcopy(MILK)] if milk else [], modifiers=[deepcopy(SHOT)] if shot else [])

MENU = [
    {'name': 'Café, sin prisa', 'intro': 'De un espresso breve a una taza que se queda contigo.', 'items': [
        product('espresso', 'Espresso', '1.75', 'espresso', 'Corto, intenso y con una crema delicada.', 'La expresión más directa del café. Un sorbo concentrado para descubrir su cuerpo y su final.', '30 ml', ['Intenso', 'Con cuerpo'], shot=True),
        product('americano', 'Americano', '2.25', 'americano', 'Espresso y agua caliente. Todo el carácter, con más espacio.', 'Una taza larga y limpia para acompañar una conversación o disfrutar sin añadidos.', '240 ml', ['Limpio', 'Equilibrado'], shot=True),
        product('cappuccino', 'Cappuccino', '2.90', 'cappuccino', 'Espresso, leche y una capa de espuma suave.', 'El encuentro entre la intensidad del café y una textura aireada. Un clásico que siempre encuentra su momento.', '240 ml', ['Cremoso', 'Clásico'], 'Leche', milk=True, shot=True),
        product('flat-white', 'Flat white', '3.25', 'flat-white', 'Doble espresso y leche de textura sedosa.', 'Más protagonismo del café y una capa fina de microespuma. Para quien busca un perfil intenso sin renunciar a la suavidad.', '180 ml', ['Sedoso', 'Intenso'], 'Leche', milk=True),
        product('latte', 'Latte', '3.10', 'latte', 'Espresso envuelto en leche vaporizada.', 'Una taza amplia, suave y redonda. La leche acompaña al café y deja una sensación delicada en cada sorbo.', '300 ml', ['Suave', 'Redondo'], 'Leche', milk=True, shot=True),
        product('mocha-cacao', 'Mocha cacao', '3.60', 'mocha', 'Café, chocolate y leche. Un abrazo en taza.', 'El cacao suma profundidad al espresso sin convertirlo en un postre pesado. Ideal para una pausa dulce.', '300 ml', ['Chocolate', 'Cremoso'], 'Leche; revisar ingredientes del chocolate', milk=True, shot=True),
    ]},
    {'name': 'Sobre hielo', 'intro': 'Para el calor de Machala: café fresco, texturas ligeras y nuevos rituales.', 'items': [
        product('cold-brew', 'Cold brew', '3.25', 'cold-brew', 'Café infusionado en frío, servido sobre hielo.', 'Una extracción lenta que ofrece una taza fresca y de cuerpo suave. Para beber despacio, sin leche.', '350 ml', ['Refrescante', 'Suave'], featured=True),
        product('iced-latte', 'Iced latte', '3.50', 'iced-latte', 'Espresso, leche fría y mucho hielo.', 'La versión fresca del latte de siempre. El café se encuentra con la leche en una bebida ligera y cremosa.', '350 ml', ['Cremoso', 'Frío'], 'Leche', milk=True, shot=True),
        product('iced-vanilla-latte', 'Iced vanilla latte', '3.95', 'vanilla-latte', 'Latte frío con un toque aromático de vainilla.', 'Dulzor moderado, café y leche fría. Una pausa de sobremesa que también funciona a cualquier hora.', '350 ml', ['Vainilla', 'Dulce'], 'Leche', milk=True, shot=True),
        product('espresso-tonic', 'Espresso tonic', '3.75', 'espresso-tonic', 'Espresso sobre tónica y hielo, con un toque cítrico.', 'El amargor de la tónica y el carácter del café se equilibran en una bebida burbujeante. Sin alcohol.', '350 ml', ['Cítrico', 'Burbujeante'], featured=True),
        product('iced-americano', 'Iced americano', '2.60', 'iced-americano', 'Espresso, agua fría y hielo. Así de simple.', 'Una bebida directa y refrescante que deja todo el protagonismo al café. Sin leche ni jarabes.', '350 ml', ['Ligero', 'Sin leche'], shot=True),
        product('affogato', 'Affogato', '3.95', 'affogato', 'Helado de vainilla con un espresso recién servido.', 'Frío y caliente en la misma cucharada. El espresso abraza el helado y cambia de textura mientras lo disfrutas.', '1 porción', ['Vainilla', 'Contraste'], 'Leche; puede contener huevo'),
    ]},
    {'name': 'Matcha & otras pausas', 'intro': 'Verde, especias y fruta. Hay más de una forma de hacer una pausa.', 'items': [
        product('matcha-latte', 'Matcha latte', '3.75', 'matcha-latte', 'Té verde matcha y leche vaporizada.', 'Un perfil vegetal delicado, acompañado por la textura de la leche. Una alternativa al café que también contiene cafeína.', '300 ml', ['Vegetal', 'Sedoso'], 'Leche', milk=True),
        product('iced-matcha', 'Iced matcha latte', '3.95', 'iced-matcha', 'Matcha, leche fría y hielo en capas.', 'Fresco y cremoso, con el carácter del té verde. Remuévelo antes de beber para unir las capas.', '350 ml', ['Verde', 'Refrescante'], 'Leche', milk=True),
        product('strawberry-matcha', 'Strawberry matcha', '4.50', 'strawberry-matcha', 'Frutilla, leche y matcha. Tres capas, un solo momento.', 'La fruta aporta un contrapunto dulce al té verde. Una combinación fresca para quienes disfrutan probar algo distinto.', '350 ml', ['Frutilla', 'Matcha'], 'Leche', featured=True, milk=True),
        product('chai-latte', 'Chai latte', '3.60', 'chai-latte', 'Té negro especiado y leche caliente.', 'Canela, jengibre y cardamomo acompañan al té negro en una taza aromática. Cálido, envolvente y con cafeína.', '300 ml', ['Especias', 'Aromático'], 'Leche', milk=True),
    ]},
    {'name': 'Del horno', 'intro': 'Capas crujientes, chocolate y ese último bocado que pide otro café.', 'items': [
        product('croissant-mantequilla', 'Croissant de mantequilla', '2.50', 'croissant', 'Hojaldre dorado, ligero y delicadamente crujiente.', 'Para partir con las manos y acompañar con un café. El contraste entre las capas exteriores y el centro suave hace el resto.', '1 unidad', ['Mantequilla', 'Crujiente'], 'Trigo, leche y huevo'),
        product('roll-canela', 'Roll de canela', '3.25', 'cinnamon-roll', 'Masa suave enrollada con canela y azúcar.', 'Una espiral aromática, de miga tierna y dulzor cálido. Va especialmente bien con un americano o un flat white.', '1 unidad', ['Canela', 'Tierno'], 'Trigo, leche y huevo'),
        product('cookie-chocolate', 'Cookie de chocolate', '2.25', 'cookie', 'Bordes dorados y trozos de chocolate.', 'Una galleta generosa para acompañar el café. Crujiente por fuera y con un centro más suave.', '1 unidad', ['Chocolate', 'Mantequilla'], 'Trigo, leche, huevo; posible soya'),
        product('brownie', 'Brownie de chocolate', '3.00', 'brownie', 'Chocolate intenso y centro húmedo.', 'Una porción pequeña con mucho carácter. El cacao encuentra un buen compañero en el espresso y el cold brew.', '1 porción', ['Cacao', 'Intenso'], 'Trigo, leche, huevo y frutos secos'),
        product('banana-pistacho', 'Banana bread & pistacho', '3.50', 'banana-bread', 'Bizcocho de banano con un toque de pistacho.', 'Una miga húmeda, el dulzor del banano y un final de frutos secos. Un guiño al banano de nuestra región y a nuevas combinaciones.', '1 porción', ['Banano', 'Pistacho'], 'Trigo, leche, huevo y pistacho', featured=True),
    ]},
    {'name': 'Algo salado', 'intro': 'Para cuando una taza pide un poco más.', 'items': [
        product('avocado-toast', 'Avocado toast', '5.75', 'avocado-toast', 'Pan tostado, aguacate y huevo, con un toque de limón.', 'Cremoso, crujiente y fresco. Una opción de brunch para acompañar con americano o una bebida sobre hielo.', '1 tostada', ['Aguacate', 'Brunch'], 'Trigo y huevo', featured=True),
        product('croissant-jamon-queso', 'Croissant de jamón y queso', '4.25', 'croissant-sandwich', 'Hojaldre con jamón, queso y hojas frescas.', 'Un clásico salado con el contraste de una masa de mantequilla. Para una mañana larga o una pausa a media tarde.', '1 unidad', ['Salado', 'Hojaldre'], 'Trigo, leche y huevo'),
        product('grilled-cheese', 'Grilled cheese', '4.75', 'grilled-cheese', 'Pan dorado a la plancha y queso fundido.', 'Sencillo y reconfortante: corteza crujiente y centro cremoso. Una buena pareja para un café largo.', '1 sándwich', ['Queso', 'Crujiente'], 'Trigo y leche'),
    ]},
]
