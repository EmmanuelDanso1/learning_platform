from realmind import db
from datetime import datetime

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(120), nullable=True)
    in_stock = db.Column(db.Boolean, default=True) 
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    ecommerce_product_id = db.Column(db.Integer, nullable=True)
    # Foreign Key to Admin
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    admin = db.relationship('Admin', backref=db.backref('products', lazy=True))

    def __repr__(self):
        return f'<Product {self.name}>'

    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'in_stock': self.in_stock,
            'image_filename': self.image_filename
        }

