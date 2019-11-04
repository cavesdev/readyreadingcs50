import os

from flask import Flask, session, render_template, request, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

KEY = 'yAcxcAMdMRIghLzrb86x5Q'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app = Flask(__name__)

# configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # check if user exists
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 0:
            return render_template('error.html', message="User doesn't exist. Please register first.")

        # try to log in users
        if db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                      {"username": username, "password": password}).rowcount == 0:
            return render_template('error.html', message="Incorrect password.")

        session['username'] = username
        return render_template('index.html')
    else:
        if session.get('username') is not None:
            return render_template('error.html',
                                   message="Please logout from the current user before attempting to log in again")
        return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db.execute("INSERT INTO users(username, password) VALUES (:username, :password)",
                   {"username": username, "password": password})
        db.commit()
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')


@app.route('/logout')
def logout():
    if session.get('username') is None:
        return render_template('error.html', message="There is no user logged in.")

    session['username'] = None
    return redirect(url_for('index'))


@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    kw_type = request.form.get('kw_type')

    if kw_type is None:
        kw_type = 'title'

    results = db.execute(f"SELECT * FROM books WHERE {kw_type} LIKE :keyword", {"keyword": f"%{keyword}%"}).fetchall()

    return render_template('search.html', keyword=keyword, results=results)
