from flask import render_template, current_app
from flask_mail import Message
from learning_app.extensions import mail
import os


def send_order_status_email(order, new_status):
    """
    Send email notification to customer based on order status
    """
    try:
        # Email templates for each status
        email_templates = {
            'Received': {
                'subject': f'Order Received - #{order.original_order_id}',
                'body': f"""
Dear {order.full_name},

Thank you for your order! We have received your order #{order.original_order_id} and it is now in our system.

Order Details:
- Order ID: {order.original_order_id}
- Total Amount: GH₵{order.total_amount:.2f}
- Payment Method: {order.payment_method}

We will begin processing your order shortly. You will receive another email when your order moves to the next stage.

Thank you for shopping with RealMindX Education Ltd!

Best regards,
RealMindX Education Ltd Team
"""
            },
            'Processing': {
                'subject': f'Your Order Is Being Packaged! - #{order.original_order_id}',
                'body': f"""
Dear {order.full_name},

Good News! Your order #{order.original_order_id} has been confirmed and is now being prepared for shipment.

Thank you for shopping with RealMindX Education Ltd!

We will contact you shortly to confirm your order details, so please keep your phone accessible. If you do not receive a confirmation call within One (1) business day, please reach out to our customer service.

Order Details:
- Order ID: {order.original_order_id}
- Total Amount: GH₵{order.total_amount:.2f}
- Status: Processing

Best regards,
RealMindX Education Ltd Team
"""
            },
            'Shipped': {
                'subject': f'Your Order Is On Its Way To You! - #{order.original_order_id}',
                'body': f"""
Dear {order.full_name},

Your order #{order.original_order_id} is on its way 🚚

We've handed your package over to our delivery partner. Details of the delivery person will be sent to you via SMS shortly.

Order Details:
- Order ID: {order.original_order_id}
- Total Amount: GH₵{order.total_amount:.2f}
- Status: Shipped

Thank you for shopping with RealMindX Education Ltd!

Best regards,
RealMindX Education Ltd Team
"""
            },
            'Delivered': {
                'subject': f'Your Order Has Been Delivered! - #{order.original_order_id}',
                'body': f"""
Dear {order.full_name},

Your order #{order.original_order_id} has been delivered. We hope you're enjoying your purchase!

Thank you for shopping with RealMindX Education Ltd!

If you have a moment, we'd love to hear your feedback. Your experience helps us improve and serve you better. You can contact us on any of our customer care channels.

We look forward to serving you again!

Order Details:
- Order ID: {order.original_order_id}
- Total Amount: GH₵{order.total_amount:.2f}
- Status: Delivered

Best regards,
RealMindX Education Ltd Team
"""
            }
        }
        
        # Get the email template for the status
        if new_status not in email_templates:
            return False
            
        template = email_templates[new_status]
        
        # Create and send the email
        msg = Message(
            subject=template['subject'],
            sender=os.getenv('MAIL_USERNAME'),
            recipients=[order.email]
        )
        msg.body = template['body']
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
