import os
import csv
from flask import Flask, session, request, render_template, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash
app = Flask(__name__)

# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(("postgresql://postgres:Lai1015@localhost:5433/postgres"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    if 'username' in session:
        username = session['username']
        return render_template('search.html', username=username)         
    return render_template("index.html")

 
@app.route("/login",methods=["POST"])
def login():
    username=request.form.get("username")
    password=request.form.get("password")
    if username == '' or password == '':
        flash("Error: username or password cannot be empty.")
        return render_template("index.html")
    exist = db.execute(text("SELECT * FROM users WHERE (username=:username)"),{"username": username}).fetchone()
    match = db.execute(text("SELECT * FROM users WHERE username=:username AND password=:password") , {"username":username, "password":password}).fetchone()
    if exist is not None:
        if match is not None:
            session['username'] = username
            flash("Logged in successfully. You can search your books now!")
            return render_template("search.html",username=username)
        else:
             flash("Error: password is incorrect.")
             return render_template("index.html")
    else:
        flash("Error: username doesn't exist.")
        return render_template("index.html")


@app.route("/register_form",methods=['GET'])
def register_form():
    return render_template("register.html")

    
@app.route("/register", methods=['POST'])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    email=request.form.get("email")
    taken = db.execute(text("SELECT * from users WHERE username=:username"),{"username":username}).fetchone()
    reg_status=db.execute(text("SELECT * from users WHERE email=:email"),{"email":email}).fetchone()
    if taken is not None:
       if reg_status is None: 
           flash("The username is used by other users. please pick a different username.")
           return render_template("register.html")
    elif reg_status is not None:
        flash ("The email is registered, please log in with the username related to this email.")
        return render_template("index.html")
    else:
        db.execute(text("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)"),{"username": username, "password":password, "email":email})
        db.commit()
    session['username'] = username
    flash("Registration completed and log in successfully. You can search your books now!")
    return render_template("search.html",username=username)


@app.route("/logout", methods=['GET'])
def logout():
    del session['username']
    flash("Logged out successfully.")
    return render_template("index.html")

@app.route("/search",methods=['POST'])
def search():
    if 'username' in session:
        username = session['username']
    content=[]      
    content="%"+request.form.get("content")+"%"
    content=content.title()
    content = db.execute(text("SELECT * FROM books WHERE (isbn LIKE :content OR title LIKE :content OR author LIKE :content)") , {"content":content}).fetchall()

    return render_template('search.html',results=content,username=username)

@app.route("/<isbn>",methods=['GET','POST'])
def book(isbn):
    if  request.method == "POST":
        username=session["username"]    
        isbn = db.execute(text("SELECT isbn FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()[0]
        content = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchall()
        reviews = db.execute(text("SELECT username, comment, rating FROM reviews WHERE isbn = :isbn"),{"isbn": isbn}).fetchall()
    #    rating =  request.form.get("rating")
    #    comment = request.form.get("comment") 

    #    check= db.execute(text("SELECT username FROM reviews WHERE (isbn=:isbn)"), {"isbn":isbn})
    #    if check is not None:
    #        flash('You already make comment before.') 
    #        reviews = db.execute(text("SELECT username, comment, rating FROM reviews WHERE isbn = :isbn"),{"isbn": isbn}).fetchall()
    #        return render_template("book.html",isbn=isbn, content=content,username=session["username"], reviews=reviews)
    
    #    username = session["username"]
        rating =  request.form.get("rating")
        comment = request.form.get("comment")
        db.execute(text("INSERT INTO reviews (username, isbn, comment, rating) VALUES (:username, :isbn, :comment, :rating)"), {"username": username,"isbn": isbn, "comment": comment, "rating": rating})
        db.commit()
        reviews = db.execute(text("SELECT username, comment, rating FROM reviews WHERE isbn = :isbn"),{"isbn": isbn}).fetchall()
        flash('Review submitted!')            
        return render_template("book.html",isbn=isbn, content=content,username=username, reviews=reviews)
    else:
        username = session["username"]
        content = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchall()
        isbn = db.execute(text("SELECT isbn FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()[0]
        reviews = db.execute(text("SELECT username, comment, rating FROM reviews WHERE isbn = :isbn"),{"isbn": isbn}).fetchall()
        
        return render_template("book.html",isbn=isbn, content=content,username=username, reviews=reviews)