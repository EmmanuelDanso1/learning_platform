from datetime import datetime
from learning_app.extensions import db

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

# newsletter subscribers
class ExternalSubscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    source = db.Column(db.String(50), default='bookshop')
    added_on = db.Column(db.DateTime, default=datetime.utcnow)
