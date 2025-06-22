from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, abort, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
# using the imports from __init__.py file
from realmind.models import Admin, Application, JobPost, News, Gallery, Product
from realmind.forms import JobPostForm
from realmind import db
import os
import requests
from realmind.utils.util import UPLOAD_FOLDER, allowed_profile_pic, allowed_document, allowed_file
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

# gallery
@admin_bp.route('/upload_gallery', methods=['GET', 'POST'])
@login_required
def upload_gallery():
    if not isinstance(current_user, Admin):
        abort(403)

    if request.method == 'POST':
        file = request.files.get('file')
        caption = request.form.get('caption')

        if not file or not allowed_file(file.filename):
            flash('Invalid or missing file.', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'gallery')
        os.makedirs(upload_folder, exist_ok=True)  # Ensure the folder exists

        save_path = os.path.join(upload_folder, filename)
        file.save(save_path)

        file_type = 'video' if filename.lower().endswith(('.mp4', '.mov', '.avi')) else 'image'

        new_item = Gallery(filename=filename, caption=caption, file_type=file_type)
        db.session.add(new_item)
        db.session.commit()

        flash('Gallery item uploaded successfully!', 'success')
        return redirect(url_for('main.gallery'))

    return render_template('admin/upload_gallery.html')


@admin_bp.route('/gallery/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_gallery(item_id):
    item = Gallery.query.get_or_404(item_id)

    if not isinstance(current_user, Admin):
        abort(403)

    if request.method == 'POST':
        caption = request.form.get('caption')
        file = request.files.get('file')

        if caption:
            item.caption = caption

        if file and allowed_file(file.filename):
            # Delete old file
            old_path = os.path.join(current_app.root_path, 'static/uploads/gallery', item.filename)
            if os.path.exists(old_path):
                os.remove(old_path)

            # Save new file
            filename = secure_filename(file.filename)
            new_path = os.path.join(current_app.root_path, 'static/uploads/gallery', filename)
            file.save(new_path)

            item.filename = filename
            item.file_type = 'video' if filename.lower().endswith(('.mp4', '.mov', '.avi')) else 'image'

        db.session.commit()
        flash('Gallery item updated successfully.', 'success')
        return redirect(url_for('admin.manage_gallery'))  # Redirect to gallery dashboard

    return render_template('admin/edit_gallery.html', item=item)


@admin_bp.route('/gallery/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_gallery(item_id):
    item = Gallery.query.get_or_404(item_id)
    file_path = os.path.join(current_app.root_path, 'static/uploads/gallery', item.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(item)
    db.session.commit()
    flash('Gallery item deleted successfully.', 'success')
    return redirect(url_for('admin.manage_gallery'))


# manage admin
@admin_bp.route('/manage_gallery')
@login_required
def manage_gallery():
    if not isinstance(current_user, Admin):
        abort(403)

    gallery_items = Gallery.query.order_by(Gallery.date_posted.desc()).all()
    return render_template('admin/manage_gallery.html', gallery_items=gallery_items)

# post jobs
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
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists

            path = os.path.join(upload_dir, filename)
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
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists

            path = os.path.join(upload_dir, filename)
            image.save(path)
            news_item.image_url = f'uploads/{filename}'

        db.session.commit()
        flash('News updated successfully!', 'success')
        return redirect(url_for('admin.admin_news_dashboard'))

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

# product uploads
@admin_bp.route('/admin/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        image_file = request.files['image']
        in_stock = request.form.get('in_stock') == 'true'

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            image_file.save(upload_path)

            product = Product(
                name=name,
                description=description,
                price=price,
                in_stock=in_stock,
                image_filename=filename,
                admin_id=current_user.id
            )
            db.session.add(product)
            db.session.commit()  # Commit first to get product.id

            # Prepare sync data
            product_data = {
                'name': name,
                'description': description,
                'price': price,
                'in_stock': in_stock,
                'image_filename': filename
            }

            # Sync to E-Commerce API
            API_TOKEN = os.getenv('API_TOKEN')
            try:
                headers = {'Authorization': f'Bearer {API_TOKEN}'}
                res = requests.post(
                    "http://localhost:5001/api/products",
                    json=product_data,
                    headers=headers
                )
                print("E-commerce response:", res.status_code, res.json())
                if res.status_code == 201:
                    ecommerce_id = res.json().get('id')
                    if ecommerce_id:
                        product.ecommerce_product_id = ecommerce_id
                        db.session.commit()
            except Exception as e:
                print("Error syncing with e-commerce:", e)

            flash("Product added and synced!", "success")
            return redirect(url_for('admin.manage_products'))

    return render_template('admin/add_product.html')


# edit product
@admin_bp.route('/admin/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.in_stock = request.form.get('in_stock') == 'true'

        image_file = request.files.get('image')
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            image_file.save(upload_path)
            product.image_filename = filename

        db.session.commit()

        # Sync update to e-commerce
        API_TOKEN = os.getenv('API_TOKEN')
        ecommerce_id = product.ecommerce_product_id

        if ecommerce_id:
            product_data = {
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'in_stock': product.in_stock,
                'image_filename': product.image_filename
            }

            try:
                headers = {'Authorization': f'Bearer {API_TOKEN}'}
                res = requests.put(
                    f"http://localhost:5001/api/products/{ecommerce_id}",
                    json=product_data,
                    headers=headers
                )
                print("E-commerce sync update:", res.status_code, res.json())
            except Exception as e:
                print("Error syncing product update to e-commerce:", e)

        flash("Product updated successfully.", "success")
        return redirect(url_for('admin.manage_products'))

    return render_template('admin/edit_product.html', product=product)



# delete product
@admin_bp.route('/admin/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Delete local image
    try:
        image_path = os.path.join(current_app.root_path, 'static/uploads', product.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        print("Image deletion error:", e)

    # Get the e-commerce ID before deleting locally
    ecommerce_id = product.ecommerce_product_id

    # Delete locally
    db.session.delete(product)
    db.session.commit()

    # Sync deletion to E-Commerce
    if ecommerce_id:
        API_TOKEN = os.getenv('API_TOKEN')
        try:
            headers = {'Authorization': f'Bearer {API_TOKEN}'}
            res = requests.delete(
                f"http://localhost:5001/api/products/{ecommerce_id}",
                headers=headers
            )
            print("E-commerce delete response:", res.status_code, res.json())
        except Exception as e:
            print("Error deleting from e-commerce:", e)

    flash('Product deleted from both systems.', 'info')
    return redirect(url_for('admin.manage_products'))




# manage products
@admin_bp.route('/admin/manage-products')
@login_required
def manage_products():
    products = Product.query.order_by(Product.date_created.desc()).all()
    return render_template('admin/manage_products.html', products=products)

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
