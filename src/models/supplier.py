from . import db

class Supplier(db.Model):
    __tablename__ = 'supplier'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    site = db.Column(db.String(100), unique=True, nullable=True)
    mail = db.Column(db.String(100), unique=True, nullable=True)
    comment = db.Column(db.String(255), nullable=True)
    # items = db.relationship('Item', backref='supplier_rel', lazy=True)
