from .supplier_routes import supplier_bp
# Ce fichier permet l'importation des modules dans le package routes
from .location_routes import location_bp
from .admin_routes import admin_bp
from .ai_routes import ai_bp
from .main_routes import main_bp
from .items_api import items_api_bp
from .reports_routes import reports_bp
from .utils_routes import utils_bp

# Liste des blueprints à enregistrer dans l'application
blueprints = [
    location_bp,
    admin_bp,
    ai_bp,
    main_bp,
    items_api_bp,
    reports_bp,
    utils_bp,
    supplier_bp
]
