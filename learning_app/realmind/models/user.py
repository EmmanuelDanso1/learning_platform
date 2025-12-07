from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from learning_app.extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

    # Allow NULL for Google OAuth users
    password = db.Column(db.String(255), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)
    applications = db.relationship('Application', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Email verification
    is_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    # Profile Info (for "Complete Profile" page)
    firstname = db.Column(db.String(150), nullable=True)
    surname = db.Column(db.String(150), nullable=True)
    other_names = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    ghana_card_number = db.Column(db.String(20), nullable=True)

    preferred_subject = db.Column(db.String(150), nullable=True)
    preferred_level = db.Column(db.String(150), nullable=True)

    # Document uploads i.e cv/certificates
    cv = db.Column(db.String(255), nullable=True)
    certificate = db.Column(db.String(255), nullable=True)

    # NEW FIELD - track login provider
    auth_provider = db.Column(db.String(20), default="local")  # local | google

    def __repr__(self):
        return f"<User {self.fullname}>"
    
    def get_id(self):
        return f"user:{self.id}"

    @property
    def is_admin(self):
        return False

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password:
            return False  # OAuth users cannot use password login
        return check_password_hash(self.password, password)

    # Profile completion check
    @property
    def is_profile_complete(self):
        required = [
            self.firstname,
            self.surname,
            self.other_names,
            self.phone,
            self.ghana_card_number,
            self.preferred_level,
            self.preferred_subject
        ]
        return all(required)