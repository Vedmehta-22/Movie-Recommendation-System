from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)
    
class Favorite(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_email = db.Column(
        db.String(120)
    )

    movie_name = db.Column(
        db.String(200)
    )    

class UserMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    movie_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False) # 'watchlist', 'dropped', 'best', 'worst'