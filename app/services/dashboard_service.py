from flask import url_for, g
from app.core.extensions import db
from app.models import Product, User, Category, AuditLog


def dashboard_data(section, products):
    """Only stored records. No revenue, orders or trends are invented."""
    admin = g.user.role == 'admin'
    tracked = [p for p in products if p.stock is not None and p.is_active]
    untracked = sum(p.stock is None and p.is_active for p in products)
    categories = db.session.query(db.func.count(Category.id)).scalar()
    stats = [
        dict(label='Productos publicados', value=sum(p.is_active for p in products), note=f'{len(products)} productos en la carta', icon='products', section='products'),
        dict(label='Unidades registradas', value=sum(p.stock for p in tracked), note=f'{len(tracked)} productos con stock registrado', icon='inventory', section='inventory'),
        dict(label='Stock por registrar', value=untracked, note='Productos publicados sin cantidad registrada', icon='activity', section='inventory'),
        dict(label='Clientes registrados' if admin else 'Categorías', value=User.query.filter_by(role='customer', active=True).count() if admin else categories,
             note='Cuentas de clientes activas' if admin else 'Categorías de la carta', icon='users' if admin else 'categories', section='users' if admin else 'categories'),
    ]
    labels = {'product.create':'Producto creado', 'product.update':'Producto actualizado', 'product.deactivate':'Producto desactivado',
              'user.register':'Cuenta creada', 'user.firebase_link':'Cuenta vinculada a Firebase', 'user.permissions':'Permisos actualizados', 'menu.seed':'Carta importada',
              'user.create_admin':'Administrador creado', 'user.password_reset_cli':'Contraseña restablecida', 'product.preserve_image':'Fotografía actualizada'}
    activity = []
    if admin:
        for event in AuditLog.query.order_by(AuditLog.id.desc()).limit(6):
            activity.append(dict(id=event.id, title=labels.get(event.action, event.action),
                description=f'{event.actor.name if event.actor else "Sistema"} · {event.entity} {event.entity_id or ""}',
                time=event.created_at.isoformat()))
    nav = [('dashboard','Resumen'),('products','Productos'),('categories','Categorías'),('inventory','Inventario')]
    if admin:
        nav += [('users','Usuarios y roles'),('activity','Actividad')]
    return dict(section=section, name=g.user.name, role='Administrador' if admin else 'Personal',
        navigation=[dict(key=key,label=label,href=url_for('main.admin_preview',section=key)) for key,label in nav],
        stats=stats, activity=activity, canViewActivity=admin,
        stock=dict(out=sum(p.stock == 0 and p.is_active for p in products), unknown=untracked),
        products=[dict(id=p.id,name=p.name,image=p.image,price=f'{p.price:.2f} USD',href=url_for('main.product_edit',product_id=p.id))
                  for p in sorted(products,key=lambda p:p.updated_at,reverse=True)[:4]],
        urls=dict(site=url_for('main.home'),account=url_for('main.account_preview'),logout=url_for('main.logout'),
                  create=url_for('main.product_create'),inventory=url_for('main.admin_preview',section='inventory'),
                  activity=url_for('main.admin_preview',section='activity')))
