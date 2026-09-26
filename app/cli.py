import click
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from app.core.extensions import db
from app.models import Category, Product, User
from app.cafe_content import CAFE
from app.services.auth_service import audit, identity_fields


def register_commands(app):
    @app.cli.command('seed-menu')
    def seed_menu():
        """Importa productos faltantes sin sobrescribir los existentes ni inventar stock."""
        from decimal import Decimal
        db.session.execute(text('SELECT pg_advisory_xact_lock(2409202601)'))
        created = 0
        for position, group in enumerate(CAFE['menu']):
            category = Category.query.filter_by(name=group['name']).first()
            if not category:
                category = Category(name=group['name'], intro=group.get('intro', ''), position=position)
                db.session.add(category)
                db.session.flush()
            for order, item in enumerate(group['items']):
                if Product.query.filter((Product.menu_id == item['id']) | (Product.slug == item['slug'])).first():
                    continue
                details = {k: v for k, v in item.items() if k not in {'id','name','slug','price','published','image','short_description','long_description','featured'}}
                image = item['image']
                if item['slug'] == 'cold-brew':
                    image = '/static/img/home/cold-brew-1600.webp'
                    details['image_small'] = '/static/img/home/cold-brew-800.webp'
                product = Product(name=item['name'], slug=item['slug'], menu_id=item['id'],
                    tagline=item.get('short_description', ''), description=item.get('long_description', ''),
                    price=Decimal(item['price']), image_url=image, stock=None, weight_grams=0,
                    is_active=item.get('published', True), is_featured=item.get('featured', False),
                    category_id=category.id, position=order, details=details)
                db.session.add(product)
                created += 1
        audit('menu.seed', 'product', None, {'created': created})
        db.session.commit()
        click.echo(f'{created} productos importados; datos existentes conservados. Stock sin registrar.')

    @app.cli.command('create-admin')
    @click.option('--email', prompt='Correo')
    @click.option('--name', prompt='Nombre')
    @click.password_option(confirmation_prompt=True)
    def create_admin(email, name, password):
        """Crea un administrador; nunca usa contraseñas predeterminadas."""
        try:
            name, email, password = identity_fields(dict(email=email, name=name, password=password))
            db.session.execute(text('SELECT pg_advisory_xact_lock(2409202602)'))
            if User.query.filter_by(email=email).first():
                raise ValueError('Ese correo ya tiene una cuenta. No se ha cambiado su rol.')
            user = User(name=name, email=email, password_hash=generate_password_hash(password), role='admin')
            db.session.add(user)
            db.session.flush()
            audit('user.create_admin', 'user', user.id, actor_id=user.id)
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            raise click.ClickException(str(error)) from None
        except IntegrityError:
            db.session.rollback()
            raise click.ClickException('No se pudo crear la cuenta; ese correo ya está registrado.') from None
        click.echo('Administrador creado.')

    @app.cli.command('reset-password')
    @click.option('--email', prompt='Correo de la cuenta')
    @click.password_option(prompt='Nueva contraseña', confirmation_prompt=True)
    def reset_password(email, password):
        """Restablece el acceso desde la terminal autorizada, sin cambiar roles."""
        try:
            _, email, password = identity_fields(dict(name='Cuenta', email=email, password=password))
            user = User.query.filter_by(email=email).with_for_update().first()
            if not user:
                raise ValueError('No existe una cuenta con ese correo. Usa el correo con el que creaste el administrador.')
            if user.firebase_uid:
                raise ValueError('Esta cuenta usa Firebase. Cambia la contraseña desde Recuperar acceso o desde Firebase Authentication.')
            if not user.active:
                raise ValueError('La cuenta está desactivada. Debe activarla un administrador.')
            user.password_hash = generate_password_hash(password)
            user.session_version += 1
            audit('user.password_reset_cli', 'user', user.id)
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            raise click.ClickException(str(error)) from None
        click.echo('Contraseña actualizada. Inicia sesión con ese correo y la nueva contraseña.')
