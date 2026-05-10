from datetime import datetime
from learning_app.extensions import db


class Partner(db.Model):
    __tablename__ = 'partner'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(150), nullable=False)
    description    = db.Column(db.String(255), nullable=True)   # short tagline
    website_url    = db.Column(db.String(500), nullable=True)
    logo_filename  = db.Column(db.String(255), nullable=True)
    is_active      = db.Column(db.Boolean, default=True, nullable=False)
    display_order  = db.Column(db.Integer, default=0, nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id       = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)

    def __repr__(self):
        return f"<Partner {self.name}>"
