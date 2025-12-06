from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

#  Redis for rate limit storage (production-safe)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379" 
)

db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.user_login'
