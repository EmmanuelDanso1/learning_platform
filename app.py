from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# app.config['SECRET_KEY'] = 'your_secret_key'
# db = SQLAlchemy(app)
# bcrypt = Bcrypt(app)
# login_manager = LoginManager(app)
# login_manager.login_view = 'user_login'

# class User(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(20), unique=True, nullable=False)
#     password = db.Column(db.String(60), nullable=False)
#     role = db.Column(db.String(10), nullable=False, default='user')  # 'user' or 'admin'

# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))
@app.route("/")
def home():
    return render_template("home.html",  title="Home")

# about route
@app.route("/about")
def about():
    return render_template("about.html", title="About")

# services route
@app.route("/services")
def services():
    return render_template("services.html", title="Services")

@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")

@app.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    # if request.method == 'POST':
    #     username = request.form['username']
    #     password = request.form['password']
    #     hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    #     new_user = User(username=username, password=hashed_password, role='user')
    #     db.session.add(new_user)
    #     db.session.commit()
    #     flash('User account created successfully! Please log in.', 'success')
    #     return redirect(url_for('user_login'))
    return render_template('user_signup.html')

# @app.route('/admin_register', methods=['GET', 'POST'])
# def admin_register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
#         new_admin = User(username=username, password=hashed_password, role='admin')
#         db.session.add(new_admin)
#         db.session.commit()
#         flash('Admin account created successfully! Please log in.', 'success')
#         return redirect(url_for('admin_login'))
#     return render_template('admin_register.html')

# @app.route('/user_login', methods=['GET', 'POST'])
# def user_login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = User.query.filter_by(username=username, role='user').first()
#         if user and bcrypt.check_password_hash(user.password, password):
#             login_user(user)
#             flash('User login successful!', 'success')
#             return redirect(url_for('user_dashboard'))
#         else:
#             flash('Login failed. Check username and password.', 'danger')
#     return render_template('user_login.html')

# @app.route('/admin_login', methods=['GET', 'POST'])
# def admin_login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         admin = User.query.filter_by(username=username, role='admin').first()
#         if admin and bcrypt.check_password_hash(admin.password, password):
#             login_user(admin)
#             flash('Admin login successful!', 'success')
#             return redirect(url_for('admin_dashboard'))
#         else:
#             flash('Login failed. Check username and password.', 'danger')
#     return render_template('admin_login.html')

# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     flash('You have been logged out.', 'info')
#     return redirect(url_for('user_login'))

# @app.route('/user_dashboard')
# @login_required
# def user_dashboard():
#     if current_user.role != 'user':
#         return redirect(url_for('user_login'))
#     return render_template('user_dashboard.html', username=current_user.username)

# @app.route('/admin_dashboard')
# @login_required
# def admin_dashboard():
#     if current_user.role != 'admin':
#         return redirect(url_for('admin_login'))
#     users = User.query.filter_by(role='user').all()
#     return render_template('admin_dashboard.html', username=current_user.username, users=users)

@app.route("/")
def hello():
    return "hety"

if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)
