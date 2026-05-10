from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from learning_app.extensions import db

class JobPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    job_type = db.Column(db.String(50))
    requirements = db.Column(db.Text, nullable=False)

    # job post deletion but application history still remains
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    applications = db.relationship('Application', backref='job', lazy=True)

    # level and suject
    level = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    application_deadline = db.Column(db.DateTime, nullable=True)