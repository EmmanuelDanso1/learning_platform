import os
from flask import current_app
from werkzeug.utils import secure_filename

def save_profile_picture(file, current_user):
    """
    Saves a new profile picture, deletes the old one if it exists,
    and returns the filename saved.
    """
    if not file:
        return None

    filename = secure_filename(file.filename)
    upload_folder = os.path.join(current_app.root_path, 'static/uploads')
    filepath = os.path.join(upload_folder, filename)

    # Create the upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)

    # Save the new file
    file.save(filepath)

    # Delete old profile pic if any
    if current_user.profile_pic:
        try:
            old_path = os.path.join(upload_folder, current_user.profile_pic)
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting old profile picture: {e}")

    # Update user/admin profile_pic attribute
    current_user.profile_pic = filename

    return filename

def delete_profile_picture(current_user):
    """
    Deletes the user's current profile picture if it exists.
    """
    if current_user.profile_pic:
        try:
            upload_folder = os.path.join(current_app.root_path, 'static/uploads')
            filepath = os.path.join(upload_folder, current_user.profile_pic)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            current_app.logger.error(f"Error deleting profile picture: {e}")

        current_user.profile_pic = None
