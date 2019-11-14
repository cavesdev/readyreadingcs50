import os
import requests

from flask import Flask, session, render_template, request, url_for, redirect, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


KEY = 'yAcxcAMdMRIghLzrb86x5Q'
USER_ID = 102371908

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

        # try to log in user
        user = db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                          {"username": username, "password": password}).fetchone()

        if user is None:
            return render_template('error.html', message="Incorrect password.")

        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('index'))
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


@app.route('/books/<string:isbn>', methods=['GET', 'POST'])
def book_detail(isbn):

    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    reviews = db.execute("SELECT users.username, rating, review FROM reviews JOIN users ON reviews.user_id = users.id "
                         "WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    gr_reviews = requests.get(f'https://www.goodreads.com/book/isbn/{isbn}',
                              params={"format": 'json', "user_id": USER_ID})

    if request.method == 'POST':
        if session.get('user_id') is None:
            render_template('error.html', message="You must be logged in to submit a review.")

        if db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND isbn = :isbn",
                      {"user_id": session.get('user_id'), "isbn": isbn}).rowcount != 0:
            return render_template('error.html', message="You can't review a book more than once.")

        user_id = session.get('user_id')
        rating = request.form.get('star-rating')
        review = request.form.get('review-text')

        db.execute("INSERT INTO reviews (user_id, isbn, rating, review) "
                   "VALUES (:user_id, :isbn, :rating, :review)",
                   {"user_id": user_id, "isbn": isbn, "rating": rating, "review": review})
        db.commit()
        return redirect(url_for('book_detail', isbn=isbn))

    return render_template('detail.html', book=book, reviews=reviews, gr_reviews=gr_reviews.json())


@app.route('/api/<string:isbn>')
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    average_rating = db.execute("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    if book is None:
        return abort(404)
    else:
        avg_float = float("{0:.2f}".format(average_rating.avg))
        res = dict(title=book.title, author=book.author, year=book.year, isbn=isbn, review_count=review_count.count,
                   average_rating=avg_float)
    return jsonify(res)
