# import os
# from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory
# from flask_mail import Message, Mail
# from flask_login import login_user, login_required, logout_user, current_user, LoginManager
# from models import db, User, Admin, JobPost, Application
# from forms import UserSignupForm, AdminSignupForm, LoginForm, JobPostForm, ApplyJobForm
# from sqlalchemy import or_
# from werkzeug.security import generate_password_hash, check_password_hash
# from werkzeug.utils import secure_filename
# from dotenv import load_dotenv

# load_dotenv()

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# app.config['UPLOAD_FOLDER'] = 'uploads'
# app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

# db.init_app(app)

# # Email configuration
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
# app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True

# mail = Mail(app)

# login_manager = LoginManager(app)
# login_manager.login_view = 'user_login'

# @login_manager.user_loader
# def load_user(user_id):
#     try:
#         user_type, id = user_id.split(":")
#         if user_type == "user":
#             return User.query.get(int(id))
#         elif user_type == "admin":
#             return Admin.query.get(int(id))
#     except ValueError:
#         return None

# # Helper function to check allowed file extensions
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# @app.route("/")
# def home():
#     return render_template("home.html", title="Home")

# @app.route("/about")
# def about():
#     return render_template("about.html", title="About")

# @app.route("/services")
# def services():
#     return render_template("services.html", title="Services")

# @app.route("/contact")
# def contact():
#     return render_template("contact.html", title="Contact")

# #Authentication
# @app.route("/user/signup", methods=['GET', 'POST'])
# def user_signup():
#     form = UserSignupForm()
#     if form.validate_on_submit():
#         existing_user = User.query.filter_by(email=form.email.data).first()
#         if existing_user:
#             flash('Email already exists. Please log in.', 'danger')
#             return redirect(url_for('user_login'))

#         hashed_pw = generate_password_hash(form.password.data)
#         new_user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
#         db.session.add(new_user)
#         db.session.commit()
#         flash('Account created successfully!', 'success')
#         return redirect(url_for('user_login'))
#     return render_template('user_signup.html', form=form)

# @app.route("/admin/signup", methods=['GET', 'POST'])
# def admin_signup():
#     form = AdminSignupForm()
#     if form.validate_on_submit():
#         existing_admin = Admin.query.filter_by(email=form.email.data).first()
#         if existing_admin:
#             flash('Email already exists. Please log in.', 'danger')
#             return redirect(url_for('admin_login'))

#         hashed_pw = generate_password_hash(form.password.data)
#         new_admin = Admin(username=form.username.data, email=form.email.data, password=hashed_pw)
#         db.session.add(new_admin)
#         db.session.commit()
#         flash('Admin account created successfully!', 'success')
#         return redirect(url_for('admin_login'))
#     return render_template('admin_signup.html', form=form)

# @app.route("/user/login", methods=['GET', 'POST'])
# def user_login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user and check_password_hash(user.password, form.password.data):
#             login_user(user)
#             return redirect(url_for('users_dashboard'))
#         flash('Invalid credentials', 'danger')
#     return render_template('user_login.html', form=form)

# @app.route("/user/dashboard")
# @login_required
# def users_dashboard():
#     if not isinstance(current_user, User):
#         return redirect(url_for('admin_dashboard'))

#     page = request.args.get('page', 1, type=int)
#     search_query = request.args.get('q', '')

#     jobs_query = JobPost.query

#     if search_query:
#         jobs_query = jobs_query.filter(
#             or_(
#                 JobPost.title.ilike(f"%{search_query}%"),
#                 JobPost.description.ilike(f"%{search_query}%"),
#                 JobPost.requirements.ilike(f"%{search_query}%")
#             )
#         )

#     jobs = jobs_query.order_by(JobPost.date_posted.desc()).paginate(page=page, per_page=5)

#     return render_template("users_dashboard.html", user=current_user, jobs=jobs, search_query=search_query)

# @app.route("/admin/login", methods=['GET', 'POST'])
# def admin_login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         admin = Admin.query.filter_by(email=form.email.data).first()
#         if admin and check_password_hash(admin.password, form.password.data):
#             login_user(admin)
#             return redirect(url_for('admin_dashboard'))
#         flash('Invalid credentials', 'danger')
#     return render_template('admin_login.html', form=form)

# @app.route("/admin/dashboard")
# @login_required
# def admin_dashboard():
#     if not isinstance(current_user, Admin):
#         return redirect(url_for('users_dashboard'))
    
#     jobs = JobPost.query.filter_by(admin_id=current_user.id).order_by(JobPost.date_posted.desc()).all()
#     return render_template("admin_dashboard.html", admin=current_user, jobs=jobs)


# @app.route("/admin/post-job", methods=['GET', 'POST'])
# @login_required
# def post_job():
#     if not isinstance(current_user, Admin):
#         return redirect(url_for('users_dashboard'))
    
#     form = JobPostForm()
#     if form.validate_on_submit():
#         job = JobPost(
#             title=form.title.data,
#             description=form.description.data,
#             requirements=form.requirements.data,
#             admin_id=current_user.id
#         )
#         db.session.add(job)
#         db.session.commit()
#         flash('Job posted!', 'success')

#         # Send email to all users about the new job post
#         users = User.query.all()
#         for user in users:
#             msg = Message(f"New Job: {job.title}",
#                           sender=os.getenv('MAIL_USERNAME'),
#                           recipients=[user.email])
#             msg.body = f"Hi {user.username},\n\nA new job has been posted: {job.title}. Visit your dashboard to apply!\n\n{url_for('users_dashboard', _external=True)}"
#             mail.send(msg)

#         return redirect(url_for('admin_dashboard'))
#     return render_template('post_job.html', form=form)

# @app.route("/apply/<int:job_id>", methods=['POST'])
# @login_required
# def apply(job_id):
#     if isinstance(current_user, Admin):
#         return redirect(url_for('admin_dashboard'))
    
#     job = JobPost.query.get(job_id)
#     if not job:
#         flash('Job not found.', 'danger')
#         return redirect(url_for('users_dashboard'))

#     form = ApplyJobForm()
#     if form.validate_on_submit():
#         # Handle file uploads (CV & Certificate)
#         if 'cv' in request.files and allowed_file(request.files['cv'].filename):
#             cv = request.files['cv']
#             cv_filename = secure_filename(cv.filename)
#             cv.save(os.path.join(app.config['UPLOAD_FOLDER'], cv_filename))
#         else:
#             flash('Invalid file type for CV.', 'danger')
#             return redirect(url_for('users_dashboard'))

#         if 'certificate' in request.files and allowed_file(request.files['certificate'].filename):
#             certificate = request.files['certificate']
#             cert_filename = secure_filename(certificate.filename)
#             certificate.save(os.path.join(app.config['UPLOAD_FOLDER'], cert_filename))

#         application = Application(user_id=current_user.id, job_id=job.id, cv=cv_filename, certificate=cert_filename)
#         db.session.add(application)
#         db.session.commit()
#         flash('Applied successfully!', 'success')

#         # Send email confirmation to user
#         msg = Message(f"Job Application Confirmation: {job.title}",
#                       sender=os.getenv('MAIL_USERNAME'),
#                       recipients=[current_user.email])
#         msg.body = f"Hello {current_user.username},\n\nYou have successfully applied for the job: {job.title}. We will review your application soon.\n\nBest regards,\nJob Portal Team"
#         mail.send(msg)

#         return redirect(url_for('users_dashboard'))

# @app.route("/admin/applicants/<int:job_id>")
# @login_required
# def view_applicants(job_id):
#     if not isinstance(current_user, Admin):
#         return redirect(url_for('users_dashboard'))
    
#     job = JobPost.query.get(job_id)
#     if not job or job.admin_id != current_user.id:
#         return redirect(url_for('admin_dashboard'))

#     applications = job.applications
#     return render_template('view_applicants.html', applications=applications, job=job)

# @app.route("/admin/accept/<int:application_id>")
# @login_required
# def accept_application(application_id):
#     if not isinstance(current_user, Admin):
#         return redirect(url_for('users_dashboard'))
    
#     application = Application.query.get(application_id)
#     if not application or application.job.admin_id != current_user.id:
#         return redirect(url_for('admin_dashboard'))

#     application.status = 'accepted'
#     db.session.commit()
#     flash('Application accepted.', 'success')
#     return redirect(url_for('view_applicants', job_id=application.job_id))

# # appplication status
# @app.route('/admin/update_status/<int:application_id>', methods=['POST'])
# @login_required
# def update_application_status(application_id):
#     if not isinstance(current_user, Admin):
#         return redirect(url_for('users_dashboard'))

#     application = Application.query.get(application_id)
#     if not application:
#         flash('Application not found.', 'danger')
#         return redirect(url_for('admin_dashboard'))
    
#     # Ensure that the admin is allowed to change the status of applications for jobs they posted
#     if application.job.admin_id != current_user.id:
#         flash('You do not have permission to change this application status.', 'danger')
#         return redirect(url_for('admin_dashboard'))

#     new_status = request.form.get('status')  # 'status' will be the key for form data
#     if new_status not in ['under review', 'accepted', 'rejected']:
#         flash('Invalid status.', 'danger')
#         return redirect(url_for('admin_dashboard'))

#     # Update the application status
#     application.status = new_status
#     db.session.commit()
#     flash(f'Application status updated to {new_status}.', 'success')
#     return redirect(url_for('view_applicants', job_id=application.job_id))

# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     session.clear()
#     return redirect(url_for('user_login'))
