import os
import logging
from flask_wtf import CSRFProtect
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from learning_app.extensions import db,bcrypt,migrate,mail, login_manager
from flask_mail import Mail
from flask_migrate import Migrate
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
from learning_app.realmind.routes.oauth_routes import oauth_bp, init_oauth
from datetime import timedelta
from learning_app.extensions import limiter
from learning_app.realmind.utils.logging import setup_logging
from redis import Redis
# Load environment variables early
load_dotenv()

#  Load environment variables from the .env in this same folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Make sure a valid key exists
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    secret_key = "fallback_secret_key"  # optional: for dev use only
serializer = URLSafeTimedSerializer(secret_key)

# redis
redis_client = None

# csrf token
csrf = CSRFProtect()
def create_app():
    app = Flask(
        __name__,
        static_folder='realmind/static',
        template_folder='realmind/templates'
    )

    # SESSION CONFIGURATION
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

    # Load config
    app.config.from_object("learning_app.config.ProductionConfig")
    app.config.from_object('learning_app.config.Config')

    # Secrets
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

    # Mail
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    )

    # Uploads
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # SETUP LOGGING HERE
    setup_logging(app)
    app.logger.info("Application startup initiated")

    # Redis
    global redis_client
    redis_client = Redis(
        host=app.config["REDIS_HOST"],
        port=app.config["REDIS_PORT"],
        password=app.config["REDIS_PASSWORD"],
        decode_responses=True
    )
    app.logger.info("Redis client initialized")

    # CSRF
    csrf.init_app(app)

    # Rate limiting
    limiter.init_app(app)

    # Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.logger.info("Flask extensions initialized")

    # Models
    from learning_app.realmind.models.user import User
    from learning_app.realmind.models.admin import Admin

    @login_manager.user_loader
    def load_user(user_id):
        if isinstance(user_id, str):
            if user_id.startswith("admin:"):
                return Admin.query.get(int(user_id.split(":")[1]))
            elif user_id.startswith("user:"):
                return User.query.get(int(user_id.split(":")[1]))
        return None

    # Blueprints
    from learning_app.realmind.routes.main_routes import main_bp
    from learning_app.realmind.routes.auth_routes import auth_bp
    from learning_app.realmind.routes.admin_routes import admin_bp
    from learning_app.realmind.routes.jobs_routes import job_bp
    from learning_app.realmind.routes.donation_routes import donation_bp
    from learning_app.realmind.routes.user_routes import user_bp
    from learning_app.realmind.routes.receive_orders_api import api_bp

    # OAuth
    init_oauth(app)
    app.register_blueprint(oauth_bp, url_prefix="/oauth")

    app.register_blueprint(main_bp, name='main')
    app.register_blueprint(auth_bp, name='auth')
    app.register_blueprint(admin_bp, name='admin')
    app.register_blueprint(job_bp, name='jobs')
    app.register_blueprint(donation_bp, name='donation')
    app.register_blueprint(user_bp, name='user')
    app.register_blueprint(api_bp, name='api')

    # Exempt API from CSRF (server-to-server)
    csrf.exempt(api_bp)

    # Dev-only table creation
    with app.app_context():
        db.create_all()

    app.logger.info("Application startup complete")
    return app

