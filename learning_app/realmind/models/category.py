from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from learning_app.extensions import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    products = db.relationship('Product', back_populates='category', lazy=True)
