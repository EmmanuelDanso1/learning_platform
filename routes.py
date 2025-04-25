import os
from math import ceil
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, bcrypt, User, Admin, JobPost, Application
from forms import UserSignupForm, AdminSignupForm, LoginForm, JobPostForm
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db.init_app(app)
bcrypt.init_app(app)

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


@app.route("/")
def home():
    return render_template("home.html", title="Home")

@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/services")
def services():
    return render_template("services.html", title="Services")

@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")

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

    return render_template('post_job.html',
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
        flash('Account created successfully!', 'success')
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
    return redirect(url_for('user_login'))

@app.route('/users/dashboard')
@login_required
def users_dashboard():
    if not isinstance(current_user, User):
        return redirect(url_for('admin_dashboard'))

    jobs = JobPost.query.order_by(JobPost.id.desc()).all()  # Get all jobs
    return render_template('users_dashboard.html', jobs=jobs)


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


@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply(job_id):
    if not isinstance(current_user, User):
        flash("Only users can apply for jobs.", "danger")
        return redirect(url_for('users_dashboard'))

    job = JobPost.query.get_or_404(job_id)

    # Optional: check if user already applied
    existing_application = Application.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if existing_application:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('users_dashboard'))

    new_application = Application(user_id=current_user.id, job_id=job_id)
    db.session.add(new_application)
    db.session.commit()
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('users_dashboard'))


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
