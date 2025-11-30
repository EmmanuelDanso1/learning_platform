# realmind/routes/oauth_routes.py
import os
from flask import Blueprint, redirect, url_for, flash
from authlib.integrations.flask_client import OAuth
from flask_login import login_user
from learning_app.extensions import db
from learning_app.realmind.models.user import User

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
# GOOGLE LOGIN
# ===========================
@oauth_bp.route("/google/login")
def google_login():
    redirect_uri = url_for("oauth_bp.google_authorized", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)



@oauth_bp.route("/google/authorized")
def google_authorized():
    token = oauth.google.authorize_access_token()
    if not token:
        flash("Google login failed.", "danger")
        return redirect(url_for("auth.user_login"))

    user_info = oauth.google.get(
        "https://openidconnect.googleapis.com/v1/userinfo"
    ).json()

    email = user_info.get("email")
    fullname = user_info.get("name", email.split("@")[0])

    return handle_oauth_user(email, fullname)



# ===========================
# SHARED USER CREATION LOGIC
# ===========================
def handle_oauth_user(email, fullname):
    if not email:
        flash("Google did not return an email address.", "danger")
        return redirect(url_for("auth.user_login"))

    user = User.query.filter_by(email=email).first()

    # If user does NOT exist → create new Google user
    if not user:
        user = User(
            fullname=fullname,
            email=email,
            password=None,  # Google users do not use password
            auth_provider="google",
            is_verified=True,  # Google email is trusted
            otp_code=None,
            otp_expiry=None
        )

        db.session.add(user)
        db.session.commit()

    # If user exists but used local signup
    elif user.auth_provider == "local":
        flash("This email is already registered using normal signup.", "warning")
        return redirect(url_for("auth.user_login"))

    # Successful OAuth login
    login_user(user)
    flash(f"Welcome, {fullname}!", "success")
    return redirect(url_for("user.users_dashboard"))

