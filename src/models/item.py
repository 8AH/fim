
from . import db
from datetime import datetime


class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    
    # Flag pour distinguer les articles temporaires et permanents
    is_temporary = db.Column(db.Boolean, default=False, nullable=False)
    
    # Clés étrangères pour les emplacements (nullable pour les articles temporaires)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True)
    furniture_id = db.Column(db.Integer, db.ForeignKey('furniture.id'), nullable=True)
    drawer_id = db.Column(db.Integer, db.ForeignKey('drawer.id'), nullable=True)
    
    # Champs texte pour la compatibilité (nullable pour les articles temporaires)
    zone = db.Column(db.String(100), nullable=True)
    mobilier = db.Column(db.String(100), nullable=True)
    niveau_tiroir = db.Column(db.String(100), nullable=True)

    # Fournisseur (clé étrangère)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)

    # Dates de création et d'emprunt
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations avec les tables de localisation
    zone_rel = db.relationship('Zone', backref='items', lazy=True)
    furniture_rel = db.relationship('Furniture', backref='items', lazy=True)
    drawer_rel = db.relationship('Drawer', backref='items', lazy=True)

    # Relation avec le fournisseur
    supplier_rel = db.relationship('Supplier', backref='items', lazy=True)

    def __repr__(self):
        if self.is_temporary:
            return f'<Item (Temp) {self.name}>'
        return f'<Item {self.name}>'
        
    @property
    def location_info(self):
        """Retourne les informations de localisation formatées"""
        if self.is_temporary:
            return "Article temporaire (sans emplacement)"
        
        zone_name = self.zone_rel.name if self.zone_rel else "Non spécifié"
        furniture_name = self.furniture_rel.name if self.furniture_rel else "Non spécifié"
        drawer_name = self.drawer_rel.name if self.drawer_rel else "Non spécifié"
        
        return f"{zone_name} > {furniture_name} > {drawer_name}"
