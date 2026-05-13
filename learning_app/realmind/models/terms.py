from datetime import datetime
from learning_app.extensions import db


class TermsAndConditions(db.Model):
    __tablename__ = 'terms_and_conditions'

    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    admin_id   = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)

    def __repr__(self):
        return f"<TermsAndConditions updated={self.updated_at}>"
