from datetime import datetime
from realmind import db

class ReceivedOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_order_id = db.Column(db.String(50))
    user_id = db.Column(db.Integer)
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    total_amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_received = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('ReceivedOrderItem', backref='order', cascade="all, delete-orphan")

class ReceivedOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('received_order.id'))
    product_id = db.Column(db.Integer)
    product_name = db.Column(db.String(120))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
