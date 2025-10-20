from flask import Blueprint, request, jsonify, current_app
from learning_app.realmind.models import ReceivedOrder, ReceivedOrderItem
from learning_app.extensions import db
from flask_login import login_required
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/orders', methods=['POST'])
def receive_order():
    # Check API token
    token = request.headers.get('Authorization')
    expected_token = f"Bearer {os.getenv('API_TOKEN')}"
    if not token or token != expected_token:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()

        # Basic validation
        required_fields = ['order_id', 'user_id', 'full_name', 'email', 'address', 'total_amount', 'payment_method', 'items']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing fields in order data'}), 400

        # Save order
        received_order = ReceivedOrder(
            original_order_id=data['order_id'],
            user_id=data['user_id'],
            full_name=data['full_name'],
            email=data['email'],
            address=data['address'],
            total_amount=data['total_amount'],
            payment_method=data['payment_method']
        )
        db.session.add(received_order)
        db.session.flush()  # Get the ID

        # Save items
        for item in data['items']:
            received_item = ReceivedOrderItem(
                order_id=received_order.id,
                product_id=item['product_id'],
                product_name=item['product_name'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(received_item)

        db.session.commit()
        print("Order saved:", received_order.original_order_id)

        return jsonify({'message': 'Order received successfully'}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error receiving order: {e}")
        return jsonify({'error': str(e)}), 500
