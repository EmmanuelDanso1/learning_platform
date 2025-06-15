from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, abort, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
# using the imports from __init__.py file
from realmind.models import Admin, Application, JobPost, News
from realmind.forms import JobPostForm
from realmind import db
import os
from realmind.utils.util import UPLOAD_FOLDER, allowed_profile_pic, allowed_document
admin_bp = Blueprint('admin', __name__)

# admin dashbaord
@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        return redirect(url_for('main.users_dashboard'))
    jobs = JobPost.query.filter_by(admin_id=current_user.id).all()
    return render_template('admin_dashboard.html', admin=current_user, jobs=jobs)


# Profile picture upload
@admin_bp.route('/upload_admin_profile_pic', methods=['POST'])
@login_required
def upload_admin_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    file = request.files['profile_pic']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if file:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.root_path, 'static/uploads/', filename)
        file.save(upload_path)

        # Delete old picture if it exists
        if current_user.profile_pic:
            try:
                os.remove(os.path.join(current_app.root_path, 'static/uploads/', current_user.profile_pic))
            except Exception:
                pass

        current_user.profile_pic = filename
        db.session.commit()
        flash('Profile picture updated!', 'success')

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete_admin_profile_pic', methods=['POST'])
@login_required
def delete_admin_profile_pic():
    if current_user.profile_pic:
        try:
            os.remove(os.path.join(current_app.root_path, 'static/uploads/', current_user.profile_pic))
        except Exception:
            pass
        current_user.profile_pic = None
        db.session.commit()
        flash('Profile picture deleted.', 'info')

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('settings.html')


@admin_bp.route('/admin/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if not isinstance(current_user, Admin):
        return redirect(url_for('user.users_dashboard'))

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
        return redirect(url_for('admin.post_job'))

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


@admin_bp.route('/admin/post-news', methods=['GET', 'POST'])
@login_required
def post_news():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')
        image_url = None

        if image and image.filename:
            filename = secure_filename(image.filename)
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(path)
            image_url = f'uploads/{filename}'

        news_item = News(title=title, content=content, image_url=image_url, admin_id=current_user.id)
        db.session.add(news_item)
        db.session.commit()
        flash('News posted successfully!', 'success')
        return redirect(url_for('admin.admin_news_dashboard'))

    return render_template('admin_post_news.html')

# edit theses
@admin_bp.route('/edit-news/<int:news_id>', methods=['GET', 'POST'])
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
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(path)
            news_item.image_url = f'uploads/{filename}'

        db.session.commit()
        flash('News updated successfully!', 'success')
        return redirect(url_for('admin.news_dashboard'))

    return render_template('admin_post_news.html', news_item=news_item, editing=True)


# --- Delete News ---
@admin_bp.route('/admin/delete-news/<int:news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    news_item = News.query.get_or_404(news_id)
    if news_item.admin_id != current_user.id:
        abort(403)

    db.session.delete(news_item)
    db.session.commit()
    flash('News deleted successfully.', 'success')
    return redirect(url_for('admin.admin_news_dashboard'))

# --- News Dashboard ---
@admin_bp.route('/admin/news-dashboard')
@login_required
def admin_news_dashboard():
    if not isinstance(current_user, Admin):
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))  # home is under main_bp

    news_list = News.query.filter_by(admin_id=current_user.id).order_by(News.created_at.desc()).all()
    return render_template('admin_news_dashboard.html', news_list=news_list)

# Serve uploaded profile pictures or files
@admin_bp.route('/admin/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'static/uploads/')
    return send_from_directory(upload_folder, filename)


# View applicants for a job
@admin_bp.route('/admin/applicants/<int:job_id>')
@login_required
def view_applicants(job_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('user.users_dashboard'))

    job = JobPost.query.get(job_id)
    if not job or job.admin_id != current_user.id:
        return redirect(url_for('admin.admin_dashboard'))

    applications = job.applications
    return render_template('view_applicants.html', applications=applications)


# Accept an applicant
@admin_bp.route('/admin/accept/<int:application_id>')
@login_required
def accept_application(application_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('main.users_dashboard'))

    application = Application.query.get(application_id)
    if not application or application.job.admin_id != current_user.id:
        return redirect(url_for('admin.admin_dashboard'))

    application.status = 'accepted'
    db.session.commit()
    flash('Application accepted.', 'success')
    return redirect(url_for('admin.view_applicants', job_id=application.job_id))

# --- Edit Job Post ---
@admin_bp.route('/admin/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('main.users_dashboard'))

    job = JobPost.query.get_or_404(job_id)

    if job.admin_id != current_user.id:
        flash("You are not authorized to edit this job.", "danger")
        return redirect(url_for('admin.post_job'))

    form = JobPostForm(obj=job)

    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.requirements = form.requirements.data
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('admin.post_job'))

    return render_template('edit_job.html', form=form, job=job)

# --- Delete Job Post ---
@admin_bp.route('/admin/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('main.users_dashboard'))

    job = JobPost.query.get_or_404(job_id)

    if job.admin_id != current_user.id:
        flash("You are not authorized to delete this job.", "danger")
        return redirect(url_for('admin.post_job'))

    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('admin.post_job'))
