from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import datetime, timedelta

from learning_app.extensions import db

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False) 
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255), nullable=True)
    job_posts = db.relationship('JobPost', backref='admin', lazy=True)
    news_posts = db.relationship('News', backref='admin', lazy=True)

    # Email verification fields
    is_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Admin {self.fullname}>"
    
    @property
    def is_admin(self):
        return True

    def get_id(self):
        return f"admin:{self.id}"

    # Password methods
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

     # **OTP helper method**
    def generate_otp(self, expiry_minutes=10):
        self.otp_code = f"{random.randint(100000, 999999)}"
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        return self.otp_code