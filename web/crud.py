from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session
import time
import json
from flask_sqlalchemy import SQLAlchemy

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
    card_uid = db.Column(db.String(255))  # Kolom baru untuk menyimpan card UID

# Variabel untuk menyimpan UID
current_uid = ""

def is_user_logged_in():
    return 'user_id' in session

def get_logged_in_user():
    if is_user_logged_in():
        user_id = session['user_id']
        return User.query.get(user_id)
    return None

@app.route('/')
def index():
    user = get_logged_in_user()
    if user:
        return redirect(url_for('profile'))
    else:
        return render_template('home.html')

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

    # Periksa apakah card UID sudah terdaftar
    existing_card_user = User.query.filter_by(card_uid=card_uid).first()
    if existing_card_user:
        return jsonify(success=False, message='Card UID already registered')

    # Periksa apakah username atau email sudah ada di database
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify(success=False, message='Username or email already exists')

    # Tambahkan pengguna baru ke dalam database
    new_user = User(full_name=full_name, username=username, email=email, password=password, card_uid=card_uid)
    db.session.add(new_user)
    db.session.commit()

    # Redirect ke halaman login setelah registrasi sukses
    return redirect(url_for('show_login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_email = request.form.get('username_email')
        password = request.form.get('password')

        user = User.query.filter((User.username == username_email) | (User.email == username_email)).first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('home'))  # Mengarahkan ke halaman home setelah login sukses

        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html', error='')

@app.route('/home')
def home():
    user = get_logged_in_user()
    if user:
        return render_template('home.html', user=user)
    else:
        return render_template('home.html')

@app.route('/register', methods=['GET'])
def show_register():
    return render_template('registration.html')

@app.route('/login', methods=['GET'])
def show_login():
    return render_template('login.html')

@app.route('/profile')
def profile():
    user = get_logged_in_user()
    if user:
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    # Bersihkan sesi dan redirect ke halaman home
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)