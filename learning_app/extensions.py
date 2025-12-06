from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])


db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.user_login'