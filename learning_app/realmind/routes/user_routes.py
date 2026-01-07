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
from learning_app.realmind.utils.util import allowed_document , allowed_profile_pic


user_bp = Blueprint('user', __name__)


@user_bp.route('/users/dashboard')
@login_required
def users_dashboard():

    # Redirect admins to admin dashboard
    if getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.admin_dashboard'))

    # -------- REQUIRED FIELDS --------
    required_fields = [
        current_user.firstname,
        current_user.surname,
        current_user.phone,
        current_user.ghana_card_number,
        current_user.preferred_subject,
        current_user.preferred_level,
        current_user.cv,
        current_user.certificate
    ]

    profile_complete = all(required_fields)

    # Fetch Jobs
    jobs = JobPost.query.order_by(JobPost.id.desc()).all()

    # Jobs applied for
    applied_jobs = [app.job_id for app in current_user.applications]

    return render_template(
        'users_dashboard.html',
        jobs=jobs,
        applied_jobs=applied_jobs,
        profile_complete=profile_complete
    )


@user_bp.route("/users/dashboard/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))

    # SUBJECT LIST
    subjects = [
        "Mathematics", "English", "Integrated Science", "Creative Arts",
        "Our World and Our People", "Ghanaian Language", "Computing",
        "Physical Education", "Religious and Moral Education",
        "Elective Mathematics", "Biology", "Physics", "Chemistry",
        "General Agriculture", "Animal Husbandry", "Crop Husbandry",
        "Fisheries", "Forestry", "Food and Nutrition", "Management in Living",
        "Textile Studies", "Visual Arts", "Graphic Design", "Sculpture",
        "Ceramics", "Picture Making", "General Knowledge in Art", "Music",
        "French", "Literature in English", "Government", "History",
        "Geography", "Economics", "Business Management", "Financial Accounting",
        "Cost Accounting", "Elective ICT", "Christian Religious Studies",
        "Islamic Religious Studies", "Arabic", "Tourism", "Auto Mechanics",
        "Welding and Fabrication", "Building Construction", "Technical Drawing",
        "Electrical Engineering Technology", "Plumbing", "Applied Electricity",
        "Electronics", "Woodwork", "Metalwork", "Printing Craft",
        "Spanish", "Sewing", "Pottery", "Other"
    ]

    # Helper to update only non-empty fields
    def update_if_not_empty(model, field, value):
        if value and value.strip():
            setattr(model, field, value.strip())

    if request.method == "POST":

        # BASIC PROFILE FIELDS (safe update)
        update_if_not_empty(current_user, "firstname", request.form.get("firstname"))
        update_if_not_empty(current_user, "surname", request.form.get("surname"))
        update_if_not_empty(current_user, "other_names", request.form.get("other_names"))
        update_if_not_empty(current_user, "phone", request.form.get("phone"))
        update_if_not_empty(current_user, "ghana_card_number", request.form.get("ghana_card_number"))

        # MULTIPLE LEVELS (always overwrite because it's a list)
        preferred_levels = request.form.getlist("preferred_level")
        current_user.preferred_level = ",".join(preferred_levels)

        # MULTIPLE SUBJECTS
        selected_subjects = request.form.getlist("preferred_subject")

        # If user typed "Other" subject
        other_subject = request.form.get("preferred_subject_other")
        if other_subject and other_subject.strip():
            selected_subjects = [s for s in selected_subjects if s != "Other"]
            selected_subjects.append(other_subject.strip())

        current_user.preferred_subject = ",".join(selected_subjects)

        # UPLOAD DIR
        base_upload = os.path.join(
            current_app.config["UPLOAD_FOLDER_USERS"],
            f"user_{current_user.id}", 
            "documents"
        )
        os.makedirs(base_upload, exist_ok=True)

        # ================================
        # CV UPLOAD
        # ================================
        cv_file = request.files.get("cv")
        if cv_file and cv_file.filename.strip():
            ext = cv_file.filename.rsplit(".", 1)[-1]
            filename = secure_filename(f"cv_{uuid.uuid4().hex}.{ext}")
            cv_path = os.path.join(base_upload, filename)
            cv_file.save(cv_path)

            # Delete old CV
            if current_user.cv:
                old_cv = os.path.join(base_upload, current_user.cv)
                if os.path.exists(old_cv):
                    try:
                        os.remove(old_cv)
                    except:
                        pass

            current_user.cv = filename

        # ================================
        # CERTIFICATE UPLOAD
        # ================================
        certificate_file = request.files.get("certificate")
        if certificate_file and certificate_file.filename.strip():
            ext = certificate_file.filename.rsplit(".", 1)[-1]
            filename = secure_filename(f"cert_{uuid.uuid4().hex}.{ext}")
            cert_path = os.path.join(base_upload, filename)
            certificate_file.save(cert_path)

            # Delete old certificate
            if current_user.certificate:
                old_cert = os.path.join(base_upload, current_user.certificate)
                if os.path.exists(old_cert):
                    try:
                        os.remove(old_cert)
                    except:
                        pass

            current_user.certificate = filename

        # ================================
        # PROFILE PICTURE UPLOAD
        # ================================
        pic = request.files.get("profile_pic")
        if pic and pic.filename.strip():
            ext = pic.filename.rsplit(".", 1)[-1]
            filename = secure_filename(f"profile_{uuid.uuid4().hex}.{ext}")

            upload_path = os.path.join(
                current_app.config["UPLOAD_FOLDER_USERS"],
                f"user_{current_user.id}",
                "profile"
            )
            os.makedirs(upload_path, exist_ok=True)

            file_path = os.path.join(upload_path, filename)
            pic.save(file_path)

            # Delete old picture
            if current_user.profile_pic:
                old_pic = os.path.join(upload_path, current_user.profile_pic)
                if os.path.exists(old_pic):
                    try:
                        os.remove(old_pic)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting old profile picture: {e}")

            current_user.profile_pic = filename

        db.session.commit()
        db.session.refresh(current_user)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("user.view_profile"))

    return render_template("edit_profile.html", subjects=subjects)



@user_bp.route("/dashboard/view-profile")
@login_required
def view_profile():
    applications = current_user.applications 
    return render_template("view_profile.html", applications=applications)

@user_bp.route("/dashboard/application-history")
@login_required
def application_history():
    applications = current_user.applications 
    return render_template("job_application_history.html", applications=applications)


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

    # Prevent duplicate applications
    existing_application = Application.query.filter_by(
        user_id=current_user.id,
        job_id=job.id
    ).first()

    if existing_application:
        flash("You have already applied for this job.", "warning")
        return redirect(url_for("user.users_dashboard"))

    if request.method == 'POST':
        # CSRF validation
        token = request.form.get("csrf_token")
        try:
            validate_csrf(token)
        except ValidationError:
            abort(400, description="Invalid CSRF token.")

        # Uploaded documents
        cv = request.files.get('cv')
        certificate = request.files.get('certificate')
        cover_letter = request.files.get('cover_letter')

        # Validation
        if not cv or not allowed_document(cv.filename):
            return redirect(request.url)

        if not certificate or not allowed_document(certificate.filename):
            return redirect(request.url)

        # --- Correct Upload Path ---
        upload_root = current_app.config['UPLOAD_FOLDER']  
        user_folder = os.path.join(upload_root, f"user_{current_user.id}")
        os.makedirs(user_folder, exist_ok=True)

        # Save CV
        cv_filename = f"{uuid.uuid4().hex}_{secure_filename(cv.filename)}"
        cv_path = os.path.join(user_folder, cv_filename)
        cv.save(cv_path)

        # Save Certificate
        certificate_filename = f"{uuid.uuid4().hex}_{secure_filename(certificate.filename)}"
        certificate_path = os.path.join(user_folder, certificate_filename)
        certificate.save(certificate_path)

        # Save Cover Letter (optional)
        cover_letter_filename = None
        cover_letter_path = None

        if cover_letter and cover_letter.filename.strip():
            if not allowed_document(cover_letter.filename):
                flash("Cover letter must be a PDF, DOC, or DOCX.", "danger")
                return redirect(request.url)

            cover_letter_filename = f"{uuid.uuid4().hex}_{secure_filename(cover_letter.filename)}"
            cover_letter_path = os.path.join(user_folder, cover_letter_filename)
            cover_letter.save(cover_letter_path)

        # Save application record
        new_app = Application(
            date_applied=datetime.now(),
            status='Under review',
            cv=f"user_{current_user.id}/{cv_filename}",
            certificate=f"user_{current_user.id}/{certificate_filename}",
            cover_letter=f"user_{current_user.id}/{cover_letter_filename}" if cover_letter_filename else None,
            user_id=current_user.id,
            job_id=job.id
        )

        db.session.add(new_app)
        db.session.commit()

        # Email Admin
        try:
            admin_msg = Message(
                subject=f"New Job Application - {job.title}",
                sender=os.getenv('MAIL_USERNAME'),
                recipients=[os.getenv('MAIL_USERNAME')],
                body=(
                    f"A new application was submitted.\n\n"
                    f"Applicant: {current_user.username} ({current_user.email})\n"
                    f"Job: {job.title}\n"
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

        # Email User
        try:
            user_msg = Message(
                subject="Your Job Application Has Been Received",
                sender=os.getenv('MAIL_USERNAME'),
                recipients=[current_user.email],
                body=(
                    f"Dear {current_user.username},\n\n"
                    f"We received your application for the position: {job.title}.\n"
                    f"Our team will review it shortly.\n\n"
                    f"RealmindX Recruitment Team"
                )
            )
            mail.send(user_msg)
            flash("Application submitted successfully.", "success")

        except Exception as e:
            print("User email error:", e)
            flash("Application submitted, but confirmation email failed.", "warning")

        return redirect(url_for("user.users_dashboard"))

    return render_template('apply.html', job=job)

# contacts for authenticated users
@user_bp.route('/dashboard/contact')
def contacts():
    return render_template("contacts.html", title="Contacts")


@user_bp.route('/dashboard/submit', methods=['POST'])
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

    return redirect(url_for('user.contacts'))

