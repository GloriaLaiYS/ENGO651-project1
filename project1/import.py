import csv
import os 
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(("postgresql://postgres:Lai1015@localhost:5433/postgres"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    with open("books.csv",'r') as f:
        read=csv.reader(f)
        next(f)        
        for isbn,title,author,year in read:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",{"isbn": isbn, "title": title, "author": author, "year": year})
        db.commit()
if __name__ == "__main__":
    main()    
            