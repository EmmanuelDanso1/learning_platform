import os
import uuid
from math import ceil
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, current_app, request, flash, session, send_from_directory, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, bcrypt, User, Admin, JobPost, Application, News
from forms import UserSignupForm, AdminSignupForm, LoginForm, JobPostForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

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


@app.route("/job")
def job():
    jobs = JobPost.query.order_by(JobPost.id.desc()).all()  # fetch all jobs
    return render_template("jobs.html", title="Job", jobs=jobs)


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



@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    form = UserSignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already exists. Please log in.', 'danger')
            return redirect(url_for('user_login'))

        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)  # LOGIN directly after signup ✅

        next_page = session.pop('next', None)
        if next_page:
            return redirect(url_for(next_page))
        return redirect(url_for('users_dashboard'))

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
        cover_letter = request.files.get('cover_letter')  # Optional field

        if not cv or not allowed_document(cv.filename):
            flash('CV must be a PDF, DOC, or DOCX file.', 'danger')
            return redirect(request.url)

        if not certificate or not allowed_document(certificate.filename):
            flash('Certificate must be a PDF, DOC, or DOCX file.', 'danger')
            return redirect(request.url)

        # Save CV
        cv_filename = f"{uuid.uuid4().hex}_{secure_filename(cv.filename)}"
        cv.save(os.path.join(app.config['UPLOAD_FOLDER'], cv_filename))

        # Save Certificate
        certificate_filename = f"{uuid.uuid4().hex}_{secure_filename(certificate.filename)}"
        certificate.save(os.path.join(app.config['UPLOAD_FOLDER'], certificate_filename))

        # Handle optional cover letter
        cover_letter_filename = None
        if cover_letter and cover_letter.filename != '':
            if not allowed_document(cover_letter.filename):
                flash('Cover letter must be a PDF, DOC, or DOCX file.', 'danger')
                return redirect(request.url)

            cover_letter_filename = f"{uuid.uuid4().hex}_{secure_filename(cover_letter.filename)}"
            cover_letter.save(os.path.join(app.config['UPLOAD_FOLDER'], cover_letter_filename))

        # Save application
        new_application = Application(
            date_applied=datetime.now(),
            status='Under review',
            cv=cv_filename,
            certificate=certificate_filename,
            cover_letter=cover_letter_filename,  # Can be None
            user_id=current_user.id,
            job_id=job_id
        )
        db.session.add(new_application)
        db.session.commit()

        flash('Application submitted successfully!', 'success')
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
