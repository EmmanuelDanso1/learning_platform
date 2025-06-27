from datetime import datetime
from realmind import db

class InfoDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # PDF or Word file
    image = db.Column(db.String(255))  # thumbnail
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    admin = db.relationship('Admin', backref='info_documents')
