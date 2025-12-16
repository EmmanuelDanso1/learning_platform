from flask import Blueprint, request, jsonify, current_app
from learning_app.realmind.models import ReceivedOrder, ReceivedOrderItem
from learning_app.extensions import db
import os
import logging
from learning_app.extensions import csrf

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/orders', methods=['POST'])
@csrf_exempt
def receive_order():
    """Receive orders from Bookshop and save to admin dashboard"""
    
    # Check API token
    token = request.headers.get('Authorization')
    expected_token = f"Bearer {os.getenv('API_TOKEN')}"
    
    if not token or token != expected_token:
        current_app.logger.warning(
            f"[Admin API] Unauthorized order submission attempt from {request.remote_addr}"
        )
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        
        if not data:
            current_app.logger.warning("[Admin API] No JSON data received")
            return jsonify({'error': 'No data provided'}), 400

        # Basic validation
        required_fields = ['order_id', 'user_id', 'full_name', 'email', 'address', 
                          'total_amount', 'payment_method', 'items']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            current_app.logger.warning(
                f"[Admin API] Missing fields in order data: {missing_fields}"
            )
            return jsonify({
                'error': 'Missing fields in order data',
                'missing_fields': missing_fields
            }), 400

        order_id = data['order_id']
        current_app.logger.info(f"[Admin API] Receiving order {order_id} from Bookshop")

        # Check for duplicate order
        existing = ReceivedOrder.query.filter_by(original_order_id=order_id).first()
        if existing:
            current_app.logger.warning(
                f"[Admin API] Duplicate order submission: {order_id}"
            )
            return jsonify({
                'error': 'Order already exists',
                'order_id': order_id
            }), 409

        # Save order
        received_order = ReceivedOrder(
            original_order_id=data['order_id'],
            user_id=data['user_id'],
            full_name=data['full_name'],
            email=data['email'],
            address=data['address'],
            phone=data.get('phone', ''),  # Include phone if provided
            total_amount=data['total_amount'],
            payment_method=data['payment_method']
        )
        db.session.add(received_order)
        db.session.flush()  # Get the ID

        # Save items
        items_count = 0
        for item in data['items']:
            received_item = ReceivedOrderItem(
                order_id=received_order.id,
                product_id=item['product_id'],
                product_name=item['product_name'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(received_item)
            items_count += 1

        db.session.commit()
        
        current_app.logger.info(
            f"[Admin API] ✓ Order {order_id} saved successfully with {items_count} items"
        )

        return jsonify({
            'message': 'Order received successfully',
            'order_id': order_id,
            'items_count': items_count
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"[Admin API] Error receiving order: {e}")
        return jsonify({'error': 'Internal server error'}), 500