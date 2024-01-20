from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session, flash
import time
import json
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import secrets

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/doorlock_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'your_email@example.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@example.com'

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
mail = Mail(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    card_uid = db.Column(db.String(255))
    card_activated = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    failed_login = db.Column(db.DateTime, default=None)
    role = db.Column(db.String(20), nullable=False, default='user')
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def increment_failed_login(self):
        self.failed_attempts += 1
        self.failed_login = datetime.utcnow()
        db.session.commit()

    def reset_failed_login(self):
        self.failed_attempts = 0
        self.failed_login = None
        db.session.commit()

    def is_account_locked(self):
        if self.failed_attempts >= 3:
            if (
                self.failed_login
                and datetime.utcnow() - self.failed_login < timedelta(minutes=15)
            ):
                return True
            else:
                self.reset_failed_login()
        return False

current_uid = ""

def is_user_logged_in():
    return 'user_id' in session

def get_logged_in_user():
    if is_user_logged_in():
        user_id = session['user_id']
        return User.query.get(user_id)
    return None

def is_admin_logged_in():
    return 'admin_id' in session

def get_logged_in_admin():
    if is_admin_logged_in():
        admin_id = session['admin_id']
        return Admin.query.get(admin_id)
    return None

def send_reset_email(email, token):
    reset_link = url_for('reset_password', token=token, _external=True)
    message = Message('Reset Your Password', recipients=[email])
    message.body = f'To reset your password, click the following link: {reset_link}'
    mail.send(message)

def generate_reset_token():
    return secrets.token_hex(16)

@app.route('/')
def index():
    user = get_logged_in_user()
    admin = get_logged_in_admin()
    role = user.role if user else admin.role if admin else None
    return render_template('index.html', user=user, admin=admin, role=role)


@app.route('/stream')
def stream():
    def event_stream():
        while True:
            # Mengirimkan UID ke klien
            yield f"data: {json.dumps({'uid': current_uid})}\n\n"
            time.sleep(1)

    return Response(event_stream(), content_type='text/event-stream')

@app.route('/update_uid', methods=['POST'])
def update_uid():
    global current_uid
    current_uid = request.form.get('uid')

    return jsonify(success=True)

@app.route('/register', methods=['POST'])
def register():
    full_name = request.form.get('full_name')
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    card_uid = request.form.get('card_uid')

    existing_card_user = User.query.filter_by(card_uid=card_uid).first()
    if existing_card_user:
        flash('Card UID already registered', 'error')
        return redirect(url_for('register'))  # Ganti 'registration' dengan rute registrasi yang sesuai

    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        flash('Username or email already exists', 'error')
        return redirect(url_for('register'))

    new_user = User(full_name=full_name, username=username, email=email, password=password, card_uid=card_uid)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return render_template('contact_info.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username_email = request.form['username_email']
        password = request.form['password']

        user = User.query.filter((User.username == username_email) | (User.email == username_email)).first()

        if user:
            if user.is_account_locked():
                flash('Account is locked. Try again after 15 minutes.')
                return redirect(url_for('login'))

            if user.check_password(password):
                user.reset_failed_login()
                session['user_id'] = user.id
                flash('Login successful', 'success')
                return redirect(url_for('home'))
            else:
                user.increment_failed_login()
        
        admin = Admin.query.filter((Admin.username == username_email) | (Admin.email == username_email)).first()

        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            return redirect(url_for('tabel')) 
        else:
            flash('Wrong Username/Password. Try again.')

    return render_template('login.html')

@app.route('/home')
def home():
    user_id = session.get('user_id')
    admin_id = session.get('admin_id')

    if user_id:
        user = User.query.get(user_id)
        return render_template('home.html', user=user, role=user.role)
    elif admin_id:
        admin = Admin.query.get(admin_id)
        return render_template('home.html', admin=admin, role='admin')
    else:
        return redirect(url_for('login'))
    
@app.route('/rfid')
def rfid_feature():
    # You can add any necessary logic for the RFID feature here
    return render_template('rfid.html')

@app.route('/pushbutton')
def button_feature():
    # You can add any necessary logic for the RFID feature here
    return render_template('pushbutton.html')

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_admin = Admin.query.filter((Admin.username == username) | (Admin.email == email)).first()
        if existing_admin:
            flash('Username or email already exists', 'error')
            return redirect(url_for('register_admin'))

        new_admin = Admin(full_name=full_name, username=username, email=email, password=password)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()

        flash('Admin registration successful', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('admin_registration.html')

@app.route('/register', methods=['GET'])
def show_register():
    return render_template('registration.html')

@app.route('/login', methods=['GET'])
def show_login():
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_reset_token()
            user.reset_token = token
            user.reset_token_expiration = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()

            send_reset_email(user.email, token)

            flash('Check your email for instructions to reset your password.', 'info')
            return redirect(url_for('login'))

        flash('Email address not found. Please register for an account.', 'error')

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if user and user.reset_token_expiration > datetime.utcnow():
        if request.method == 'POST':
            new_password = request.form.get('new_password')
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiration = None
            db.session.commit()

            flash('Password reset successful. You can now login with your new password.', 'success')
            return redirect(url_for('login'))

        return render_template('reset_password.html', token=token)

    flash('Invalid or expired reset token. Please try again.', 'error')
    return redirect(url_for('forgot_password'))

@app.route('/profile')
def profile():
    user = get_logged_in_user()
    admin = get_logged_in_admin()

    if user:
        return render_template('profile.html', user=user)
    elif not admin:
        flash('Unauthorized access. Please log in as an admin.', 'error')
        return redirect(url_for('login'))

    users = User.query.all()

    return render_template('profileadmin.html', admin=admin, users=users)

@app.route('/tabel')
def tabel():
    admin = get_logged_in_admin()

    if not admin:
        flash('Unauthorized access. Please log in as an admin.', 'error')
        return redirect(url_for('login'))

    users = User.query.all()

    return render_template('data_users.html', admin=admin, users=users)

@app.route('/live_check')
def live_check():
    return render_template('live_check.html')

@app.route('/get_card_owner', methods=['GET'])
def get_card_owner():
    uid = request.args.get('uid')

    # Cari pemilik kartu berdasarkan UID
    user = User.query.filter_by(card_uid=uid).first()

    if user:
        card_owner = user.full_name
    else:
        card_owner = 'Unknown'

    return jsonify(owner=card_owner)

@app.route('/toggle_activation/<int:user_id>', methods=['POST'])
def toggle_activation(user_id):
    user = User.query.get(user_id)

    if user:
        user.card_activated = not user.card_activated
        db.session.commit()

        flash(f'User {user.full_name} is {"Activated" if user.card_activated else "Deactivated"}', 'success')
    else:
        flash('User not found', 'error')

    return redirect(url_for('tabel'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.full_name} has been deleted', 'success')
    else:
        flash('User not found', 'error')

    return redirect(url_for('tabel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)