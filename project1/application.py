import os
import csv
from flask import Flask, session, request, render_template, redirect, flash, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

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

    exist = db.execute("SELECT * FROM users WHERE (username=:username)",{"username": username}).fetchone()
    match = db.execute("SELECT * FROM users WHERE username=:username AND password=:password" , {"username":username, "password":password}).fetchone()
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
    taken = db.execute("SELECT * from users WHERE username=:username",{"username":username}).fetchone()
    reg_status=db.execute("SELECT * from users WHERE email=:email",{"email":email}).fetchone()
    if taken is not None:
       if reg_status is None: 
           flash("The username is used by other users. please pick a different username.")
           return render_template("register.html")
    elif reg_status is not None:
        flash ("The email is registered, please log in with the username related to this email.")
        return render_template("index.html")
    else:
        db.execute("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)",{"username": username, "password":password, "email":email})
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
    content = db.execute("SELECT * FROM books WHERE (isbn LIKE :content OR title LIKE :content OR author LIKE :content)" , {"content":content}).fetchall()

    return render_template('search.html',results=content,username=username)

@app.route("/book/<isbn>",methods=['GET','POST'])
def book(isbn):
    if request.method == "POST":
        username = session["username"]
        
        rating = int(request.form.get("rating"))
        comment = request.form.get("comment")
        
        isbn = db.execute("SELECT isbn FROM books WHERE isbn = :isbn",{"isbn": isbn}).fetchone()[0]
        
        check = db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn",{"username": username, "isbn": isbn})

        if check is not None:
            session['username'] = username
            flash("You already have review on this book.")
        else:
            db.execute("INSERT INTO reviews (username, isbn, comment, rating) VALUES (:username, :isbn, :comment, :rating)", {"username": username,"isbn": isbn, "comment": comment, "rating": rating})
            db.commit()
            flash('Review submitted!')
            return redirect("/book/" + isbn)
    else:
        book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
        
        isbn = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()[0]
        reviews = db.execute("SELECT username, comment, rating FROM reviews WHERE isbn = :isbn",{"isbn": isbn}).fetchall()
        
        return render_template("book.html", content=book_info, reviews=reviews)