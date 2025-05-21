import os
import uuid
import requests
from math import ceil
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, current_app, request, flash, session, send_from_directory,abort
from flask_login import LoginManager, UserMixin, login_user,login_required, logout_user, current_user
from models import db, bcrypt, User, Admin, JobPost, Application, News, Donation
from forms import UserSignupForm, AdminSignupForm, LoginForm, DonationForm, JobPostForm, PasswordResetForm, PasswordResetRequestForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# token for password reset
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Paystack using test mode.
# Live mode will be implemented later
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_INITIALIZE_URL = "https://api.paystack.co/transaction/initialize"


# flask mail
mail = Mail(app)

# set max upload file size
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit

# File upload settings
UPLOAD_FOLDER = os.path.join('static', 'uploads')
PROFILE_PIC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helpers
def allowed_profile_pic(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in PROFILE_PIC_EXTENSIONS

def allowed_document(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in DOCUMENT_EXTENSIONS




db.init_app(app)
bcrypt.init_app(app)

# db miigration
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'user_login'

@login_manager.user_loader
def load_user(user_id):
    try:
        user_type, id = user_id.split(":")
        if user_type == "user":
            return User.query.get(int(id))
        elif user_type == "admin":
            return Admin.query.get(int(id))
    except ValueError:
        return None


@app.route('/')
def home():
    # everyone can see on the homepage
    latest_news = News.query.order_by(News.created_at.desc()).limit(5).all()
    return render_template('home.html', latest_news=latest_news)


@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/services")
def services():
    return render_template("services.html", title="Services")

@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")

# news
@app.route('/news')
def news():
    news_list = News.query.order_by(News.created_at.desc()).all()
    return render_template('news.html', news_list=news_list)

# if users click on carousel, it should direct them to the news section for them to read more
@app.route('/news/<int:news_id>')
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    return render_template('news_detail.html', news=news)

# job
@app.route("/job")
def job():
    jobs = JobPost.query.order_by(JobPost.id.desc()).all()  # fetch all jobs
    return render_template("jobs.html", title="Job", jobs=jobs)


# contact for users to send email to admin
@app.route('/submit', methods=['POST'])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message_body = request.form['message']

    # Construct the email content
    msg = Message(subject=f"Contact Form: {subject}",
                  sender=email,
                  recipients=[os.getenv('MAIL_USERNAME')])  # Realmindx receives it

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

    return redirect(url_for('contact'))


# applying from homepage
@app.route('/apply_homepage/<int:job_id>', methods=['POST'])
def apply_homepage(job_id):
    if not current_user.is_authenticated:
        session['next'] = 'users_dashboard'  # Save after login redirection
        flash('You must sign up or log in first to apply.', 'warning')
        return redirect(url_for('user_signup'))  # send them to signup

    # If user is already logged in, just send to dashboard
    return redirect(url_for('users_dashboard'))

# jobs
@app.route('/jobs')
def job_listings():
    keyword = request.args.get('keyword', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 5

    query = JobPost.query
    if keyword:
        query = query.filter(JobPost.title.ilike(f"%{keyword}%"))

    total = query.count()
    jobs = query.order_by(JobPost.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('jobs.html',
                           jobs=jobs.items,
                           current_page=page,
                           total_pages=jobs.pages,
                           keyword=keyword)

# Donation using Paystack
@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        amount = int(request.form['amount']) * 100  # Convert to pesewas
        reference = str(uuid.uuid4())

        # Save donation record
        donation = Donation(name=name, email=email, amount=amount, reference=reference)
        db.session.add(donation)
        db.session.commit()

        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": email,
            "amount": amount,
            "reference": reference,
            "callback_url": url_for('donation_success', _external=True)
        }

        try:
            response = requests.post(PAYSTACK_INITIALIZE_URL, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            payment_url = response.json()['data']['authorization_url']
            return redirect(payment_url)

        except requests.exceptions.Timeout:
            flash("Request timed out. Please try again.", "warning")
            return render_template("errors/timeout.html"), 504

        except requests.exceptions.ConnectionError:
            flash("Could not connect to Paystack. Check your internet and try again.", "danger")
            return render_template("errors/connection_error.html"), 502

        except requests.exceptions.RequestException as e:
            flash("Something went wrong while initializing payment.", "danger")
            return render_template("errors/general_error.html", error=str(e)), 500

    return render_template('donate.html')

@app.route('/donation-success')
def donation_success():
    # Add your webhook or verification later if needed
    flash("Thank you for your donation!", "success")
    return render_template('donation_success.html')

@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    form = UserSignupForm()
    
    if form.validate_on_submit():
        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('user_login'))

        # Check if username already exists
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_username:
            flash('Username already taken. Please choose another.', 'danger')
            return redirect(url_for('user_signup'))

        # Hash the password and create a new user
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )

        # Save to database
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('user_login'))

    return render_template('user_signup.html', form=form)


@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    form = AdminSignupForm()
    if form.validate_on_submit():
        existing_admin = Admin.query.filter_by(email=form.email.data).first()
        if existing_admin:
            flash('Email already exists. Please log in.', 'danger')
            return redirect(url_for('admin_login'))

        hashed_pw = generate_password_hash(form.password.data)
        new_admin = Admin(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(new_admin)
        db.session.commit()
        flash('Admin account created successfully!', 'success')
        return redirect(url_for('admin_login'))

    return render_template('admin_signup.html', form=form)

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)

            next_page = session.pop('next', None)
            if next_page:
                return redirect(url_for(next_page))
            return redirect(url_for('users_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('user_login.html', form=form)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin and check_password_hash(admin.password, form.password.data):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin_login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('home'))

@app.route('/users/dashboard')
@login_required
def users_dashboard():
    # Check if current user is a regular User (not admin)
    if not isinstance(current_user, User):
        return redirect(url_for('admin_dashboard'))

    # Get all job posts
    jobs = JobPost.query.order_by(JobPost.id.desc()).all()

    # Get job IDs the user has already applied for
    applied_jobs = [application.job_id for application in current_user.applications]

    return render_template('users_dashboard.html', jobs=jobs, applied_jobs=applied_jobs)



@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        return redirect(url_for('users_dashboard'))
    jobs = JobPost.query.filter_by(admin_id=current_user.id).all()
    return render_template('admin_dashboard.html', admin=current_user, jobs=jobs)

@app.route('/admin/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if not isinstance(current_user, Admin):
        return redirect(url_for('users_dashboard'))

    form = JobPostForm()
    
    if form.validate_on_submit():
        job = JobPost(
            title=form.title.data,
            description=form.description.data,
            requirements=form.requirements.data,
            admin_id=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('post_job'))

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 5
    jobs_paginated = JobPost.query.order_by(JobPost.id.desc()).paginate(page=page, per_page=per_page)
    
    return render_template(
        'post_job.html',
        form=form,
        jobs=jobs_paginated.items,
        total_pages=jobs_paginated.pages,
        current_page=page
    )

# News 
@app.route('/admin/post-news', methods=['GET', 'POST'])
@login_required
def post_news():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')
        image_url = None

        if image and image.filename:
            filename = secure_filename(image.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(path)
            image_url = f'uploads/{filename}'

        news_item = News(title=title, content=content, image_url=image_url, admin_id=current_user.id)
        db.session.add(news_item)
        db.session.commit()
        flash('News posted successfully!', 'success')
        return redirect(url_for('news'))

    return render_template('admin_post_news.html')
# Edit News
@app.route('/admin/edit-news/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    news_item = News.query.get_or_404(news_id)
    if news_item.admin_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        news_item.title = request.form['title']
        news_item.content = request.form['content']
        image = request.files.get('image')

        if image and image.filename:
            filename = secure_filename(image.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(path)
            news_item.image_url = f'uploads/{filename}'

        db.session.commit()
        flash('News updated successfully!', 'success')
        return redirect(url_for('news'))

    return render_template('admin_post_news.html', news_item=news_item, editing=True)
#Delete News
@app.route('/admin/delete-news/<int:news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    news_item = News.query.get_or_404(news_id)
    if news_item.admin_id != current_user.id:
        abort(403)

    db.session.delete(news_item)
    db.session.commit()
    flash('News deleted successfully.', 'success')
    return redirect(url_for('news'))
# managing news on dashboard
@app.route('/admin/news-dashboard')
@login_required
def admin_news_dashboard():
    if not isinstance(current_user, Admin):
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    news_list = News.query.filter_by(admin_id=current_user.id).order_by(News.created_at.desc()).all()
    return render_template('admin_news_dashboard.html', news_list=news_list)

# crud
# Edit job post
@app.route('/admin/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('users_dashboard'))

    job = JobPost.query.get_or_404(job_id)

    if job.admin_id != current_user.id:
        flash("You are not authorized to edit this job.", "danger")
        return redirect(url_for('post_job'))

    form = JobPostForm(obj=job)

    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.requirements = form.requirements.data
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('post_job'))

    return render_template('edit_job.html', form=form, job=job)


# Delete job post
@app.route('/admin/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('users_dashboard'))

    job = JobPost.query.get_or_404(job_id)

    if job.admin_id != current_user.id:
        flash("You are not authorized to delete this job.", "danger")
        return redirect(url_for('post_job'))

    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('post_job'))


# cv uploads
# Where you want to store uploaded CVs and certificates
#if users apply to a job, it will show applied after click on apply 
@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    job = JobPost.query.get_or_404(job_id)

    existing_application = Application.query.filter_by(user_id=current_user.id, job_id=job.id).first()
    if existing_application:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('users_dashboard'))

    if request.method == 'POST':
        cv = request.files.get('cv')
        certificate = request.files.get('certificate')
        cover_letter = request.files.get('cover_letter')

        if not cv or not allowed_document(cv.filename):
            flash('CV must be a PDF, DOC, or DOCX file.', 'danger')
            return redirect(request.url)

        if not certificate or not allowed_document(certificate.filename):
            flash('Certificate must be a PDF, DOC, or DOCX file.', 'danger')
            return redirect(request.url)

        # Save CV
        cv_filename = f"{uuid.uuid4().hex}_{secure_filename(cv.filename)}"
        cv_path = os.path.join(app.config['UPLOAD_FOLDER'], cv_filename)
        cv.save(cv_path)

        # Save Certificate
        certificate_filename = f"{uuid.uuid4().hex}_{secure_filename(certificate.filename)}"
        certificate_path = os.path.join(app.config['UPLOAD_FOLDER'], certificate_filename)
        certificate.save(certificate_path)

        # Optional Cover Letter
        cover_letter_filename = None
        cover_letter_path = None
        if cover_letter and cover_letter.filename != '':
            if not allowed_document(cover_letter.filename):
                flash('Cover letter must be a PDF, DOC, or DOCX file.', 'danger')
                return redirect(request.url)

            cover_letter_filename = f"{uuid.uuid4().hex}_{secure_filename(cover_letter.filename)}"
            cover_letter_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_letter_filename)
            cover_letter.save(cover_letter_path)

        # Save Application to DB
        new_application = Application(
            date_applied=datetime.now(),
            status='Under review',
            cv=cv_filename,
            certificate=certificate_filename,
            cover_letter=cover_letter_filename,
            user_id=current_user.id,
            job_id=job_id
        )
        db.session.add(new_application)
        db.session.commit()

        # Send Email to RealMindX
        try:
            admin_msg = Message(
                subject=f"New Job Application for {job.title}",
                recipients=["realmindx@example.com"],  # Change this to the actual admin email
                body=(
                    f"New application received from {current_user.username} ({current_user.email}) "
                    f"for the job: {job.title}.\n\nPlease find the attached documents."
                )
            )
            with app.open_resource(cv_path) as fp:
                admin_msg.attach(cv_filename, "application/octet-stream", fp.read())
            with app.open_resource(certificate_path) as fp:
                admin_msg.attach(certificate_filename, "application/octet-stream", fp.read())
            if cover_letter_path:
                with app.open_resource(cover_letter_path) as fp:
                    admin_msg.attach(cover_letter_filename, "application/octet-stream", fp.read())
            mail.send(admin_msg)
        except Exception as e:
            print("Admin email error:", e)

        # Send Confirmation Email to Applicant
        try:
            user_msg = Message(
                subject="Application Received - Realmindx Education",
                sender=os.getenv('MAIL_USERNAME'),
                recipients=[current_user.email]
            )
            user_msg.body = f"""Dear {current_user.username},

Thank you for applying for the position: {job.title}.

We have received your application and our team will review it shortly.
If you are shortlisted, someone from our team will contact you soon.

Best regards,  
RealmIndx Recruitment Team
"""
            mail.send(user_msg)
            flash("Application submitted successfully.", "success")
        except Exception as e:
            print("User email error:", e)
            flash("Application submitted, but failed to send confirmation email.", "warning")

        return redirect(url_for('users_dashboard'))

    return render_template('apply.html', job=job)

# profile picture  for users
@app.route('/upload_profile_pic', methods=['POST'])
@login_required
def upload_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('users_dashboard'))

    file = request.files['profile_pic']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('users_dashboard'))

    if file:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.root_path, 'static/uploads/', filename)
        file.save(upload_path)

        # Delete old pic if exists
        if current_user.profile_pic:
            try:
                os.remove(os.path.join(app.root_path, 'static/uploads/', current_user.profile_pic))
            except Exception:
                pass

        current_user.profile_pic = filename
        db.session.commit()
        flash('Profile picture updated!', 'success')

    return redirect(url_for('users_dashboard'))

# delete profile
@app.route('/delete_profile_pic', methods=['POST'])
@login_required
def delete_profile_pic():
    if current_user.profile_pic:
        try:
            os.remove(os.path.join(app.root_path, 'static/uploads/', current_user.profile_pic))
        except Exception:
            pass
        current_user.profile_pic = None
        db.session.commit()
        flash('Profile picture deleted.', 'info')

    return redirect(url_for('users_dashboard'))

# profile picture uploads for admin
@app.route('/upload_admin_profile_pic', methods=['POST'])
@login_required
def upload_admin_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('admin_dashboard'))

    file = request.files['profile_pic']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('admin_dashboard'))

    if file:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.root_path, 'static/uploads/', filename)
        file.save(upload_path)

        # Delete old pic if exists
        if current_user.profile_pic:
            try:
                os.remove(os.path.join(app.root_path, 'static/uploads/', current_user.profile_pic))
            except Exception:
                pass

        current_user.profile_pic = filename
        db.session.commit()
        flash('Profile picture updated!', 'success')

    return redirect(url_for('admin_dashboard'))

# delete profile
@app.route('/delete_admin_profile_pic', methods=['POST'])
@login_required
def delete_admin_profile_pic():
    if current_user.profile_pic:
        try:
            os.remove(os.path.join(app.root_path, 'static/uploads/', current_user.profile_pic))
        except Exception:
            pass
        current_user.profile_pic = None
        db.session.commit()
        flash('Profile picture deleted.', 'info')

    return redirect(url_for('admin_dashboard'))

# admin to see uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/admin/applicants/<int:job_id>')
@login_required
def view_applicants(job_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('users_dashboard'))
    job = JobPost.query.get(job_id)
    if not job or job.admin_id != current_user.id:
        return redirect(url_for('admin_dashboard'))
    applications = job.applications
    return render_template('view_applicants.html', applications=applications)

@app.route('/admin/accept/<int:application_id>')
@login_required
def accept_application(application_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('users_dashboard'))
    application = Application.query.get(application_id)
    if not application or application.job.admin_id != current_user.id:
        return redirect(url_for('admin_dashboard'))
    application.status = 'accepted'
    db.session.commit()
    flash('Application accepted.', 'success')
    return redirect(url_for('view_applicants', job_id=application.job_id))

# password reset and forgot password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_link = url_for('reset_password', token=token, _external=True)

            try:
                msg = Message("Password Reset Request",
                              sender=os.getenv('MAIL_USERNAME'),
                              recipients=[user.email])
                msg.body = f"Click the link to reset your password: {reset_link}"
                mail.send(msg)
                flash('Password reset link has been sent to your email.', 'info')
            except Exception as e:
                print(f"Email sending failed: {e}")
                flash('Could not send email. Please try again later.', 'danger')
        else:
            flash('No account found with that email.', 'danger')
        return redirect(url_for('user_login'))
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()
        user.set_password(form.password.data)  # Ensure your User model supports this
        db.session.commit()
        flash('Your password has been updated.', 'success')
        return redirect(url_for('user_login'))
    
    return render_template('reset_password.html', form=form)
