from flask import Blueprint, render_template, redirect, url_for,jsonify, flash, send_from_directory, abort, request, current_app,session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
# using the imports from __init__.py file
from learning_app.realmind.models import Admin, Application, JobPost, News, Gallery, Newsletter, Product, Category, PromotionFlier, InfoDocument, ReceivedOrder, ReceivedOrderItem
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
from learning_app.realmind.utils.util import UPLOAD_FOLDER, allowed_profile_pic,allowed_image_file, allowed_document, allowed_file


# upload files to the E_commerce
from urllib.parse import urlparse

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


# --- Delete News ---
import os

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
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        image_file = request.files['image']
        category_name = request.form['category_name'].strip().title()
        in_stock = request.form.get('in_stock') == 'true'

        # New fields from form
        author = request.form.get('author')
        grade = request.form.get('grade')
        level = request.form.get('level')
        subject = request.form.get('subject')
        brand = request.form.get('brand')

        # Discount percentage (optional)
        discount_percentage = request.form.get('discount_percentage')
        discount_percentage = float(discount_percentage) if discount_percentage else 0.0

        # Create or find category
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()

        # Save image locally
        filename = None
        upload_path = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image_file.save(upload_path)

        # Save product locally
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

        # Sync to e-commerce
        API_TOKEN = os.getenv('API_TOKEN')
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

        BOOKSHOP_API = os.getenv("BOOKSHOP_API_BASE_URL")
        API_TOKEN = os.getenv("API_TOKEN")
        try:
            headers = {
                'Authorization': f'Bearer {API_TOKEN}',
                'X-CSRFToken': request.cookies.get('csrf_token', '')
            }

            files = {
                'data': (None, json.dumps(product_data)),
                'image': open(upload_path, 'rb')
            }

            res = requests.post(
                f"{os.getenv('BOOKSHOP_API')}/products",
                files=files,
                headers=headers
            )

            print("Bookshop sync response:", res.status_code, res.json())

            if res.status_code == 201:
                ecommerce_id = res.json().get('id')
                if ecommerce_id:
                    product.ecommerce_product_id = ecommerce_id
                    db.session.commit()
        except Exception as e:
            print("Error syncing with e-commerce:", e)

        flash("Product added and synced!", "success")
        return redirect(url_for('admin.manage_products'))

    csrf_token = generate_csrf()
    return render_template('admin/add_product.html', csrf_token=csrf_token)

@admin_bp.route('/admin/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except CSRFError:
            abort(400, description="Invalid CSRF token")

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

        # Discount
        discount_raw = request.form.get('discount_percentage')
        product.discount_percentage = float(discount_raw) if discount_raw else 0.0

        # Handle category
        category_name = request.form.get('category_name', '').strip().title()
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
                db.session.commit()
            product.category_id = category.id

        # Handle new image upload
        image_file = request.files.get('image')
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            image_file.save(upload_path)
            product.image_filename = filename

        db.session.commit()

        # Sync update to e-commerce
        ecommerce_id = product.ecommerce_product_id
        if ecommerce_id:
            product_data = {
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'in_stock': product.in_stock,
                'image_filename': product.image_filename,
                'author': product.author,
                'grade': product.grade,
                'level': product.level,
                'subject': product.subject,
                'brand': product.brand,
                'discount_percentage': product.discount_percentage,
                'category': category_name
            }

            try:
                API_TOKEN = os.getenv('API_TOKEN')
                headers = {'Authorization': f'Bearer {API_TOKEN}'}
                res = requests.put(
                    f"{os.getenv('API_BASE_URL')}/products/{ecommerce_id}",
                    json=product_data,
                    headers=headers
                )
                print("E-commerce sync update:", res.status_code, res.json())
            except Exception as e:
                print("Error syncing product update to e-commerce:", e)

        flash("Product updated successfully.", "success")
        return redirect(url_for('admin.manage_products'))

    # Generate CSRF token for GET request and send to template
    csrf_token = generate_csrf()
    return render_template('admin/edit_product.html', product=product, csrf_token=csrf_token)


@admin_bp.route('/admin/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except CSRFError:
        abort(400, description="Invalid CSRF token")

    product = Product.query.get_or_404(product_id)

    # Sync delete to E-commerce site via API
    ecommerce_id = product.ecommerce_product_id
    if ecommerce_id:
        try:
            API_TOKEN = os.getenv('API_TOKEN')
            headers = {'Authorization': f'Bearer {API_TOKEN}'}
            res = requests.delete(
                f"{os.getenv("API_BASE_URL")}products/{ecommerce_id}", 
                headers=headers,
                timeout=10
            )

            if res.status_code != 200:
                print("E-commerce deletion failed:", res.status_code, res.json())
                flash("E-commerce deletion failed. Product not deleted.", "danger")
                return redirect(url_for('admin.manage_products'))

        except Exception as e:
            print("Exception syncing delete to E-commerce:", e)
            flash("Error deleting product from E-commerce site.", "danger")
            return redirect(url_for('admin.manage_products'))

    # Delete image locally
    if product.image_filename:
        image_path = os.path.join(current_app.root_path, 'static/uploads', product.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete product locally
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully from both platforms.", "success")
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



from flask_wtf.csrf import generate_csrf

@admin_bp.route('/upload_info', methods=['GET', 'POST'])
@login_required
def upload_info():
    if request.method == 'POST':
        title = request.form['title'].strip()
        source = request.form['source'].strip()
        doc_file = request.files['file']
        image_file = request.files.get('image')

        if not title or not source or not doc_file:
            flash("Please fill out all required fields.", "warning")
            return redirect(url_for('admin.upload_info'))

        # Save locally
        upload_dir = os.path.join(current_app.root_path, 'static/uploads')
        os.makedirs(upload_dir, exist_ok=True)

        doc_filename = secure_filename(doc_file.filename)
        doc_path = os.path.join(upload_dir, doc_filename)
        doc_file.save(doc_path)

        image_filename = None
        image_path = None
        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(upload_dir, image_filename)
            image_file.save(image_path)

        # Save to DB
        new_doc = InfoDocument(
            title=title,
            source=source,
            filename=doc_filename,
            image=image_filename,
            admin_id=current_user.id
        )
        db.session.add(new_doc)
        db.session.commit()

        # Sync to e-commerce
        data = {
            'title': title,
            'source': source,
            'uploaded_by': current_user.username
        }

        files = {
            'file': (doc_file.filename, open(doc_path, 'rb'), doc_file.mimetype)
        }
        if image_file and image_filename:
            files['image'] = (image_file.filename, open(image_path, 'rb'), image_file.mimetype)

        headers = {
            'Authorization': f'Bearer {os.getenv("API_TOKEN")}'
        }

        try:
            res = requests.post(
                f'{os.getenv('API_BASE_URL')}/info',
                data=data,
                files=files,
                headers=headers
            )
            if res.status_code == 201:
                ecommerce_id = res.json().get('id')
                new_doc.ecommerce_id = ecommerce_id
                db.session.commit()
                flash("Info document uploaded and synced to e-commerce site.", "success")
            else:
                flash(f"Failed to sync: {res.status_code} - {res.text}", "danger")
        except Exception as e:
            print("Upload error:", e)
            flash("An error occurred during upload.", "danger")
        finally:
            files['file'][1].close()
            if 'image' in files:
                files['image'][1].close()

        return redirect(url_for('admin.upload_info'))

    # GET method
    return render_template('admin/upload_info.html', csrf_token=generate_csrf())


# edit and delete
@admin_bp.route('/admin/info/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_info(id):
    info = InfoDocument.query.get_or_404(id)

    if request.method == 'POST':
        # Validate CSRF token
        csrf_token = request.form.get('csrf_token')
        if not csrf_token or csrf_token != generate_csrf():
            abort(400, description="CSRF token is missing or invalid.")

        info.title = request.form['title']
        info.source = request.form['source']

        file = request.files.get('file')
        image = request.files.get('image')

        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        file_path = None
        image_path = None

        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            info.filename = filename

        if image and image.filename and allowed_image_file(image.filename):
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(upload_dir, image_filename)
            image.save(image_path)
            info.image = image_filename

        db.session.commit()
        flash("Info document updated successfully.", "success")

        # Sync with e-commerce platform
        try:
            if info.ecommerce_id:
                ecommerce_base_url = os.getenv('ECOMMERCE_API_BASE_URL')
                api_token = os.getenv('API_TOKEN')

                payload = {
                    'title': info.title,
                    'source': info.source
                }
                files = {}
                if file_path:
                    files['file'] = (file.filename, open(file_path, 'rb'), file.mimetype)
                if image_path:
                    files['image'] = (image.filename, open(image_path, 'rb'), image.mimetype)

                response = requests.patch(
                    f"{os.getenv('API_BASE_URL')}/info/{info.ecommerce_id}",
                    data=payload,
                    files=files,
                    headers={'Authorization': f'Bearer {api_token}'}
                )

                if response.status_code != 200:
                    print("E-commerce update sync failed:", response.text)
                else:
                    print("E-commerce update sync successful.")
        except Exception as e:
            print("E-commerce sync error:", e)
        finally:
            if file_path:
                files['file'][1].close()
            if image_path:
                files['image'][1].close()

        return redirect(url_for('admin.manage_info'))

    return render_template('admin/edit_info.html', info=info, csrf_token=generate_csrf())


@admin_bp.route('/admin/info/<int:id>/delete', methods=['POST'])
@login_required
def delete_info(id):
    # Proper CSRF validation
    token = request.form.get('csrf_token')
    try:
        validate_csrf(token)
    except CSRFError:
        abort(400, description="CSRF token is missing or invalid.")

    info = InfoDocument.query.get_or_404(id)

    # Delete files if they exist
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if info.filename:
            file_path = os.path.join(upload_folder, info.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        if info.image:
            image_path = os.path.join(upload_folder, info.image)
            if os.path.exists(image_path):
                os.remove(image_path)
    except Exception as e:
        print("File deletion failed:", e)

    db.session.delete(info)
    db.session.commit()
    flash("Info document deleted.", "success")

    # Sync deletion to e-commerce
    try:
        if info.ecommerce_id:
            
            api_token = os.getenv('API_TOKEN')

            delete_url = f"{os.getenv('API_BASE_URL')}/info/{info.ecommerce_id}"
            headers = {'Authorization': f'Bearer {api_token}'}

            response = requests.delete(delete_url, headers=headers)

            if response.status_code != 200:
                print(f"E-commerce delete sync failed: {response.status_code}")
                print("Response content:", response.text)
            else:
                print("E-commerce delete sync successful.")
        else:
            print("No ecommerce_id set. Skipping delete sync.")
    except Exception as e:
        print("E-commerce sync error:", e)

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

        if image_file and allowed_image_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(current_app.root_path, 'static', 'fliers', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            image_file.save(save_path)

            new_flier = PromotionFlier(title=title, image_filename=filename)
            db.session.add(new_flier)
            db.session.commit()

            API_TOKEN = os.getenv('API_TOKEN')
            headers = {'Authorization': f'Bearer {API_TOKEN}'}
            data = {'title': title}
            files = {'image': open(save_path, 'rb')}

            try:
                res = requests.post(
                    f'{os.getenv('API_BASE_URL')}/fliers',
                    data=data,
                    files=files,
                    headers=headers
                )
                if res.status_code == 201:
                    flash("Flier posted and sent to e-commerce!", "success")
                else:
                    flash("Flier posted locally, but failed to sync.", "warning")
            except Exception as e:
                print("Error posting flier to e-commerce:", e)
                flash("Flier posted locally. Failed to send to e-commerce.", "danger")
            finally:
                files['image'].close()
        else:
            flash("Invalid or missing image file.", "danger")

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
            abort(400, description="Invalid CSRF token.")

        new_title = request.form.get('title', '').strip()
        new_image = request.files.get('image')

        if new_title:
            flier.title = new_title

        # Save new image if uploaded
        if new_image and allowed_image_file(new_image.filename):
            filename = secure_filename(new_image.filename)
            path = os.path.join(current_app.root_path, 'static', 'fliers', filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            new_image.save(path)
            flier.image_filename = filename

        db.session.commit()

        # Sync with e-commerce
        try:
            API_TOKEN = os.getenv('API_TOKEN')
            headers = {'Authorization': f'Bearer {API_TOKEN}'}
            data = {'title': flier.title}
            files = {}

            if new_image:
                files['image'] = open(path, 'rb')

            res = requests.put(
                f"{os.getenv('API_BASE_URL')}/fliers/{flier.id}",
                data=data,
                files=files,
                headers=headers
            )

            if files:
                files['image'].close()

            if res.status_code == 200:
                flash("Flier updated and synced with e-commerce.", "success")
            else:
                flash("Flier updated locally, but failed to sync with e-commerce.", "warning")

        except Exception as e:
            print("Error updating flier on e-commerce:", e)
            flash("Flier updated locally. Failed to sync.", "danger")

        return redirect(url_for('admin.post_flier'))

    return render_template('admin/update_flier.html', flier=flier, csrf_token=generate_csrf())

@admin_bp.route('/admin/delete-flier/<int:flier_id>', methods=['POST'])
@login_required
def delete_flier(flier_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(400, description="Invalid CSRF token.")

    flier = PromotionFlier.query.get_or_404(flier_id)
    image_path = os.path.join(current_app.root_path, 'static', 'fliers', flier.image_filename)

    db.session.delete(flier)
    db.session.commit()

    if os.path.exists(image_path):
        os.remove(image_path)

    try:
        API_TOKEN = os.getenv('API_TOKEN')
        headers = {'Authorization': f'Bearer {API_TOKEN}'}
        res = requests.delete(f"{os.getenv('API_BASE_URL')}/fliers/{flier.id}", headers=headers)

        if res.status_code == 200:
            flash("Flier deleted from both platforms.", "success")
        else:
            flash("Flier deleted locally, but not on e-commerce.", "warning")
    except Exception as e:
        print("Error deleting flier from e-commerce:", e)
        flash("Flier deleted locally. Failed to delete from e-commerce.", "danger")

    return redirect(url_for('admin.manage_fliers'))


@admin_bp.route('/admin/manage-fliers')
@login_required
def manage_fliers():
    fliers = PromotionFlier.query.order_by(PromotionFlier.id.desc()).all()
    csrf_token = generate_csrf()
    return render_template('admin/manage_fliers.html', fliers=fliers, csrf_token=csrf_token)


# Newsletter
@admin_bp.route('/admin/newsletter', methods=['GET', 'POST'])
@login_required
def create_newsletter():
    if request.method == 'POST':
        token = request.form.get('csrf_token')
        try:
            validate_csrf(token)
        except CSRFError:
            abort(400, description="CSRF token is missing or invalid.")

        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            flash("Title and content are required.", "danger")
            return redirect(url_for('admin.create_newsletter'))

        # Save to DB
        newsletter = Newsletter(title=title, content=content)
        db.session.add(newsletter)
        db.session.commit()

        # Fetch subscribers from API
        API_TOKEN = os.getenv('API_TOKEN')
        try:
            res = requests.get(
                f"{os.getenv('API_BASE_URL')}/newsletter-subscribers",
                headers={'Authorization': f'Bearer {API_TOKEN}'}
            )
            subscribers = res.json().get('subscribers', [])

            for email in subscribers:
                msg = Message(
                    subject=title,
                    recipients=[email],
                    html=content
                )
                mail.send(msg)

            flash("Newsletter sent to subscribers.", "success")
        except Exception as e:
            print("Error sending newsletter:", e)
            flash("Failed to send newsletter to subscribers.", "danger")

        return redirect(url_for('admin.list_newsletters'))

    # For GET request
    return render_template('admin/create_newsletter.html', csrf_token=generate_csrf())

# list newsletter
@admin_bp.route('/admin/newsletters')
@login_required
def list_newsletters():
    newsletters = Newsletter.query.order_by(Newsletter.created_on.desc()).all()
    return render_template('admin/list_newsletters.html', newsletters=newsletters)

# --- View Newsletter ---
@admin_bp.route('/admin/newsletter/<int:id>')
@login_required
def view_newsletter(id):
    newsletter = Newsletter.query.get_or_404(id)
    return render_template('admin/view_newsletter.html', newsletter=newsletter)

# --- Edit Newsletter ---
@admin_bp.route('/admin/newsletter/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_newsletter(id):
    newsletter = Newsletter.query.get_or_404(id)

    if request.method == 'POST':
        token = request.form.get('csrf_token')
        try:
            validate_csrf(token)
        except CSRFError:
            abort(400, description="CSRF token is missing or invalid.")

        newsletter.title = request.form.get('title')
        newsletter.content = request.form.get('content')

        if not newsletter.title or not newsletter.content:
            flash("Title and content are required.", "danger")
            return redirect(url_for('admin.edit_newsletter', id=id))

        db.session.commit()
        flash("Newsletter updated successfully.", "success")
        return redirect(url_for('admin.view_newsletter', id=id))

    return render_template('admin/edit_newsletter.html', newsletter=newsletter, csrf_token=generate_csrf())

# --- Delete Newsletter ---
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError

@admin_bp.route('/admin/newsletter/<int:id>/delete', methods=['POST'])
@login_required
def delete_newsletter(id):
    token = request.form.get('csrf_token')

    try:
        validate_csrf(token)
    except ValidationError:
        abort(400, description="CSRF token is missing or invalid.")

    newsletter = Newsletter.query.get_or_404(id)
    db.session.delete(newsletter)
    db.session.commit()
    flash("Newsletter deleted successfully.", "success")
    return redirect(url_for('admin.list_newsletters'))


# send order status mail
@admin_bp.route('/update-received-order-status/<int:order_id>', methods=['POST'])
@login_required
def update_received_order_status(order_id):
    order = ReceivedOrder.query.get_or_404(order_id)
    new_status = request.form.get('status')

    if new_status not in ['Received', 'In Process', 'Delivered']:
        return jsonify({'error': 'Invalid status'}), 400

    # Update local DB
    order.status = new_status
    db.session.commit()

    # Send email to user if delivered
    if new_status == 'Delivered':
        try:
            send_order_status_email(
                to=order.email,
                full_name=order.full_name,
                order_id=order.original_order_id,
                status=new_status,
                order_date=datetime.now().strftime('%d %B %Y %I:%M%p').lower()
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send delivery email: {e}")

    # Send API update to e-commerce
    api_url = f"{os.getenv('API_BASE_URL')}/orders/{order.original_order_id}/status"
    token = os.getenv('API_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'status': new_status}

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code != 200:
            current_app.logger.error(f"API update failed: {response.text}")
            return jsonify({'error': 'API sync failed'}), 500
    except Exception as e:
        current_app.logger.error(f"API request error: {e}")
        return jsonify({'error': 'API request error'}), 500

    return jsonify({'success': True, 'status': new_status})

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
