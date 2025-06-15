# util.py
import os

# File upload settings
UPLOAD_FOLDER = os.path.join('static', 'uploads')
PROFILE_PIC_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helpers
def allowed_profile_pic(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in PROFILE_PIC_EXTENSIONS

def allowed_document(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in DOCUMENT_EXTENSIONS
