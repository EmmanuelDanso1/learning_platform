import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

def save_profile_picture(file, current_user):
    """Save a new profile picture and delete the old one."""
    if not file or file.filename == "":
        return None

    # Create unique filename
    ext = file.filename.rsplit(".", 1)[-1]
    filename = f"profile_{uuid.uuid4().hex}.{ext}"

    # Path: static/uploads/users/user_<id>/profile/
    upload_folder = os.path.join(
        current_app.root_path,
        'static/uploads/users',
        f"user_{current_user.id}",
        "profile"
    )
    os.makedirs(upload_folder, exist_ok=True)

    # Full path
    filepath = os.path.join(upload_folder, filename)

    # Save file
    file.save(filepath)

    # Delete old picture
    if current_user.profile_pic:
        try:
            old_path = os.path.join(upload_folder, current_user.profile_pic)
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting old picture: {e}")

    # Update user model
    current_user.profile_pic = filename
    return filename


def delete_profile_picture(current_user):
    """Deletes the existing profile picture."""
    if not current_user.profile_pic:
        return

    folder = os.path.join(
        current_app.root_path,
        'static/uploads/users',
        f"user_{current_user.id}",
        "profile"
    )
    filepath = os.path.join(folder, current_user.profile_pic)

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        current_app.logger.error(f"Error deleting picture: {e}")

    current_user.profile_pic = None
