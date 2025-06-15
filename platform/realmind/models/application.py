from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from realmind import db

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='under review')
    cv = db.Column(db.String(150), nullable=False)
    certificate = db.Column(db.String(150), nullable=False)
    cover_letter = db.Column(db.String(150), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_post.id'), nullable=False)