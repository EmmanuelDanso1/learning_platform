from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from itsdangerous import URLSafeTimedSerializer
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message
# using the content from __init__.py
from learning_app.realmind.models import User, Admin
from learning_app.realmind.forms import PasswordResetRequestForm, LoginForm, AdminSignupForm, UserSignupForm, PasswordResetForm
from learning_app.extensions import db, mail
import os
from datetime import datetime
from learning_app.realmind.utils.otp_utils import generate_otp, otp_expiry_time

auth_bp = Blueprint('auth', __name__)
s = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))

@auth_bp.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    form = AdminSignupForm()
    
    if form.validate_on_submit():
        existing_admin = Admin.query.filter_by(email=form.email.data).first()
        if existing_admin:
            flash('Email already exists. Please log in.', 'danger')
            return redirect(url_for('auth.admin_login'))

        # Create admin
        new_admin = Admin(
            fullname=form.fullname.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            is_verified=False
        )

        # Generate OTP
        otp = new_admin.generate_otp()

        db.session.add(new_admin)
        db.session.commit()

        # Send OTP email
        try:
            msg = Message(
                subject="Admin Verification Code",
                recipients=[new_admin.email],
                sender="realmindxgh@gmail.com"
            )
            msg.body = f"Your verification code is: {otp}\nThis code expires in 10 minutes."
            mail.send(msg)
        except Exception as e:
            print("Email sending error:", e)
            flash('Error sending verification email. Please try again.', 'danger')
            return redirect(url_for('auth.admin_signup'))

        flash('Admin account created! Check your email for the verification code.', 'success')
        return redirect(url_for('auth.verify_admin_otp', admin_id=new_admin.id))

    return render_template('admin_signup.html', form=form)

# Verify Admin Email
@auth_bp.route('/admin/verify/<int:admin_id>', methods=['GET', 'POST'])
def verify_admin_otp(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    if request.method == 'POST':
        input_otp = request.form.get('otp')
        if admin.otp_code == input_otp and admin.otp_expiry > datetime.utcnow():
            admin.is_verified = True
            admin.otp_code = None
            admin.otp_expiry = None
            db.session.commit()
            flash('Email verified successfully!', 'success')
            return redirect(url_for('auth.admin_login'))
        else:
            flash('Invalid or expired OTP.', 'danger')
    return render_template('admin_verify.html', admin=admin)

@auth_bp.route('/admin/resend-otp/<int:admin_id>', methods=['GET', 'POST'])
def resend_admin_otp(admin_id):
    admin = Admin.query.get_or_404(admin_id)

    # Generate a new OTP
    otp = admin.generate_otp()  # uses the method in Admin model
    db.session.commit()

    # Send OTP email
    try:
        msg = Message(
            subject="Admin Verification Code",
            recipients=[admin.email],
            sender="realmindxgh@gmail.com"
        )
        msg.body = f"Your new verification code is: {otp}\nThis code expires in 10 minutes."
        mail.send(msg)
        flash('A new OTP has been sent to your email.', 'success')
    except Exception as e:
        flash('Error sending verification email. Please try again later.', 'danger')

    return redirect(url_for('auth.verify_admin_otp', admin_id=admin.id))

@auth_bp.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    form = UserSignupForm()
    
    if form.validate_on_submit():

        # Check if email exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('auth.user_login'))

        # Create user
        hashed_password = generate_password_hash(form.password.data)
        otp = generate_otp()

        new_user = User(
            fullname=form.fullname.data,
            email=form.email.data,
            password=hashed_password,
            is_verified=False,
            otp_code=otp,
            otp_expiry=otp_expiry_time()
        )

        db.session.add(new_user)
        db.session.commit()

        # Send OTP email
        try:
            msg = Message(
                subject="Your Verification Code",
                recipients=[new_user.email],
                sender="realmindxgh@gmail.com"
            )
            msg.body = f"Your email verification code is: {otp}\nThis code expires in 10 minutes."
            mail.send(msg)
        except Exception as e:
            flash('Error sending verification email. Please try again.', 'danger')
            return redirect(url_for('auth.user_signup'))

        flash('Account created! Check your email for the verification code.', 'success')
        return redirect(url_for('auth.verify_otp', user_id=new_user.id))

    return render_template('user_signup.html', form=form)

# Verify otp
@auth_bp.route('/verify-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        entered_otp = request.form.get('otp')

        if entered_otp != user.otp_code:
            flash('Invalid verification code.', 'danger')
            return redirect(url_for('auth.verify_otp', user_id=user.id))

        if datetime.utcnow() > user.otp_expiry:
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.resend_otp', user_id=user.id))

        user.is_verified = True
        user.otp_code = None
        user.otp_expiry = None

        db.session.commit()
        login_user(user)

        flash('Your email has been verified! Welcome.', 'success')
        return redirect(url_for('user.users_dashboard'))

    return render_template('verify_otp.html', user=user)

# Resend OTP
@auth_bp.route('/resend-otp/<int:user_id>')
def resend_otp(user_id):
    user = User.query.get_or_404(user_id)

    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiry = otp_expiry_time()
    db.session.commit()

    msg = Message(
        subject="New Verification Code",
        recipients=[user.email],
        sender="realmindxgh@gmail.com"
    )
    msg.body = f"Your new verification code is: {otp}"
    mail.send(msg)

    flash('A new OTP has been sent to your email.', 'success')
    return redirect(url_for('auth.verify_otp', user_id=user.id))


@auth_bp.route('/user/login', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.user_login"))

        # If user uses Google login only
        if user.auth_provider == "google":
            flash("This account is linked to Google Login. Please login using Google.", "warning")
            return redirect(url_for("auth.user_login"))

        # For local users, ensure they have a password
        if not user.password:
            flash("No password set. Please use Google Login.", "warning")
            return redirect(url_for("auth.user_login"))

        # Check password
        if not check_password_hash(user.password, form.password.data):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.user_login"))

        # Check if email is verified
        if not user.is_verified:
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for('auth.verify_otp', user_id=user.id))

        # Successful login
        login_user(user)

        # automatic session for inactive user
        session.permanent =True
        
        # Handle next page redirection
        next_page = session.pop('next', None)
        if next_page:
            return redirect(next_page)

        return redirect(url_for('user.users_dashboard'))

    return render_template("user_login.html", form=form)


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin and check_password_hash(admin.password, form.password.data):
            login_user(admin)
            return redirect(url_for('admin.admin_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin_login.html', form=form)

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))  # adjust as needed

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_link = url_for('auth.reset_password', token=token, _external=True)

            try:
                msg = Message(
                    subject="Password Reset Request",
                    sender=os.getenv('MAIL_USERNAME'),
                    recipients=[user.email]
                )
                msg.body = f"""
Hello {user.username},

We received a request to reset your password.
r
Click the link below to reset it:
{reset_link}

If you did not request this, simply ignore this email.

Regards,
RealmIndx Support Team
"""
                mail.send(msg)
                flash('Password reset link has been sent to your email.', 'info')
            except Exception as e:
                print(f"Email sending failed: {e}")
                flash('Could not send email. Please try again later.', 'danger')
        else:
            flash('No account found with that email.', 'danger')
        return redirect(url_for('auth.user_login'))

    return render_template('forgot_password.html', form=form)

# password reset
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()
        user.set_password(form.password.data)  # Ensure `set_password()` hashes and sets the password
        db.session.commit()
        flash('Your password has been updated.', 'success')
        return redirect(url_for('auth.user_login'))

    return render_template('reset_password.html', form=form)
