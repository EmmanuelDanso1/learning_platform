from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from realmind import db

class JobPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    job_type = db.Column(db.String(50))
    requirements = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    applications = db.relationship('Application', backref='job', cascade='all, delete-orphan', lazy=True)