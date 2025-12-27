import os
import redis
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:

    # Browser closes user is logout
    # users close browser
    SESSION_PERMANENT = False      # logout when browser closes
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # use True in production (HTTPS)
    SESSION_COOKIE_SAMESITE = "Lax"

    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    SESSION_COOKIE_NAME = "learning_platform_session"

    # profile uplaod path
    UPLOAD_FOLDER_USERS = os.path.join(BASE_DIR, "realmind", "static", "uploads", "users")

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "realmind", "static", "uploads")




    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    PAYSTACK_INITIALIZE_URL = 'https://api.paystack.co/transaction/initialize'
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')

class ProductionConfig(Config):
    """
    Production overrides for Redis or secure settings
    """
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") 