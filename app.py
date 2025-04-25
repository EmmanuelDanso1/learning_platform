
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from routes import app


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
