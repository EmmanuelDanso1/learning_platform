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

    # New fields
    author = db.Column(db.String(120), nullable=True)
    grade = db.Column(db.String(50), nullable=True)
    level = db.Column(db.String(50), nullable=True)
    subject = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100), nullable=True)

    # Foreign Key to Admin
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    admin = db.relationship('Admin', backref=db.backref('products', lazy=True))

    # Foreign Key to Category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', back_populates='products')

    def __repr__(self):
        return f'<Product {self.name}>'

    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'in_stock': self.in_stock,
            'image_filename': self.image_filename,
            'author': self.author,
            'grade': self.grade,
            'level': self.level,
            'subject': self.subject,
            'brand': self.brand
        }
