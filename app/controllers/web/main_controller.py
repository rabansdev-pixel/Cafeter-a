from flask import Blueprint, render_template, redirect, url_for
from app.cafe_content import OBJECTS

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Physical café: editorial content, original objects and verified visit details."""
    return render_template("pages/home.html", objects=OBJECTS)



@main_bp.route("/origenes")
def origins():
    """Keep old bookmarks pointing to the consolidated origin section."""
    return redirect(url_for("catalog.catalog", _anchor="origen"), code=301)


@main_bp.route("/metodos")
def methods():
    """Preparation now belongs to the café experience."""
    return redirect(url_for("cafe.experience", _anchor="metodos"), code=301)


from app.controllers.web.account_controller import (
    access, account, admin, logout, product_edit, product_delete, user_update, firebase_session,
)

main_bp.add_url_rule('/login', 'login', access, methods=['GET', 'POST'])
main_bp.add_url_rule('/registro', 'register', access, methods=['GET', 'POST'])
main_bp.add_url_rule('/recuperar-acceso', 'recover', access, methods=['GET', 'POST'])
main_bp.add_url_rule('/cuenta', 'account_preview', account)
main_bp.add_url_rule('/cuenta/vista-previa', 'account_preview', account)
main_bp.add_url_rule('/admin', 'admin_preview', admin)
main_bp.add_url_rule('/admin/vista-previa', 'admin_preview', admin)
main_bp.add_url_rule('/logout', 'logout', logout, methods=['POST'])
main_bp.add_url_rule('/admin/productos/nuevo', 'product_create', product_edit, methods=['GET', 'POST'])
main_bp.add_url_rule('/admin/productos/<int:product_id>', 'product_edit', product_edit, methods=['GET', 'POST'])
main_bp.add_url_rule('/admin/productos/<int:product_id>/desactivar', 'product_delete', product_delete, methods=['POST'])
main_bp.add_url_rule('/admin/usuarios/<int:user_id>', 'user_update', user_update, methods=['POST'])

main_bp.add_url_rule('/api/auth/firebase/session', 'firebase_session', firebase_session, methods=['POST'])
