import os
import uuid
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def optimize_image(file_path, max_width=1200, quality=82):
    """
    Compress and resize an uploaded image in-place using Pillow.

    - Downsizes width to max_width (aspect ratio preserved) if larger.
    - JPEG/WEBP saved at `quality`; PNG saved with max compression.
    - Converts RGBA/P modes to RGB before saving as JPEG.
    - Silent on failure so it never breaks the upload flow.
    """
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            if img.width > max_width:
                ratio = max_width / img.width
                new_h = int(img.height * ratio)
                img = img.resize((max_width, new_h), Image.LANCZOS)

            ext = os.path.splitext(file_path)[1].lower()

            if ext in ('.jpg', '.jpeg'):
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.save(file_path, 'JPEG', quality=quality, optimize=True)

            elif ext == '.png':
                # Keep transparency; max lossless compression
                img.save(file_path, 'PNG', optimize=True, compress_level=7)

            elif ext == '.webp':
                img.save(file_path, 'WEBP', quality=quality, method=6)

            # GIF is skipped — may be animated

    except Exception as exc:
        # Log but never crash the upload
        try:
            current_app.logger.warning(f"Image optimisation skipped for {file_path}: {exc}")
        except RuntimeError:
            pass

# File upload settings
UPLOAD_FOLDER = "/var/www/learning_platform/learning_app/realmind/static/uploads/gallery"
PROFILE_PIC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

# utils.py or at the top of your gallery routes file
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}


os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FLIERS_FOLDER = os.path.join(BASE_DIR, "realmind", "static", "fliers")
upload_path = os.path.join(BASE_DIR, 'realmind', 'static', 'uploads', 'newsletters')
# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_profile_pic(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in PROFILE_PIC_EXTENSIONS

def allowed_document(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in DOCUMENT_EXTENSIONS


def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


# Newsletter

# Generate unsubscribe token
def generate_unsubscribe_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='unsubscribe-salt')

def verify_unsubscribe_token(token, max_age=86400*30):  # 30 days
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='unsubscribe-salt', max_age=max_age)
        return email
    except:
        return None
