from flask import Blueprint, render_template, request, flash, redirect, url_for
from realmind.models import News, Gallery
from flask_mail import Message
from realmind import mail

import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    gallery_slides = Gallery.query.filter_by(file_type='image').order_by(Gallery.date_posted.desc()).limit(5).all()
    latest_news = News.query.order_by(News.created_at.desc()).limit(5).all()
    return render_template('home.html', latest_news=latest_news)

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

@main_bp.route('/news/<int:news_id>')
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    return render_template('news_detail.html', news=news)

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
    name = request.form['name']
    email = request.form['email']
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
