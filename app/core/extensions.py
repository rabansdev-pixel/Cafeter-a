from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_wtf.csrf import CSRFProtect

# Instancias desacopladas para evitar importaciones circulares
db = SQLAlchemy()
ma = Marshmallow()
csrf = CSRFProtect()
