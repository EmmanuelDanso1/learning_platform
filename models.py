from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)
    applications = db.relationship('Application', backref='user', lazy=True)
    def __repr__(self):
        return f"<User {self.username}>"
    
    def get_id(self):
        return f"user:{self.id}"
    
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)
    job_posts = db.relationship('JobPost', backref='admin', lazy=True)
    
    def __repr__(self):
        return f"<Admin {self.username}>"
    
    def get_id(self):
        return f"admin:{self.id}"

class JobPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    job_type = db.Column(db.String(50))
    requirements = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    applications = db.relationship('Application', backref='job', cascade='all, delete-orphan', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='under review')  # Default status is 'under review'
    cv = db.Column(db.String(150), nullable=False)
    certificate = db.Column(db.String(150), nullable=False)
    cover_letter = db.Column(db.String(150), nullable=True)  # Optional upload
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_post.id'), nullable=False)
    