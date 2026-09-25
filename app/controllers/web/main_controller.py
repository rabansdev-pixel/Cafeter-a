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


@main_bp.route('/login', endpoint='login')
@main_bp.route('/registro', endpoint='register')
@main_bp.route('/recuperar-acceso', endpoint='recover')
def access_preview():
    """Presentation only: no credentials, accounts or sessions are processed."""
    from flask import request
    mode = {'/registro': 'register', '/recuperar-acceso': 'recover'}.get(request.path, 'login')
    return render_template('pages/access.html', mode=mode)


@main_bp.route('/cuenta/vista-previa')
def account_preview():
    return render_template('pages/account_preview.html')


@main_bp.route('/admin/vista-previa')
def admin_preview():
    """Public read-only mockup using only already-public menu information."""
    from flask import request, abort
    from app.services.menu_service import MenuService
    section = request.args.get('section', 'products')
    if section not in {'products', 'categories', 'inventory', 'users', 'activity'}:
        abort(404)
    return render_template('pages/admin_preview.html', section=section,
                           categories=MenuService.categories())
