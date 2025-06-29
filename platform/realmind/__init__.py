import os
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
# Load environment variables early
load_dotenv()

# Global extensions (initialized here, linked to app later)
db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.user_login'

# Optional: serializer instance for password reset
serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))



def create_app():
    app = Flask(__name__)

    # Base config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max
    app.config.from_object('config.Config')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Models (User, Admin, etc.)
    from .models import User, Admin

    @login_manager.user_loader
    def load_user(user_id):
        if isinstance(user_id, str):
            if user_id.startswith("admin:"):
                return Admin.query.get(int(user_id.split(":")[1]))
            elif user_id.startswith("user:"):
                return User.query.get(int(user_id.split(":")[1]))
        return None


    # Blueprints
    from .routes.main_routes import main_bp
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    from .routes.jobs_routes import job_bp
    from .routes.donation_routes import donation_bp
    from .routes.user_routes import user_bp
    # recieve orders
    from .routes.receive_orders_api import api_bp

    app.register_blueprint(main_bp, name='main')
    app.register_blueprint(auth_bp, name='auth')
    app.register_blueprint(admin_bp, name='admin')
    app.register_blueprint(job_bp, name='jobs')
    app.register_blueprint(donation_bp, name='donation')
    app.register_blueprint(user_bp, name='user')
    app.register_blueprint(api_bp, name='api')

    # Create tables (optional, only for dev)
    with app.app_context():
        db.create_all()

    return app
