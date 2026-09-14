from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# Instancias desacopladas para evitar importaciones circulares
db = SQLAlchemy()
ma = Marshmallow()
