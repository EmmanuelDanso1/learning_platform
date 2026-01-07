from flask import Blueprint, render_template, redirect, url_for,jsonify, flash, send_from_directory, abort, request, current_app,session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
# using the imports from __init__.py file
from learning_app.realmind.models import Admin, Application, JobPost, News, Gallery, Newsletter, Product, Category, PromotionFlier, InfoDocument, ReceivedOrder, ReceivedOrderItem, ExternalSubscriber
from learning_app.realmind.forms import JobPostForm
from learning_app.extensions import db, mail
from flask_mail import Message
from flask_wtf.csrf import generate_csrf,validate_csrf, CSRFError
import os
import uuid
import json
from datetime import datetime
import requests
from learning_app.realmind.models.user import User
from learning_app.realmind.utils.email import send_order_status_email
from learning_app.realmind.utils.util import UPLOAD_FOLDER, allowed_profile_pic,allowed_image_file, allowed_document, allowed_file, FLIERS_FOLDER,generate_unsubscribe_token, verify_unsubscribe_token 
import logging
from learning_app.realmind.routes.newsletter_sync import sync_bookshop_subscribers

# upload files to the E_commerce
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def is_url(value):
    try:
        result = urlparse(value)
        return all([result.scheme, result.netloc])
    except:
        return False
    

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
    # Validate CSRF token
    token = request.form.get('csrf_token')
    try:
        validate_csrf(token)
    except ValidationError:
        abort(400, description="CSRF token is missing or invalid.")

    if 'profile_pic' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    file = request.files['profile_pic']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if file:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.root_path, 'realmind/static/uploads/', filename)
        file.save(upload_path)

        # Delete old picture if it exists
        if current_user.profile_pic:
            try:
                old_path = os.path.join(current_app.root_path, 'realmind/static/uploads/', current_user.profile_pic)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass

        current_user.profile_pic = filename
        db.session.commit()
        flash('Profile picture updated!', 'success')

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete_admin_profile_pic', methods=['POST'])
@login_required
def delete_admin_profile_pic():
    token = request.form.get('csrf_token')
    try:
        validate_csrf(token)
    except ValidationError:
        abort(400, description="CSRF token is missing or invalid.")

    if current_user.profile_pic:
        try:
            os.remove(os.path.join(current_app.root_path, 'realmind/static/uploads/', current_user.profile_pic))
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

        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"

        #Absolute rendering paths
        UPLOAD_FOLDER = os.path.join(
            "/var/www/learning_platform/learning_app/realmind/static/uploads/gallery"
         )
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        file_type = 'video' if filename.lower().endswith(('.mp4', '.mov', '.avi')) else 'image'

        new_item = Gallery(filename=filename, caption=caption, file_type=file_type)
        db.session.add(new_item)
        db.session.commit()

        flash('Gallery item uploaded successfully!', 'success')
        return redirect(url_for('admin.manage_gallery'))

    return render_template('admin/upload_gallery.html', csrf_token=generate_csrf())

# Edit Gallery Item
@admin_bp.route('/gallery/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_gallery(item_id):
    item = Gallery.query.get_or_404(item_id)

    if not isinstance(current_user, Admin):
        abort(403)

    #Absolute pathe for gallery edits   
    UPLOAD_FOLDER = "/var/www/learning_platform/learning_app/realmind/static/uploads/gallery"

    if request.method == 'POST':
        caption = request.form.get('caption')
        file = request.files.get('file')

        if caption:
            item.caption = caption

        if file and allowed_file(file.filename):
            old_path = os.path.join(UPLOAD_FOLDER, item.filename)
            if os.path.exists(old_path):
                os.remove(old_path)

            ext = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{ext}"

            # save filename
            new_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(new_path)

            item.filename = filename
            item.file_type = 'video' if filename.lower().endswith(('.mp4', '.mov', '.avi')) else 'image'

        db.session.commit()
        flash('Gallery item updated successfully.', 'success')
        return redirect(url_for('admin.manage_gallery'))

    return render_template('admin/edit_gallery.html', item=item, csrf_token=generate_csrf())

# Delete Gallery Item (CSRF token expected in form)
@admin_bp.route('/gallery/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_gallery(item_id):
    item = Gallery.query.get_or_404(item_id)

    # Absolute static path (same as upload & edit)
    UPLOAD_FOLDER = "/var/www/learning_platform/learning_app/realmind/static/uploads/gallery"
    file_path = os.path.join(UPLOAD_FOLDER, item.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(item)
    db.session.commit()
    flash('Gallery item deleted successfully.', 'success')
    return redirect(url_for('admin.manage_gallery'))

# Manage Gallery View (send CSRF token to template)
@admin_bp.route('/manage_gallery')
@login_required
def manage_gallery():
    if not isinstance(current_user, Admin):
        abort(403)

    gallery_items = Gallery.query.order_by(Gallery.date_posted.desc()).all()
    return render_template('admin/manage_gallery.html', gallery_items=gallery_items, csrf_token=generate_csrf())

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
            level=form.level.data,          
            subject=form.subject.data,
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

# manage jobs
@admin_bp.route('/admin/manage-jobs')
@login_required
def manage_jobs():
    if not isinstance(current_user, Admin):
        return redirect(url_for('user.users_dashboard'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    jobs_paginated = JobPost.query.filter_by(admin_id=current_user.id)\
                                  .order_by(JobPost.id.desc())\
                                  .paginate(page=page, per_page=per_page)

    return render_template(
        'admin/manage_jobs.html',
        jobs=jobs_paginated.items,
        current_page=page,
        total_pages=jobs_paginated.pages
    )

# edit jobs
@admin_bp.route('/admin/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('user.users_dashboard'))

    job = JobPost.query.get_or_404(job_id)
    if job.admin_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for('admin.manage_jobs'))

    form = JobPostForm(obj=job)

    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.requirements = form.requirements.data
        job.level=form.level.data,          
        job.subject=form.subject.data,
        db.session.commit()
        flash("Job updated successfully!", "success")
        return redirect(url_for('admin.manage_jobs'))

    return render_template('admin/edit_job.html', form=form, job=job)

# delete
@admin_bp.route('/admin/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    if not isinstance(current_user, Admin):
        return redirect(url_for('user.users_dashboard'))

    job = JobPost.query.get_or_404(job_id)
    if job.admin_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for('admin.manage_jobs'))

    db.session.delete(job)
    db.session.commit()
    flash("Job deleted successfully!", "success")
    return redirect(url_for('admin.manage_jobs'))


from flask_wtf.csrf import generate_csrf

# Post news route
@admin_bp.route('/admin/post-news', methods=['GET', 'POST'])
@login_required
def post_news():
    # Absolute path for production
    UPLOAD_FOLDER = "/var/www/learning_platform/learning_app/realmind/static/uploads/news"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')
        image_url = None

        if image and image.filename:
            filename = secure_filename(image.filename)
            # Generate a unique filename using UUID
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            path = os.path.join(UPLOAD_FOLDER, unique_filename)
            image.save(path)
            # Store relative path for templates
            image_url = f'uploads/news/{unique_filename}'

        news_item = News(title=title, content=content, image_url=image_url, admin_id=current_user.id)
        db.session.add(news_item)
        db.session.commit()
        flash('News posted successfully!', 'success')
        return redirect(url_for('admin.admin_news_dashboard'))

    return render_template('admin_post_news.html', csrf_token=generate_csrf())


# Edit news route
@admin_bp.route('/edit-news/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    news_item = News.query.get_or_404(news_id)
    if news_item.admin_id != current_user.id:
        abort(403)
    # Absolute path for production
    UPLOAD_FOLDER = "/var/www/learning_platform/learning_app/realmind/static/uploads/news"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    if request.method == 'POST':
        news_item.title = request.form['title']
        news_item.content = request.form['content']
        image = request.files.get('image')

        if image and image.filename:
            filename = secure_filename(image.filename)
            # Generate unique UUID 
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            path = os.path.join(UPLOAD_FOLDER, unique_filename)
            image.save(path)
            news_item.image_url = f'uploads/news/{unique_filename}'

        db.session.commit()
        flash('News updated successfully!', 'success')
        return redirect(url_for('admin.admin_news_dashboard'))

    return render_template('admin_post_news.html', news_item=news_item, editing=True, csrf_token=generate_csrf())

@admin_bp.route('/admin/delete-news/<int:news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    news_item = News.query.get_or_404(news_id)
    if news_item.admin_id != current_user.id:
        abort(403)

    # Absolute path for production
    UPLOAD_FOLDER = "/var/www/learning_platform/learning_app/realmind/static/uploads/news"

    # Delete associated image file if it exists
    if news_item.image_url:
        image_path = os.path.join("/var/www/learning_platform/learning_app/realmind/static", news_item.image_url)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(news_item)
    db.session.commit()
    flash('News deleted successfully.', 'success')
    return redirect(url_for('admin.admin_news_dashboard'))



# Admin News Dashboard with CSRF token sent to template
@admin_bp.route('/admin/news-dashboard')
@login_required
def admin_news_dashboard():
    if not isinstance(current_user, Admin):
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    news_list = News.query.filter_by(admin_id=current_user.id).order_by(News.created_at.desc()).all()
    return render_template('admin_news_dashboard.html', news_list=news_list, csrf_token=generate_csrf())

# product uploads
@admin_bp.route('/admin/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        logger.info("Admin add-product POST received")

        # --- Collect form data ---
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        image_file = request.files.get('image')
        category_name = request.form['category_name'].strip().title()
        in_stock = request.form.get('in_stock') in ['true', 'on', '1']

        logger.info(
            f"Product data: name={name}, price={price}, "
            f"in_stock={in_stock}, category={category_name}"
        )

        # Optional fields
        author = request.form.get('author')
        grade = request.form.get('grade')
        level = request.form.get('level')
        subject = request.form.get('subject')
        brand = request.form.get('brand')
        discount_percentage = request.form.get('discount_percentage')
        discount_percentage = float(discount_percentage) if discount_percentage else 0.0

        # --- Handle category ---
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()
            logger.info(f"Category created: {category_name}")
        else:
            logger.info(f"Category found: {category_name}")

        # --- Save image locally ---
        filename = None
        upload_path = None

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(
                current_app.root_path, 'realmind', 'static', 'uploads', filename
            )

            try:
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                image_file.save(upload_path)
                logger.info(f"Image saved locally: {upload_path}")
                logger.info(f"Image size: {os.path.getsize(upload_path)} bytes")
            except Exception as img_err:
                logger.exception(f"Failed to save local image: {img_err}")
        else:
            logger.warning("⚠ No valid image uploaded or file type not allowed")

        # --- Save product locally ---
        product = Product(
            name=name,
            description=description,
            price=price,
            in_stock=in_stock,
            image_filename=filename,
            admin_id=current_user.id,
            category_id=category.id,
            author=author,
            grade=grade,
            level=level,
            subject=subject,
            brand=brand,
            discount_percentage=discount_percentage
        )

        db.session.add(product)
        db.session.commit()
        logger.info(f"Product saved locally: id={product.id}")

        # --- Sync to e-commerce ---
        try:
            BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
            API_TOKEN = os.getenv('API_TOKEN')

            headers = {
                'Authorization': f'Bearer {API_TOKEN}'
            }

            product_data = {
                'name': name,
                'description': description,
                'price': price,
                'in_stock': in_stock,
                'category': category.name,
                'author': author,
                'grade': grade,
                'level': level,
                'subject': subject,
                'brand': brand,
                'discount_percentage': discount_percentage
            }

            files = {'data': (None, json.dumps(product_data))}
            if upload_path and os.path.exists(upload_path):
                files['image'] = open(upload_path, 'rb')
                logger.info("Sending image to Bookshop API")
            else:
                logger.warning(" No image file to send to Bookshop API")

            logger.info(f"Sending product to {BOOKSHOP_API}/products")

            res = requests.post(
                f"{BOOKSHOP_API}/products",
                files=files,
                headers=headers,
                timeout=15
            )

            logger.info(
                f"Bookshop response: status={res.status_code}, "
                f"body={res.text[:200]}"
            )

            if res.status_code == 201:
                data = res.json()
                product.ecommerce_product_id = data.get('id')
                product.bookshop_image_url = data.get('image_url')
                db.session.commit()
                logger.info(
                    f"Linked to Bookshop product: "
                    f"id={product.ecommerce_product_id}, "
                    f"image_url={product.bookshop_image_url}"
                )

        except Exception as e:
            logger.exception("Error syncing product with Bookshop")
            flash("Product added locally but failed to sync with Bookshop.", "warning")
        else:
            flash("Product added and synced with Bookshop!", "success")

        return redirect(url_for('admin.manage_products'))

    csrf_token = generate_csrf()
    return render_template('admin/add_product.html', csrf_token=csrf_token)


@admin_bp.route('/admin/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            current_app.logger.warning("Invalid CSRF on edit_product")
            abort(400, description="Invalid CSRF token")

        current_app.logger.info(f"Editing product ID {product.id}")

        # Basic fields
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.in_stock = request.form.get('in_stock') == 'true'

        # Metadata
        product.author = request.form.get('author')
        product.grade = request.form.get('grade')
        product.level = request.form.get('level')
        product.subject = request.form.get('subject')
        product.brand = request.form.get('brand')

        discount_raw = request.form.get('discount_percentage')
        product.discount_percentage = float(discount_raw) if discount_raw else 0.0

        # Category
        category_name = request.form.get('category_name', '').strip().title()
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
                db.session.commit()
            product.category_id = category.id

        # IMAGE
        image_file = request.files.get('image')
        upload_path = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(
                current_app.root_path, 'realmind', 'static', 'uploads', filename
            )
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image_file.save(upload_path)
            product.image_filename = filename

            current_app.logger.info(f"New image uploaded: {filename}")

        db.session.commit()

        # ---- SYNC TO BOOKSHOP ----
        if product.ecommerce_product_id:
            BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
            API_TOKEN = os.getenv("API_TOKEN")

            headers = {'Authorization': f'Bearer {API_TOKEN}'}

            product_data = {
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'in_stock': product.in_stock,
                'author': product.author,
                'grade': product.grade,
                'level': product.level,
                'subject': product.subject,
                'brand': product.brand,
                'discount_percentage': product.discount_percentage,
                'category': category_name
            }

            files = None
            if upload_path:
                files = {
                    'data': (None, json.dumps(product_data)),
                    'image': open(upload_path, 'rb')
                }
            else:
                files = {'data': (None, json.dumps(product_data))}

            try:
                res = requests.put(
                    f"{BOOKSHOP_API}/products/{product.ecommerce_product_id}",
                    files=files,
                    headers=headers,
                    timeout=15
                )

                current_app.logger.info(
                    f"Bookshop update response {res.status_code}: {res.text}"
                )

                if res.status_code == 200:
                    data = res.json()
                    product.bookshop_image_url = data.get('image_url')
                    db.session.commit()

            except Exception as e:
                current_app.logger.error(f"Sync update failed: {e}")

        flash("Product updated successfully.", "success")
        return redirect(url_for('admin.manage_products'))

    csrf_token = generate_csrf()
    return render_template('admin/edit_product.html', product=product, csrf_token=csrf_token)


@admin_bp.route('/admin/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except CSRFError:
        current_app.logger.warning("Invalid CSRF on delete_product")
        abort(400, description="Invalid CSRF token")

    product = Product.query.get_or_404(product_id)
    current_app.logger.info(f"Deleting product ID {product.id}")

    BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
    API_TOKEN = os.getenv("API_TOKEN")

    # ---- DELETE FROM BOOKSHOP ----
    if product.ecommerce_product_id:
        try:
            headers = {'Authorization': f'Bearer {API_TOKEN}'}
            res = requests.delete(
                f"{BOOKSHOP_API}/products/{product.ecommerce_product_id}",
                headers=headers,
                timeout=10
            )

            current_app.logger.info(
                f"Bookshop delete response {res.status_code}: {res.text}"
            )

            if res.status_code != 200:
                flash("Failed to delete product from Bookshop.", "danger")
                return redirect(url_for('admin.manage_products'))

        except Exception as e:
            current_app.logger.error(f"Bookshop delete error: {e}")
            flash("Error deleting product from Bookshop.", "danger")
            return redirect(url_for('admin.manage_products'))

    # ---- DELETE LOCAL IMAGE ----
    if product.image_filename:
        image_path = os.path.join(
            current_app.root_path, 'realmind', 'static', 'uploads', product.image_filename
        )
        if os.path.exists(image_path):
            os.remove(image_path)
            current_app.logger.info(f"Local image deleted: {image_path}")

    db.session.delete(product)
    db.session.commit()

    current_app.logger.info(f"Product {product.id} fully deleted")
    flash("Product deleted successfully.", "success")
    return redirect(url_for('admin.manage_products'))


# manage products
@admin_bp.route('/admin/manage-products')
@login_required
def manage_products():
    products = Product.query.order_by(Product.id.desc()).all()
    csrf_token = generate_csrf()
    return render_template('admin/manage_products.html', products=products, csrf_token=csrf_token)

# Serve uploaded profile pictures or files
@admin_bp.route('/admin/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'realmind/static/uploads/')
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


from flask_wtf.csrf import generate_csrf

@admin_bp.route('/upload_info', methods=['GET', 'POST'])
@login_required
def upload_info():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        source = request.form.get('source', '').strip()
        doc_file = request.files.get('file')
        image_file = request.files.get('image')

        if not title or not source or not doc_file:
            flash("Please fill out all required fields.", "warning")
            current_app.logger.warning("Upload failed: missing required fields")
            return redirect(url_for('admin.upload_info'))

        upload_dir = os.path.join(current_app.root_path, 'realmind', 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # ---- Save document locally ----
        doc_filename = secure_filename(doc_file.filename)
        doc_path = os.path.join(upload_dir, doc_filename)
        doc_file.save(doc_path)

        current_app.logger.info(f"Info file saved locally: {doc_path}")

        # ---- Save image locally (optional) ----
        image_filename = None
        image_path = None

        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(upload_dir, image_filename)
            image_file.save(image_path)

            current_app.logger.info(f"Info image saved locally: {image_path}")

        # ---- Save to DB ----
        new_doc = InfoDocument(
            title=title,
            source=source,
            filename=doc_filename,
            image=image_filename,
            admin_id=current_user.id
        )
        db.session.add(new_doc)
        db.session.commit()

        current_app.logger.info(
            f"🗄 InfoDocument created (ID={new_doc.id}) by admin {current_user.id}"
        )

        # ---- Sync to bookshop.realmindxgh.com ----
        BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
        API_TOKEN = os.getenv("API_TOKEN")

        data = {
            'title': title,
            'source': source,
            'uploaded_by': current_user.fullname
        }

        files = {
            'file': (doc_filename, open(doc_path, 'rb'), doc_file.mimetype)
        }

        if image_filename:
            files['image'] = (
                image_filename,
                open(image_path, 'rb'),
                image_file.mimetype
            )

        headers = {'Authorization': f'Bearer {API_TOKEN}'}

        try:
            current_app.logger.info("Syncing info document to Bookshop API")

            res = requests.post(
                f"{BOOKSHOP_API}/info",
                data=data,
                files=files,
                headers=headers,
                timeout=15
            )

            current_app.logger.info(
                f"Bookshop response: {res.status_code} - {res.text}"
            )

            if res.status_code == 201:
                ecommerce_id = res.json().get('id')
                new_doc.ecommerce_id = ecommerce_id
                db.session.commit()

                current_app.logger.info(
                    f"Info synced successfully (Bookshop ID={ecommerce_id})"
                )
                flash("Info document uploaded and synced successfully.", "success")
            else:
                flash("Failed to sync info document.", "danger")
                current_app.logger.error("Info sync failed")

        except Exception as e:
            current_app.logger.exception("Exception during info sync")
            flash("An error occurred during upload.", "danger")

        finally:
            # ---- Always close file handles ----
            files['file'][1].close()
            if 'image' in files:
                files['image'][1].close()

        return redirect(url_for('admin.upload_info'))

    return render_template(
        'admin/upload_info.html',
        csrf_token=generate_csrf()
    )


# edit and delete
@admin_bp.route('/admin/info/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_info(id):
    info = InfoDocument.query.get_or_404(id)

    if request.method == 'POST':
        # ---- CSRF validation ----
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            abort(400, description="Invalid CSRF token")

        info.title = request.form.get('title', '').strip()
        info.source = request.form.get('source', '').strip()

        file = request.files.get('file')
        image = request.files.get('image')

        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        file_path = None
        image_path = None

        # ---- File update ----
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            current_app.logger.info(f"Info file updated locally: {file_path}")
            info.filename = filename

        # ---- Image update ----
        if image and image.filename:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(upload_dir, image_filename)
            image.save(image_path)

            current_app.logger.info(f"🖼 Info image updated locally: {image_path}")
            info.image = image_filename

        db.session.commit()
        current_app.logger.info(f"InfoDocument updated (ID={info.id})")

        # ---- Sync update to Bookshop ----
        BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
        API_TOKEN = os.getenv("API_TOKEN")

        if info.ecommerce_id:
            payload = {
                'title': info.title,
                'source': info.source
            }

            files = {}
            try:
                if file_path:
                    files['file'] = (info.filename, open(file_path, 'rb'))
                if image_path:
                    files['image'] = (info.image, open(image_path, 'rb'))

                current_app.logger.info(
                    f"Syncing Info update to Bookshop (ID={info.ecommerce_id})"
                )

                res = requests.patch(
                    f"{BOOKSHOP_API}/info/{info.ecommerce_id}",
                    data=payload,
                    files=files if files else None,
                    headers={'Authorization': f'Bearer {API_TOKEN}'},
                    timeout=15
                )

                current_app.logger.info(
                    f"Bookshop update response: {res.status_code} - {res.text}"
                )

            except Exception:
                current_app.logger.exception("Failed to sync Info update to Bookshop")

            finally:
                for f in files.values():
                    f[1].close()

        flash("Info document updated successfully.", "success")
        return redirect(url_for('admin.manage_info'))

    return render_template(
        'admin/edit_info.html',
        info=info,
        csrf_token=generate_csrf()
    )

@admin_bp.route('/admin/info/<int:id>/delete', methods=['POST'])
@login_required
def delete_info(id):
    # ---- CSRF validation ----
    try:
        validate_csrf(request.form.get('csrf_token'))
    except CSRFError:
        abort(400, description="Invalid CSRF token")

    info = InfoDocument.query.get_or_404(id)

    upload_folder = current_app.config['UPLOAD_FOLDER']

    # ---- Delete local files ----
    try:
        if info.filename:
            file_path = os.path.join(upload_folder, info.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                current_app.logger.info(f"Local file deleted: {file_path}")

        if info.image:
            image_path = os.path.join(upload_folder, info.image)
            if os.path.exists(image_path):
                os.remove(image_path)
                current_app.logger.info(f"Local image deleted: {image_path}")

    except Exception:
        current_app.logger.exception("Failed to delete local info files")

    # ---- Sync delete to Bookshop ----
    BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
    API_TOKEN = os.getenv("API_TOKEN")

    if info.ecommerce_id:
        try:
            current_app.logger.info(
                f"Deleting Info from Bookshop (ID={info.ecommerce_id})"
            )

            res = requests.delete(
                f"{BOOKSHOP_API}/info/{info.ecommerce_id}",
                headers={'Authorization': f'Bearer {API_TOKEN}'},
                timeout=10
            )

            current_app.logger.info(
                f" Bookshop delete response: {res.status_code} - {res.text}"
            )

        except Exception:
            current_app.logger.exception("Failed to delete Info from Bookshop")

    db.session.delete(info)
    db.session.commit()

    current_app.logger.info(f"InfoDocument deleted locally (ID={id})")
    flash("Info document deleted successfully.", "success")

    return redirect(url_for('admin.manage_info'))

@admin_bp.route('/admin/info/manage')
@login_required
def manage_info():
    documents = InfoDocument.query.order_by(InfoDocument.upload_date.desc()).all()
    return render_template('admin/manage_info.html', documents=documents, csrf_token=generate_csrf())


# received orders
@admin_bp.route('/admin/received-orders')
@login_required
def received_orders():
    if not current_user.is_admin:
        abort(403)
    orders = ReceivedOrder.query.order_by(ReceivedOrder.date_received.desc()).all()
    return render_template('admin/received_orders.html', orders=orders)

# delete order
@admin_bp.route('/admin/delete-received-order/<int:order_id>', methods=['POST'])
@login_required
def delete_received_order(order_id):
    order = ReceivedOrder.query.get_or_404(order_id)

    try:
        db.session.delete(order)
        db.session.commit()
        flash(f"Order ID {order_id} deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the order: {e}", "danger")

    return redirect(url_for('admin.received_orders'))



# admin to post flyer
@admin_bp.route('/admin/post-flier', methods=['GET', 'POST'])
@login_required
def post_flier():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        image_file = request.files.get('image')

        if not image_file or not allowed_image_file(image_file.filename):
            current_app.logger.warning("Flier upload failed: invalid image")
            flash("Invalid or missing image file.", "danger")
            return redirect(url_for('admin.post_flier'))

        import uuid
        ext = os.path.splitext(image_file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"

        os.makedirs(FLIERS_FOLDER, exist_ok=True)
        save_path = os.path.join(FLIERS_FOLDER, filename)
        image_file.save(save_path)

        flier = PromotionFlier(title=title, image_filename=filename)
        db.session.add(flier)
        db.session.commit()

        current_app.logger.info(f"Flier created locally (id={flier.id}, title='{title}')")

        BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
        API_TOKEN = os.getenv("API_TOKEN")
        headers = {"Authorization": f"Bearer {API_TOKEN}"}

        try:
            with open(save_path, 'rb') as img:
                res = requests.post(
                    f"{BOOKSHOP_API}/fliers",
                    data={"title": title},
                    files={"image": img},
                    headers=headers,
                    timeout=10
                )

            if res.status_code == 201:
                flier.external_id = res.json().get("id")
                db.session.commit()
                current_app.logger.info(
                    f"Flier synced to bookshop (local_id={flier.id}, external_id={flier.external_id})"
                )
                flash("Flier posted and synced with e-commerce.", "success")
            else:
                current_app.logger.error(
                    f"Flier sync failed (local_id={flier.id}, status={res.status_code})"
                )
                flash("Flier saved locally, sync failed.", "warning")

        except Exception:
            current_app.logger.exception(
                f"Exception syncing flier (local_id={flier.id})"
            )
            flash("Flier saved locally. Sync failed.", "danger")

        return redirect(url_for('admin.post_flier'))

    return render_template('admin/post_flier.html', csrf_token=generate_csrf())


# update flier
from flask_wtf.csrf import generate_csrf, validate_csrf
from wtforms.validators import ValidationError

@admin_bp.route('/admin/update-flier/<int:flier_id>', methods=['GET', 'POST'])
@login_required
def update_flier(flier_id):
    flier = PromotionFlier.query.get_or_404(flier_id)

    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            current_app.logger.warning(f"Invalid CSRF on update (flier_id={flier_id})")
            abort(400, "Invalid CSRF token")

        new_title = request.form.get('title', '').strip()
        new_image = request.files.get('image')

        if new_title:
            flier.title = new_title

        image_path = None
        if new_image and allowed_image_file(new_image.filename):
            old_path = os.path.join(FLIERS_FOLDER, flier.image_filename)
            if os.path.exists(old_path):
                os.remove(old_path)

            import uuid
            ext = os.path.splitext(new_image.filename)[1]
            filename = f"{uuid.uuid4().hex}{ext}"
            image_path = os.path.join(FLIERS_FOLDER, filename)
            new_image.save(image_path)
            flier.image_filename = filename

        db.session.commit()
        current_app.logger.info(f"Flier updated locally (id={flier.id})")

        if flier.external_id:
            BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
            API_TOKEN = os.getenv("API_TOKEN")
            headers = {"Authorization": f"Bearer {API_TOKEN}"}

            try:
                if image_path:
                    with open(image_path, 'rb') as img:
                        res = requests.put(
                            f"{BOOKSHOP_API}/fliers/{flier.external_id}",
                            data={"title": flier.title},
                            files={"image": img},
                            headers=headers,
                            timeout=10
                        )
                else:
                    res = requests.put(
                        f"{BOOKSHOP_API}/fliers/{flier.external_id}",
                        data={"title": flier.title},
                        headers=headers,
                        timeout=10
                    )

                if res.status_code == 200:
                    current_app.logger.info(
                        f"Flier synced update (local_id={flier.id}, external_id={flier.external_id})"
                    )
                    flash("Flier updated and synced.", "success")
                else:
                    current_app.logger.error(
                        f"Flier update sync failed (local_id={flier.id}, status={res.status_code})"
                    )
                    flash("Flier updated locally, sync failed.", "warning")

            except Exception:
                current_app.logger.exception(
                    f"Exception updating flier (local_id={flier.id})"
                )
                flash("Flier updated locally. Sync failed.", "danger")

        return redirect(url_for('admin.manage_fliers'))

    return render_template('admin/update_flier.html', flier=flier, csrf_token=generate_csrf())

@admin_bp.route('/admin/delete-flier/<int:flier_id>', methods=['POST'])
@login_required
def delete_flier(flier_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        current_app.logger.warning(f"Invalid CSRF on delete (flier_id={flier_id})")
        abort(400, "Invalid CSRF token")

    flier = PromotionFlier.query.get_or_404(flier_id)
    image_path = os.path.join(FLIERS_FOLDER, flier.image_filename)
    external_id = flier.external_id

    db.session.delete(flier)
    db.session.commit()
    current_app.logger.info(f"Flier deleted locally (id={flier_id})")

    if os.path.exists(image_path):
        os.remove(image_path)

    if external_id:
        BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
        API_TOKEN = os.getenv("API_TOKEN")
        headers = {"Authorization": f"Bearer {API_TOKEN}"}

        try:
            res = requests.delete(
                f"{BOOKSHOP_API}/fliers/{external_id}",
                headers=headers,
                timeout=10
            )

            if res.status_code == 200:
                current_app.logger.info(
                    f"Flier deleted remotely (external_id={external_id})"
                )
                flash("Flier deleted from both platforms.", "success")
            else:
                current_app.logger.error(
                    f"Remote delete failed (external_id={external_id}, status={res.status_code})"
                )
                flash("Flier deleted locally, remote delete failed.", "warning")

        except Exception:
            current_app.logger.exception(
                f"Exception deleting flier (external_id={external_id})"
            )
            flash("Flier deleted locally. Sync failed.", "danger")

    return redirect(url_for('admin.manage_fliers'))

@admin_bp.route('/admin/manage-fliers')
@login_required
def manage_fliers():
    fliers = PromotionFlier.query.order_by(PromotionFlier.id.desc()).all()
    csrf_token = generate_csrf()
    return render_template('admin/manage_fliers.html', fliers=fliers, csrf_token=csrf_token)


def sync_bookshop_subscribers():
    """
    Fetch verified subscribers from Bookshop API and sync them to Learning Platform DB
    """
    BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
    API_TOKEN = os.getenv('API_TOKEN')
    
    if not BOOKSHOP_API or not API_TOKEN:
        current_app.logger.error("Missing BOOKSHOP_API_BASE_URL or API_TOKEN")
        return False
    
    try:
        # Fetch subscribers from Bookshop API
        res = requests.get(
            f"{BOOKSHOP_API}/newsletter-subscribers",
            headers={'Authorization': f'Bearer {API_TOKEN}'},
            timeout=10
        )
        
        if res.status_code != 200:
            current_app.logger.error(
                f"Failed to fetch subscribers: {res.status_code} - {res.text}"
            )
            return False
        
        data = res.json()
        bookshop_emails = set(data.get('subscribers', []))
        
        current_app.logger.info(
            f"Fetched {len(bookshop_emails)} subscribers from Bookshop"
        )
        
        # Get existing subscribers in Learning Platform
        existing_subscribers = ExternalSubscriber.query.filter_by(source='bookshop').all()
        existing_emails = {s.email for s in existing_subscribers}
        
        # Add new subscribers
        new_emails = bookshop_emails - existing_emails
        for email in new_emails:
            new_sub = ExternalSubscriber(
                email=email,
                source='bookshop'
            )
            db.session.add(new_sub)
        
        # Remove unsubscribed users (those no longer in Bookshop)
        removed_emails = existing_emails - bookshop_emails
        if removed_emails:
            ExternalSubscriber.query.filter(
                ExternalSubscriber.email.in_(removed_emails),
                ExternalSubscriber.source == 'bookshop'
            ).delete(synchronize_session=False)
        
        db.session.commit()
        
        current_app.logger.info(
            f"Sync complete: {len(new_emails)} added, {len(removed_emails)} removed"
        )
        
        return True
        
    except requests.RequestException as e:
        current_app.logger.exception(f"Error fetching from Bookshop API: {e}")
        return False
    except Exception as e:
        current_app.logger.exception(f"Error syncing subscribers: {e}")
        db.session.rollback()
        return False

# newsletter
# IMPROVED NEWSLETTER SENDING FUNCTION
@admin_bp.route('/admin/newsletter', methods=['GET', 'POST'])
@login_required
def create_newsletter():
    if request.method == 'POST':
        token = request.form.get('csrf_token')
        try:
            validate_csrf(token)
        except CSRFError:
            abort(400, description="Invalid CSRF token")

        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            flash("Title and content are required.", "danger")
            return redirect(url_for('admin.create_newsletter'))

        # Handle image upload
        image_filename = None
        file = request.files.get('newsletter_image')

        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Invalid image format. Please use PNG, JPG, or GIF.", "danger")
                return redirect(url_for('admin.create_newsletter'))

            # Create unique filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            image_filename = f"newsletter_{uuid.uuid4().hex}.{ext}"

            
            upload_path = os.path.join(
                current_app.root_path,
                'realmind/static/uploads/newsletters'  # Fixed path
            )
            os.makedirs(upload_path, exist_ok=True)
            
            # Save the file
            file.save(os.path.join(upload_path, image_filename))
            current_app.logger.info(f"Image saved: {image_filename}")

        # Save newsletter to database
        newsletter = Newsletter(
            title=title,
            content=content,
            image_filename=image_filename
        )
        db.session.add(newsletter)
        db.session.commit()

        current_app.logger.info(
            f"Newsletter created: {newsletter.title} (ID: {newsletter.id})"
        )

        # Get active subscribers
        subscribers = ExternalSubscriber.query.filter_by(
            source='bookshop',
            is_active=True
        ).all()

        if not subscribers:
            flash("Newsletter created but no active subscribers found.", "warning")
            return redirect(url_for('admin.list_newsletters'))

        # Send emails
        success_count = 0
        failed_count = 0

        for subscriber in subscribers:
            try:
                # Generate unsubscribe token
                unsubscribe_token = generate_unsubscribe_token(subscriber.email)
                unsubscribe_url = url_for(
                    'admin.unsubscribe',
                    token=unsubscribe_token,
                    _external=True
                )

                # Build image URL if exists
                image_url = None
                if image_filename:
                    image_url = url_for(
                        'static',
                        filename=f'uploads/newsletters/{image_filename}',
                        _external=True
                    )

                # Create email message
                msg = Message(
                    subject=title,
                    sender=current_app.config['MAIL_USERNAME'],
                    recipients=[subscriber.email]
                )

                # Render email template
                msg.html = render_template(
                    'emails/newsletter.html',
                    title=title,
                    content=content,
                    image_url=image_url,
                    unsubscribe_url=unsubscribe_url,
                    subscriber_email=subscriber.email
                )

                # Send email
                mail.send(msg)
                success_count += 1
                current_app.logger.info(f"Newsletter sent to: {subscriber.email}")

            except Exception as e:
                failed_count += 1
                current_app.logger.error(
                    f"Failed to send newsletter to {subscriber.email}: {str(e)}"
                )

        # Flash appropriate message
        if success_count > 0:
            flash(
                f"Newsletter sent successfully to {success_count} subscriber(s).",
                "success"
            )
        
        if failed_count > 0:
            flash(
                f"Failed to send to {failed_count} subscriber(s). Check logs.",
                "warning"
            )

        return redirect(url_for('admin.list_newsletters'))

    # GET request - show form
    subscriber_count = ExternalSubscriber.query.filter_by(
        source='bookshop',
        is_active=True
    ).count()

    return render_template(
        'admin/create_newsletter.html',
        csrf_token=generate_csrf(),
        subscriber_count=subscriber_count
    )

# UNSUBSCRIBE ROUTE
@admin_bp.route('/unsubscribe/<token>')
def unsubscribe(token):
    email = verify_unsubscribe_token(token)
    
    if not email:
        flash("Invalid or expired unsubscribe link.", "danger")
        return redirect(url_for('main.home'))
    
    # Deactivate subscriber
    subscriber = ExternalSubscriber.query.filter_by(email=email).first()
    
    if subscriber:
        subscriber.is_active = False
        db.session.commit()
        
        current_app.logger.info(f"User {email} unsubscribed from newsletter")
        
        return render_template('unsubscribe_success.html', email=email, csrf_token=generate_csrf())
    else:
        flash("Email not found in our system.", "warning")
        return redirect(url_for('main.home'))


# IMPROVED SYNC ROUTE WITH LOGGING
@admin_bp.route('/admin/sync-subscribers')
@login_required
def sync_subscribers():
    current_app.logger.info(f"Admin {current_user.email} initiated subscriber sync")
    success = sync_bookshop_subscribers()
    
    if success:
        flash("Subscribers synced successfully.", "success")
        current_app.logger.info("Subscriber sync completed successfully")
    else:
        flash("Failed to sync subscribers. Check logs for details.", "danger")
        current_app.logger.error("Subscriber sync failed")
    
    return redirect(url_for('admin.create_newsletter'))


# LIST NEWSLETTERS WITH LOGGING
@admin_bp.route('/admin/newsletters')
@login_required
def list_newsletters():
    current_app.logger.info(f"Admin {current_user.email} viewing newsletter list")
    newsletters = Newsletter.query.order_by(Newsletter.created_at.desc()).all()
    
    # Log for debugging
    current_app.logger.info(f"Found {len(newsletters)} newsletters")
    
    return render_template(
        'admin/view_newsletters.html',
        newsletters=newsletters,
        csrf_token=generate_csrf()
    )


# VIEW ALL SUBSCRIBERS (NEW ROUTE)
@admin_bp.route('/admin/subscribers')
@login_required
def view_subscribers():
    current_app.logger.info(f"Admin {current_user.email} viewing subscriber list")
    
    # Get all subscribers
    subscribers = ExternalSubscriber.query.order_by(
        ExternalSubscriber.created_at.desc()
    ).all()
    
    total_count = len(subscribers)
    
    current_app.logger.info(f"Displaying {total_count} subscribers to admin {current_user.email}")
    
    return render_template(
        'admin/view_subscribers.html',
        subscribers=subscribers,
        total_count=total_count
    )


# EXPORT SUBSCRIBERS AS CSV 
@admin_bp.route('/admin/subscribers/export')
@login_required
def export_subscribers():
    import csv
    from io import StringIO
    from flask import make_response
    
    current_app.logger.info(f"Admin {current_user.email} exporting subscribers as CSV")
    
    subscribers = ExternalSubscriber.query.order_by(
        ExternalSubscriber.created_at.desc()
    ).all()
    
    # Create CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Email', 'Source', 'Subscribed Date'])
    
    for sub in subscribers:
        writer.writerow([
            sub.email,
            sub.source,
            sub.added_on.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=newsletter_subscribers.csv"
    output.headers["Content-type"] = "text/csv"
    
    current_app.logger.info(f"CSV export completed: {len(subscribers)} subscribers")
    
    return output


# VIEW NEWSLETTER WITH LOGGING
@admin_bp.route('/admin/newsletter/<int:id>')
@login_required
def view_newsletter(id):
    newsletter = Newsletter.query.get_or_404(id)
    current_app.logger.info(
        f"Admin {current_user.email} viewing newsletter: {newsletter.title} (ID: {id})"
    )
    return render_template('admin/view_newsletter.html', newsletter=newsletter)


# EDIT NEWSLETTER WITH LOGGING
@admin_bp.route('/admin/newsletter/<int:newsletter_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_newsletter(newsletter_id):
    newsletter = Newsletter.query.get_or_404(newsletter_id)

    if request.method == 'POST':
        token = request.form.get('csrf_token')
        try:
            validate_csrf(token)
        except CSRFError:
            abort(400, description="Invalid CSRF token")

        newsletter.title = request.form.get('title')
        newsletter.content = request.form.get('content')

        if not newsletter.title or not newsletter.content:
            flash("Title and content are required.", "danger")
            return redirect(url_for('admin.edit_newsletter', newsletter_id=newsletter_id))

        # IMAGE UPDATE
        file = request.files.get('newsletter_image')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Invalid image format. Please use PNG, JPG, or GIF.", "danger")
                return redirect(url_for('admin.edit_newsletter', newsletter_id=newsletter_id))

            # Delete old image if exists
            if newsletter.image_filename:
                old_path = os.path.join(
                    current_app.root_path,
                    'realmind/static/uploads/newsletters',
                    newsletter.image_filename
                )
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                        current_app.logger.info(f"Deleted old image: {newsletter.image_filename}")
                    except Exception as e:
                        current_app.logger.error(f"Failed to delete old image: {e}")

            # Save new image
            ext = file.filename.rsplit('.', 1)[1].lower()
            new_filename = f"newsletter_{uuid.uuid4().hex}.{ext}"

            upload_path = os.path.join(
                current_app.root_path,
                'realmind/static/uploads/newsletters'  
            )
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, new_filename))

            newsletter.image_filename = new_filename
            current_app.logger.info(f"New image saved: {new_filename}")

        db.session.commit()
        
        current_app.logger.info(
            f"Newsletter '{newsletter.title}' updated by {current_user.email}"
        )
        
        flash("Newsletter updated successfully.", "success")
        return redirect(url_for('admin.list_newsletters'))

    return render_template(
        'admin/edit_newsletter.html',
        newsletter=newsletter,
        csrf_token=generate_csrf()
    )
@admin_bp.route('/admin/newsletter/<int:newsletter_id>/delete', methods=['POST'])
@login_required
def delete_newsletter(newsletter_id):
    token = request.form.get('csrf_token')

    try:
        validate_csrf(token)
    except CSRFError:
        abort(400, description="Invalid CSRF token")

    newsletter = Newsletter.query.get_or_404(newsletter_id)
    title = newsletter.title

    # DELETE IMAGE FILE
    if newsletter.image_filename:
        image_path = os.path.join(
            current_app.root_path,
            'realmind/static/uploads/newsletters',
            newsletter.image_filename
        )
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                current_app.logger.info(f"Deleted image: {newsletter.image_filename}")
            except Exception as e:
                current_app.logger.error(f"Failed to delete image: {e}")

    db.session.delete(newsletter)
    db.session.commit()

    current_app.logger.info(f"Newsletter '{title}' deleted by {current_user.email}")

    flash(f"Newsletter '{title}' deleted successfully.", "success")
    return redirect(url_for('admin.list_newsletters'))

# DELETE SUBSCRIBER
@admin_bp.route('/admin/subscriber/<int:id>/delete', methods=['POST'])
@login_required
def delete_subscriber(id):
    token = request.form.get('csrf_token')

    try:
        validate_csrf(token)
    except ValidationError:
        current_app.logger.warning(
            f"CSRF validation failed for admin {current_user.email} deleting subscriber {id}"
        )
        abort(400, description="CSRF token is missing or invalid.")

    subscriber = ExternalSubscriber.query.get_or_404(id)
    subscriber_email = subscriber.email
    
    db.session.delete(subscriber)
    db.session.commit()
    
    current_app.logger.info(
        f"Admin {current_user.email} deleted subscriber {id}: '{subscriber_email}'"
    )
    flash(f"Subscriber {subscriber_email} has been removed.", "success")
    return redirect(url_for('admin.view_subscribers'))


# send order status mail
def send_order_status_email(order, new_status):
    """
    Send HTML email notification to customer based on order status.
    Each status gets a beautifully formatted HTML email with order details.
    """
    try:
        # Define email subject for each status
        email_subjects = {
            'Received': f'Order Received - #{order.original_order_id}',
            'Processing': f'Your Order Is Being Packaged! - #{order.original_order_id}',
            'Shipped': f'Your Order Is On Its Way To You! - #{order.original_order_id}',
            'Delivered': f'Your Order Has Been Delivered! - #{order.original_order_id}'
        }
        
        # Check if status is valid
        if new_status not in email_subjects:
            current_app.logger.warning(f"Invalid status for email: {new_status}")
            return False
        
        # Prepare order items data
        items_list = []
        for item in order.items:
            items_list.append({
                'product_name': item.product_name,
                'product_id': item.id,  # or item.product_id if you have that field
                'quantity': item.quantity,
                'price': item.price
            })
        
        # Calculate totals
        subtotal = order.total_amount
        discount = 0.00  # Update this if you have discount logic
        total = order.total_amount
        
        # Get phone number (handle if it doesn't exist)
        phone = getattr(order, 'phone', 'N/A')
        
        # Format order date
        order_date = order.date_received.strftime('%B %d, %Y')
        
        # Render the HTML email template with all order data
        html_body = render_template(
            'emails/order_status_email.html',
            order_id=order.original_order_id,
            order_date=order_date,
            full_name=order.full_name,
            address=order.address,
            phone=phone,
            payment_method=order.payment_method,
            items=items_list,
            subtotal=subtotal,
            discount=discount,
            total=total,
            status=new_status
        )
        
        # Create email message
        msg = Message(
            subject=email_subjects[new_status],
            sender=('RealMindX Education Ltd', 'noreply@realmindxgh.com'),
            recipients=[order.email]
        )
        
        # Set HTML body
        msg.html = html_body
        
        # Send email
        mail.send(msg)
        
        current_app.logger.info(
            f"Email sent successfully to {order.email} for status: {new_status}"
        )
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


@admin_bp.route('/admin/update-received-order-status/<int:order_id>', methods=['POST'])
@login_required
def update_received_order_status(order_id):
    """Update status of received order from Bookshop and send email notification"""
    
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Missing status', 'success': False}), 400

        new_status = data['status']
        
        # Updated valid statuses - changed 'In Process' to 'Processing' and added 'Shipped'
        valid_statuses = ['Received', 'Processing', 'Shipped', 'Delivered']
        if new_status not in valid_statuses:
            return jsonify({
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                'success': False
            }), 400

        # Get order from admin dashboard
        order = ReceivedOrder.query.get_or_404(order_id)
        old_status = order.status
        order.status = new_status
        db.session.commit()
        
        current_app.logger.info(
            f"[Admin] Order {order.original_order_id} status updated: "
            f"{old_status} → {new_status} by {current_user.email}"
        )

        # Send HTML email notification to customer
        email_sent = send_order_status_email(order, new_status)
        
        if email_sent:
            current_app.logger.info(
                f"[Admin] Email notification sent to {order.email} for order {order.original_order_id}"
            )
        else:
            current_app.logger.warning(
                f"[Admin] Failed to send email notification for order {order.original_order_id}"
            )

        # Sync status to Bookshop
        try:
            api_base_url = os.getenv('ECOMMERCE_API_BASE_URL')  # bookshop URL
            api_token = os.getenv('API_TOKEN')
            
            if api_base_url and api_token:
                sync_response = requests.post(
                    f'{api_base_url}/api/orders/{order.original_order_id}/status',
                    json={'status': new_status},
                    headers={
                        'Authorization': f'Bearer {api_token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=5
                )
                
                if sync_response.status_code == 200:
                    current_app.logger.info(
                        f"[Admin] Status synced to Bookshop for order {order.original_order_id}"
                    )
                else:
                    current_app.logger.warning(
                        f"[Admin] Failed to sync status to Bookshop: {sync_response.status_code}"
                    )
        except Exception as sync_err:
            current_app.logger.error(
                f"[Admin] Error syncing status to Bookshop: {sync_err}"
            )

        return jsonify({
            'success': True, 
            'status': new_status,
            'email_sent': email_sent
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"[Admin] Error updating order status: {e}")
        return jsonify({'error': 'Internal server error', 'success': False}), 500

# View user profile
@admin_bp.route("/view-user/<int:user_id>")
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    applications = Application.query.filter_by(user_id=user_id).all()
    return render_template("admin/view_user.html", user=user, applications=applications)

# Bulk and single Email send
@admin_bp.route('/users')
@login_required
def list_users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template('admin/users_list.html', users=users)

# send individual message/email
@admin_bp.route('/message/<int:user_id>', methods=['GET', 'POST'])
@login_required
def send_message_single(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        subject = request.form['subject']
        body = request.form['body']

        # send email
        send_email(user.email, subject, body)

        flash('Message sent successfully', 'success')
        return redirect(url_for('admin.list_users'))

    return render_template('admin/message_single.html', user=user)

@admin_bp.route('/bulk_message', methods=['GET', 'POST'])
@login_required
def bulk_message():
    # Only admins can use this route
    if not isinstance(current_user, Admin):
        abort(403)

    # ------------------------------------------
    # Admin selected checkboxes in user list
    # ------------------------------------------
    selected_ids_json = request.form.get("selected_ids")

    if selected_ids_json:
        selected_ids = json.loads(selected_ids_json)

        if not selected_ids:
            flash("Please select at least one user.", "warning")
            return redirect(url_for('admin.list_users'))

        # Save selected user IDs in session so the next POST knows who to send to
        session['bulk_selected_users'] = selected_ids

        # Show the message writing form
        return render_template("admin/bulk_message.html")

    # ------------------------------------------
    # Admin typed message + submitted form
    # ------------------------------------------
    if request.method == 'POST':
        selected_ids = session.get('bulk_selected_users')

        if not selected_ids:
            flash("No users selected for bulk message.", "danger")
            return redirect(url_for('admin.list_users'))

        subject = request.form.get('subject')
        body = request.form.get('message')

        users = User.query.filter(User.id.in_(selected_ids)).all()

        if not users:
            flash("Selected users not found.", "danger")
            return redirect(url_for('admin.list_users'))

        # Send email
        for user in users:
            msg = Message(
                subject=subject,
                recipients=[user.email],
                body=body,
                sender="realmindxgh@gmail.com"
            )
            mail.send(msg)

        flash(f"Message sent to {len(users)} users!", "success")

        # Clear selections after sending
        session.pop('bulk_selected_users', None)

        return redirect(url_for('admin.list_users'))

    # GET request: Show empty page (if someone just visits /bulk_message)
    return render_template("admin/bulk_message.html")

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not isinstance(current_user, Admin):
        abort(403)

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash(f"User {user.fullname} has been deleted.", "success")
    return redirect(url_for('admin.list_users'))

# Activate and deactivate users
@admin_bp.route('/deactivate_user/<int:user_id>', methods=['POST'])
def deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    flash(f'{user.fullname} has been deactivated.', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/activate_user/<int:user_id>', methods=['POST'])
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash(f'{user.fullname} has been activated.', 'success')
    return redirect(url_for('admin.list_users'))

def send_order_status_email(order, new_status):
    """
    Send HTML email notification to customer based on order status.
    Each status gets a beautifully formatted HTML email with order details.
    """
    try:
        # Define email subject for each status
        email_subjects = {
            'Received': f'Order Received - #{order.original_order_id}',
            'Processing': f'Your Order Is Being Packaged! - #{order.original_order_id}',
            'Shipped': f'Your Order Is On Its Way To You! - #{order.original_order_id}',
            'Delivered': f'Your Order Has Been Delivered! - #{order.original_order_id}'
        }
        
        # Check if status is valid
        if new_status not in email_subjects:
            print(f"Invalid status: {new_status}")
            return False
        
        # Prepare order items data
        items_list = []
        for item in order.items:
            items_list.append({
                'product_name': item.product_name,
                'product_id': item.id,  # or item.product_id if you have that field
                'quantity': item.quantity,
                'price': item.price
            })
        
        # Calculate totals
        subtotal = order.total_amount
        discount = 0.00  # Update this if you have discount logic
        total = order.total_amount
        
        # Get phone number (handle if it doesn't exist)
        phone = getattr(order, 'phone', 'N/A')
        
        # Format order date
        order_date = order.date_received.strftime('%B %d, %Y')
        
        # Render the HTML email template with all order data
        html_body = render_template(
            'emails/order_status_email.html',
            order_id=order.original_order_id,
            order_date=order_date,
            full_name=order.full_name,
            address=order.address,
            phone=phone,
            payment_method=order.payment_method,
            items=items_list,
            subtotal=subtotal,
            discount=discount,
            total=total,
            status=new_status
        )
        
        # Create email message
        msg = Message(
            subject=email_subjects[new_status],
            sender=('RealMindX Education Ltd', 'noreply@realmindxgh.com'),
            recipients=[order.email]
        )
        
        # Set HTML body
        msg.html = html_body
        
        # Send email
        mail.send(msg)
        
        print(f"Email sent successfully to {order.email} for status: {new_status}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


