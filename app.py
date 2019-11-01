import os
import requests

from flask import Flask, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash

from tables import *

KEY = 'yAcxcAMdMRIghLzrb86x5Q'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/project1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if check_password_hash(password):
            return render_template('index.html')

        return render_template('login.html')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = generate_password_hash(request.form.get('password'))

        db.session.add(Users(username=username, password=password))
        db.session.commit()

        return render_template('login.html')
    return render_template('signup.html')