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
