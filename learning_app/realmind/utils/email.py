from flask import render_template, current_app, url_for
from flask_mail import Message
from learning_app.extensions import mail, db
from sqlalchemy import or_
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


def _match_reason(user, job_subject, job_levels):
    """Return a human-readable match reason, or None if the teacher doesn't match."""
    user_subjects = {
        s.strip().lower()
        for s in (user.preferred_subject or '').split(',')
        if s.strip()
    }
    user_levels = {
        l.strip().lower()
        for l in (user.preferred_level or '').split(',')
        if l.strip()
    }

    if not user_subjects and not user_levels:
        return None

    subject_hit = bool(job_subject) and job_subject.strip().lower() in user_subjects
    level_hit   = bool(
        {jl.strip().lower() for jl in job_levels} & user_levels
    )

    if subject_hit and level_hit:
        return f"your subject area ({job_subject}) and teaching level preferences"
    if subject_hit:
        return f"your subject area ({job_subject})"
    if level_hit:
        return "your teaching level preferences"
    return None


def notify_matching_teachers(job):
    """
    Send job-alert emails to registered teachers (User records) whose
    preferred subject or level matches the newly posted job.

    Only queries users who are active, verified, and have at least one
    preference set — filtering at the DB level avoids loading the entire
    user table into memory.

    Returns (sent_count, failed_count).
    """
    from learning_app.realmind.models import User

    logger = current_app.logger

    job_levels  = [l.strip() for l in job.level.split(',') if l.strip()]
    job_subject = (job.subject or '').strip()

    # Pre-filter at the DB level: only users with at least one preference set.
    # Python-level _match_reason() then decides whether the preference
    # actually overlaps with this specific job.
    teachers = User.query.filter(
        User.is_active == True,
        User.is_verified == True,
        or_(
            User.preferred_subject.isnot(None),
            User.preferred_level.isnot(None),
        )
    ).all()

    sent = failed = 0

    for teacher in teachers:
        reason = _match_reason(teacher, job_subject, job_levels)
        if not reason:
            continue

        try:
            deadline_str = (
                job.application_deadline.strftime('%B %d, %Y at %I:%M %p')
                if job.application_deadline else None
            )
            description  = (job.description or '').strip()
            truncated    = len(description) > 200
            description  = description[:200]

            html = render_template(
                'emails/job_notification.html',
                teacher_name=teacher.fullname,
                job_title=job.title,
                job_subject=job_subject,
                job_level=job.level,
                job_location=job.location,
                job_description=description,
                job_description_truncated=truncated,
                job_deadline=deadline_str,
                apply_url=url_for('user.apply', job_id=job.id, _external=True),
                match_reason=reason,
            )

            msg = Message(
                subject=f"New Teaching Opportunity: {job.title} – RealMindX Education",
                sender=os.getenv('MAIL_USERNAME'),
                recipients=[teacher.email],
                html=html,
            )
            mail.send(msg)
            sent += 1
            logger.info(f"Job alert sent to {teacher.email} (job_id={job.id})")

        except Exception as exc:
            failed += 1
            logger.error(
                f"Job alert failed for {teacher.email} (job_id={job.id}): {exc}"
            )

    logger.info(
        f"Job notifications complete for '{job.title}' (ID {job.id}): "
        f"{sent} sent, {failed} failed"
    )
    return sent, failed
