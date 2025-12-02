from flask import Blueprint,abort, render_template, request, session, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os, uuid
from wtforms.validators import ValidationError
from flask_wtf.csrf import generate_csrf,validate_csrf, CSRFError
from learning_app.extensions import db, mail  
from learning_app.realmind.models import JobPost, Application, User
from flask_mail import Message
from learning_app.realmind.utils.util import allowed_document , allowed_profile_pic, UPLOAD_FOLDER 


user_bp = Blueprint('user', __name__)

@user_bp.route('/users/dashboard')
@login_required
def users_dashboard():
    # Redirect admins
    if getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.admin_dashboard'))

    # Fetch jobs
    jobs = JobPost.query.order_by(JobPost.id.desc()).all()
    applied_jobs = [application.job_id for application in current_user.applications]

    return render_template(
        'users_dashboard.html',
        jobs=jobs,
        applied_jobs=applied_jobs,
        profile_complete=current_user.is_profile_complete
    )


# Profile completion
@user_bp.route("/users/dashboard/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    # Prevent admins from using this page
    if current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == "POST":
        # Update profile fields
        current_user.firstname = request.form.get("firstname")
        current_user.surname = request.form.get("surname")
        current_user.other_names = request.form.get("other_names")
        current_user.phone = request.form.get("phone")
        current_user.ghana_card_number = request.form.get("ghana_card_number")  
        current_user.preferred_level = request.form.get("preferred_level")
        current_user.preferred_subject = request.form.get("preferred_subject")

        # --- DOCUMENT UPLOAD ---
        documents = request.files.get("documents")
        if documents and documents.filename != "":
            filename = secure_filename(documents.filename)

            upload_path = os.path.join(
                current_app.config["UPLOAD_FOLDER_USERS"],
                f"user_{current_user.id}",
                "documents"
            )
            os.makedirs(upload_path, exist_ok=True)

            file_path = os.path.join(upload_path, filename)
            documents.save(file_path)

            current_user.documents = filename 

        # --- PROFILE PICTURE UPLOAD ---
        pic = request.files.get("profile_pic")
        if pic and pic.filename != "":
            filename = secure_filename(pic.filename)

            upload_path = os.path.join(
                current_app.config["UPLOAD_FOLDER_USERS"],
                f"user_{current_user.id}",
                "profile"
            )
            os.makedirs(upload_path, exist_ok=True)

            file_path = os.path.join(upload_path, filename)
            pic.save(file_path)

            current_user.profile_pic = filename

        db.session.commit()
        flash("Profile updated successfully!", "success")

        return redirect(url_for("user.users_dashboard")) 

    return render_template("edit_profile.html")


@user_bp.route('/upload_profile_pic', methods=['POST'])
@login_required
def upload_profile_pic():
    # Validate CSRF token
    token = request.form.get('csrf_token')
    try:
        validate_csrf(token)
    except ValidationError:
        abort(400, description="CSRF token is missing or invalid.")

    if 'profile_pic' not in request.files or request.files['profile_pic'].filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('user.users_dashboard'))

    file = request.files['profile_pic']
    filename = secure_filename(file.filename)
    upload_path = os.path.join(current_app.root_path, 'static/uploads/', filename)
    file.save(upload_path)

    # Delete old profile pic if it exists
    if current_user.profile_pic:
        try:
            os.remove(os.path.join(current_app.root_path, 'static/uploads/', current_user.profile_pic))
        except Exception:
            pass

    current_user.profile_pic = filename
    db.session.commit()
    flash('Profile picture updated!', 'success')
    return redirect(url_for('user.users_dashboard'))


@user_bp.route('/delete_profile_pic', methods=['POST'])
@login_required
def delete_profile_pic():
    # CSRF token validation
    token = request.form.get('csrf_token')
    try:
        validate_csrf(token)
    except ValidationError:
        abort(400, description="CSRF token is missing or invalid.")

    if current_user.profile_pic:
        try:
            os.remove(os.path.join(current_app.root_path, 'static/uploads/', current_user.profile_pic))
        except Exception:
            pass
        current_user.profile_pic = None
        db.session.commit()
        flash('Profile picture deleted.', 'info')

    return redirect(url_for('user.users_dashboard'))


@user_bp.route('/apply_homepage/<int:job_id>', methods=['POST'])
def apply_homepage(job_id):
    try:
        token = request.form.get('csrf_token')
        validate_csrf(token)
    except CSRFError:
        abort(400, description="CSRF token is missing or invalid.")

    if not current_user.is_authenticated:
        session['next'] = 'user.users_dashboard'
        flash('You must create an account first to apply.', 'warning')
        return redirect(url_for('auth.user_signup'))

    return redirect(url_for('user.users_dashboard'))



@user_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    job = JobPost.query.get_or_404(job_id)

    existing_application = Application.query.filter_by(user_id=current_user.id, job_id=job.id).first()
    if existing_application:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('user.users_dashboard'))

    if request.method == 'POST':
        # CSRF Token Validation
        token = request.form.get('csrf_token')
        try:
            validate_csrf(token)
        except ValidationError:
            abort(400, description="CSRF token is missing or invalid.")

        cv = request.files.get('cv')
        certificate = request.files.get('certificate')
        cover_letter = request.files.get('cover_letter')

        if not cv or not allowed_document(cv.filename):
            flash('CV must be a PDF, DOC, or DOCX file.', 'danger')
            return redirect(request.url)

        if not certificate or not allowed_document(certificate.filename):
            flash('Certificate must be a PDF, DOC, or DOCX file.', 'danger')
            return redirect(request.url)

        user_folder = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], f'user_{current_user.id}')
        os.makedirs(user_folder, exist_ok=True)

        cv_filename = f"{uuid.uuid4().hex}_{secure_filename(cv.filename)}"
        cv_path = os.path.join(user_folder, cv_filename)
        cv.save(cv_path)

        certificate_filename = f"{uuid.uuid4().hex}_{secure_filename(certificate.filename)}"
        certificate_path = os.path.join(user_folder, certificate_filename)
        certificate.save(certificate_path)

        cover_letter_filename = None
        cover_letter_path = None
        if cover_letter and cover_letter.filename != '':
            if not allowed_document(cover_letter.filename):
                flash('Cover letter must be a PDF, DOC, or DOCX file.', 'danger')
                return redirect(request.url)

            cover_letter_filename = f"{uuid.uuid4().hex}_{secure_filename(cover_letter.filename)}"
            cover_letter_path = os.path.join(user_folder, cover_letter_filename)
            cover_letter.save(cover_letter_path)

        new_application = Application(
            date_applied=datetime.now(),
            status='Under review',
            cv=f'user_{current_user.id}/{cv_filename}',
            certificate=f'user_{current_user.id}/{certificate_filename}',
            cover_letter=f'user_{current_user.id}/{cover_letter_filename}' if cover_letter_filename else None,
            user_id=current_user.id,
            job_id=job.id
        )
        db.session.add(new_application)
        db.session.commit()

        try:
            admin_msg = Message(
                subject=f"New Job Application for {job.title}",
                sender=os.getenv('MAIL_USERNAME'),
                recipients=[os.getenv('MAIL_USERNAME')],
                body=(
                    f"New application received from {current_user.username} ({current_user.email}) "
                    f"for the job: {job.title}.\n\nPlease find the attached documents."
                )
            )
            with current_app.open_resource(cv_path) as fp:
                admin_msg.attach(cv_filename, "application/octet-stream", fp.read())
            with current_app.open_resource(certificate_path) as fp:
                admin_msg.attach(certificate_filename, "application/octet-stream", fp.read())
            if cover_letter_path:
                with current_app.open_resource(cover_letter_path) as fp:
                    admin_msg.attach(cover_letter_filename, "application/octet-stream", fp.read())
            mail.send(admin_msg)
        except Exception as e:
            print("Admin email error:", e)

        try:
            user_msg = Message(
                subject="Application Received - Realmindx Education",
                sender=os.getenv('MAIL_USERNAME'),
                recipients=[current_user.email]
            )
            user_msg.body = f"""Dear {current_user.username},\n\nThank you for applying for the position: {job.title}.\n\nWe have received your application and our team will review it shortly.\nIf you are shortlisted, someone from our team will contact you soon.\n\nBest regards,\nRealmIndx Recruitment Team\n"""
            mail.send(user_msg)
            flash("Application submitted successfully.", "success")
        except Exception as e:
            print("User email error:", e)
            flash("Application submitted, but failed to send confirmation email.", "warning")

        return redirect(url_for('user.users_dashboard'))

    return render_template('apply.html', job=job)
