import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'

    # Flask session cookie (avoid conflict with other apps)
    SESSION_COOKIE_NAME = "learning_platform_session"

    # Paystack config
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    PAYSTACK_INITIALIZE_URL = 'https://api.paystack.co/transaction/initialize'
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
