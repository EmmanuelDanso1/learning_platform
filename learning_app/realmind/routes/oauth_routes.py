import os
from flask import Blueprint, redirect, url_for, flash, session
from authlib.integrations.flask_client import OAuth
from flask_login import login_user
from learning_app.extensions import db
from learning_app.realmind.models.user import User
from learning_app.realmind.models.admin import Admin

oauth_bp = Blueprint("oauth_bp", __name__)

oauth = OAuth()


# ===========================
# Initialize OAuth Providers
# ===========================
def init_oauth(app):
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
        }
    )


# ===========================
# USER GOOGLE LOGIN
# ===========================
@oauth_bp.route("/google/login/user")
def google_login_user():
    """Initiate Google login for regular users"""
    session['oauth_type'] = 'user'  # Mark as user login
    redirect_uri = url_for("oauth_bp.google_authorized", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


# ===========================
# ADMIN GOOGLE LOGIN
# ===========================
@oauth_bp.route("/google/login/admin")
def google_login_admin():
    """Initiate Google login for admins"""
    session['oauth_type'] = 'admin'  # Mark as admin login
    redirect_uri = url_for("oauth_bp.google_authorized", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


# ===========================
# SHARED GOOGLE CALLBACK
# ===========================
@oauth_bp.route("/google/authorized")
def google_authorized():
    token = oauth.google.authorize_access_token()
    if not token:
        flash("Google login failed.", "danger")
        oauth_type = session.pop('oauth_type', 'user')
        return redirect(url_for(f"auth.{'admin' if oauth_type == 'admin' else 'user'}_login"))

    user_info = oauth.google.get(
        "https://openidconnect.googleapis.com/v1/userinfo"
    ).json()

    email = user_info.get("email")
    google_id = user_info.get("sub")
    given = user_info.get("given_name")
    family = user_info.get("family_name")
    name = user_info.get("name")

    # Construct the best possible full name
    if name:
        fullname = name
    else:
        fullname = " ".join(filter(None, [given, family]))

    # FINAL fallback
    if not fullname or fullname.strip() == "":
        fullname = email.split("@")[0]

    # Determine if this is admin or user login
    oauth_type = session.pop('oauth_type', 'user')
    
    if oauth_type == 'admin':
        return handle_oauth_admin(email, fullname, google_id)
    else:
        return handle_oauth_user(email, fullname, google_id)


# ===========================
# USER OAUTH HANDLER
# ===========================
def handle_oauth_user(email, fullname, google_id):
    if not email:
        flash("Google did not return an email address.", "danger")
        return redirect(url_for("auth.user_login"))

    user = User.query.filter_by(email=email).first()

    # If user does NOT exist → create new Google user
    if not user:
        user = User(
            fullname=fullname,
            email=email,
            password=None,
            auth_provider="google",
            google_id=google_id,
            is_verified=True,
            otp_code=None,
            otp_expiry=None
        )

        db.session.add(user)
        db.session.commit()

    # If user exists but used local signup
    elif user.auth_provider == "local":
        # Link Google account to existing local account
        if not user.google_id:
            user.google_id = google_id
            user.auth_provider = "google"
            db.session.commit()
            flash("Your account has been linked to Google!", "success")
        else:
            flash("This email is already registered. Please use password login.", "warning")
            return redirect(url_for("auth.user_login"))

    # Successful OAuth login
    login_user(user)
    flash(f"Welcome, {fullname}!", "success")
    return redirect(url_for("user.users_dashboard"))


# ===========================
# ADMIN OAUTH HANDLER
# ===========================
def handle_oauth_admin(email, fullname, google_id):
    if not email:
        flash("Google did not return an email address.", "danger")
        return redirect(url_for("auth.admin_login"))

    admin = Admin.query.filter_by(email=email).first()

    # If admin does NOT exist → create new Google admin
    if not admin:
        admin = Admin(
            fullname=fullname,
            email=email,
            password=None,
            auth_provider="google",
            google_id=google_id,
            is_verified=True,
            otp_code=None,
            otp_expiry=None
        )

        db.session.add(admin)
        db.session.commit()
        flash(f"Admin account created successfully! Welcome, {fullname}!", "success")

    # If admin exists but used local signup
    elif admin.auth_provider == "local":
        # Link Google account to existing local account
        if not admin.google_id:
            admin.google_id = google_id
            admin.auth_provider = "google"
            db.session.commit()
            flash("Your admin account has been linked to Google!", "success")
        else:
            flash("This email is already registered. Please use password login.", "warning")
            return redirect(url_for("auth.admin_login"))

    # Successful OAuth login
    login_user(admin)
    flash(f"Welcome Admin, {fullname}!", "success")
    return redirect(url_for("admin.admin_dashboard"))