import os
import uuid
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer

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
