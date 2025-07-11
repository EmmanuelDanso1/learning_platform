from flask import render_template, current_app
from flask_mail import Message
from realmind import mail

def send_order_status_email(to, full_name, order_id, status, order_date):
    subject = "Your Order Has Been Delivered"
    sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@realmindxgh@gmail.com')  # fallback just in case

    msg = Message(subject, recipients=[to], sender=sender)
    msg.html = render_template("emails/order_delivered.html", full_name=full_name, order_id=order_id, status=status, order_date=order_date)
    mail.send(msg)
