from datetime import datetime
from flask import Flask, render_template, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/doorlock_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

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

@app.route('/')
def home():
    user = get_logged_in_user()
    return render_template('home.html', user=user)

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

        # Log card tap if card UID is provided
        if card_uid:
            user = User.query.filter_by(username=username).first()
            if user:
                log_card_tap(user.id, card_uid)

        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_email = request.form['username_email']
        password = request.form['password']

        user = User.query.filter((User.username == username_email) | (User.email == username_email)).first()

        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

# Rute untuk halaman profil
@app.route('/profile')
def profile():
    if is_user_logged_in():
        user = get_logged_in_user()
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('login'))

@app.route('/card_log')
def card_log():
    user = get_logged_in_user()
    if user:
        card_logs = CardLog.query.filter_by(user_id=user.id).all()
        return render_template('card_log.html', user=user, card_logs=card_logs)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
