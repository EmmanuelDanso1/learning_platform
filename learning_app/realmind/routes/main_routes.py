from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from learning_app.realmind.models import News, Gallery
from flask_mail import Message
from flask_wtf.csrf import generate_csrf,validate_csrf, CSRFError
from learning_app.extensions import mail
from wtforms.validators import ValidationError


import os

main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.route('/')
def home():
    gallery_slides = Gallery.query.filter_by(file_type='image').order_by(Gallery.date_posted.desc()).limit(6).all()
    latest_news = News.query.order_by(News.created_at.desc()).limit(5).all()
    return render_template('home.html', latest_news=latest_news,gallery_slides=gallery_slides)

@main_bp.route('/about')
def about():
    return render_template("about.html", title="About")

@main_bp.route('/services')
def services():
    return render_template("services.html", title="Services")

@main_bp.route('/contact')
def contact():
    return render_template("contact.html", title="Contact")

@main_bp.route('/news')
def news():
    news_list = News.query.order_by(News.created_at.desc()).all()
    return render_template('news.html', news_list=news_list)

# booking service route
@main_bp.route('/book_service', methods=['GET', 'POST'])
def book_service():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        help_text = request.form.get('help')
        service = request.form.get('service')
        more_info = request.form.get('more_info')

        # Send email to RealMindX
        msg = Message(
            subject=f"Service Booking Request: {service}",
            sender=email,
            recipients=['realmindxgh@gmail.com']
        )
        msg.body = f"""
        New service booking received:
        
        Name: {name}
        Email: {email}
        Phone: {phone}
        Service Needed: {service}
        How may we help: {help_text}
        More Information: {more_info if more_info else 'N/A'}
        """
        try:
            mail.send(msg)
            flash('Your request has been submitted successfully! We’ll get back to you soon.', 'success')
            return redirect(url_for('main.book_service'))
        except Exception as e:
            flash('An error occurred while sending your message. Please try again later.', 'danger')

    return render_template('book_service.html')

@main_bp.route("/news/<int:news_id>")
def news_detail(news_id):
    news_item = News.query.get(news_id)
    if not news_item:
        abort(404)
    return render_template("news_detail.html", news_item=news_item)

@main_bp.route('/gallery')
def gallery():
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('type')  # 'image', 'video', or None

    query = Gallery.query
    if filter_type in ['image', 'video']:
        query = query.filter_by(file_type=filter_type)

    pagination = query.order_by(Gallery.date_posted.desc()).paginate(page=page, per_page=9)
    return render_template('gallery.html', gallery_items=pagination.items, pagination=pagination, filter_type=filter_type)


@main_bp.route('/submit', methods=['POST'])
def submit_contact():
    # Validate CSRF token
    token = request.form.get('csrf_token')
    try:
        validate_csrf(token)
    except ValidationError:
        abort(400, description="CSRF token is missing or invalid.")

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    subject = request.form['subject']
    message_body = request.form['message']

    msg = Message(
        subject=f"Contact Form: {subject}",
        sender=email,
        recipients=[os.getenv('MAIL_USERNAME')]
    )

    msg.body = f"""
    You have received a new message from your website contact form:

    Name: {name}
    Email: {email}
    Phone: {phone}
    Subject: {subject}
    Message:
    {message_body}
    """

    try:
        mail.send(msg)
        flash("Your message has been sent to Realmindx successfully!", "success")
    except Exception as e:
        print(f"Mail sending failed: {e}")
        flash("An error occurred while sending your message. Please try again later.", "danger")

    return redirect(url_for('main.contact'))

@main_bp.route('/unsubscribe-feedback', methods=['POST'])
def unsubscribe_feedback():
    email = request.form.get('email')
    reasons = request.form.getlist('reason')
    comments = request.form.get('comments', '')
    
    # Log feedback
    current_app.logger.info(
        f"Unsubscribe feedback from {email}: Reasons={reasons}, Comments={comments}"
    )
    
    # Optional: Save to database
    # feedback = UnsubscribeFeedback(
    #     email=email,
    #     reasons=','.join(reasons),
    #     comments=comments
    # )
    # db.session.add(feedback)
    # db.session.commit()
    
    flash("Thank you for your feedback!", "success")
    return redirect('https://realmindxgh.com')