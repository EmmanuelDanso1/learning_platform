from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from learning_app.extensions import db

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))
    file_type = db.Column(db.String(10))  # 'image' or 'video'
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

