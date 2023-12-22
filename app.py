from datetime import datetime
from flask import Flask, render_template, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask import flash
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/doorlock_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class CardLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_uid = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('card_logs', lazy=True))

with app.app_context():
    db.create_all()

def is_user_logged_in():
    return 'user_id' in session

def get_logged_in_user():
    if is_user_logged_in():
        user_id = session['user_id']
        return User.query.get(user_id)
    return None

def log_card_tap(user_id, card_uid):
    new_card_log = CardLog(user_id=user_id, card_uid=card_uid)
    db.session.add(new_card_log)
    db.session.commit()

def is_admin_logged_in():
    return 'admin_id' in session

def get_logged_in_admin():
    if is_admin_logged_in():
        admin_id = session['admin_id']
        return Admin.query.get(admin_id)
    return None

@app.route('/')
def index():
    user = get_logged_in_user()
    admin = get_logged_in_admin()
    return render_template('index.html', user=user, admin=admin)

#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_email = request.form['username_email']
        password = request.form['password']

        # jika user
        user = User.query.filter((User.username == username_email) | (User.email == username_email)).first()

        if user and user.password == password:
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('home'))
        
        # jika admin
        admin = Admin.query.filter((Admin.username == username_email) | (Admin.email == username_email)).first()

        if admin and admin.password == password:
            session['admin_id'] = admin.id
            flash('Admin login successful', 'success')
            return redirect(url_for('home'))

        flash('Invalid username or password', 'error')

    return render_template('login.html')

# regis admin
@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        new_admin = Admin(full_name=full_name, username=username, email=email, password=password)
        db.session.add(new_admin)
        db.session.commit()

        return redirect(url_for('login'))
    else:
        return render_template('admin_register.html')
    
# regis user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        card_uid = request.form.get('card_uid')  # Retrieve card UID from the form

        new_user = User(full_name=full_name, username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        if card_uid:
            user = User.query.filter_by(username=username).first()
            if user:
                log_card_tap(user.id, card_uid)

        return redirect(url_for('login'))
    else:
        return render_template('register.html')

# home
@app.route('/home')
def home():
    user_id = session.get('user_id')
    admin_id = session.get('admin_id')

    if user_id:
        # jika user
        user = User.query.get(user_id)
        return render_template('home.html', user=user)
    elif admin_id:
        # jika admin
        admin = Admin.query.get(admin_id)
        return render_template('home.html', admin=admin)
    else:
        # Jika tidak ada sesi pengguna atau admin, arahkan ke halaman login
        return redirect(url_for('login'))

# profile
@app.route('/profile')
def profile():
    if is_user_logged_in():
        user = get_logged_in_user()

        if isinstance(user, User):
            # Jika pengguna adalah User, tampilkan template untuk profil pengguna
            return render_template('profile.html', user=user)
        elif isinstance(user, Admin):
            # Jika pengguna adalah Admin, tampilkan template untuk profil admin
            return render_template('admin_profile.html', admin=user)
        else:
            # Kasus lain (misalnya, jika tipe pengguna tidak dikenali)
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

#card_log
@app.route('/card_log')
def card_log():
    user = get_logged_in_user()
    if user:
        card_logs = CardLog.query.filter_by(user_id=user.id).all()
        return render_template('card_log.html', user=user, card_logs=card_logs)
    else:
        return redirect(url_for('login'))

# logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)