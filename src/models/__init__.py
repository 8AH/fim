from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Importer les modèles pour les rendre accessibles via src.models
from .item import Item
from .location import Zone, Furniture, Drawer
from .user import User
