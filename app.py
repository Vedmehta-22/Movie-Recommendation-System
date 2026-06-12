from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash
from models import db, User, Favorite, UserMovie
from werkzeug.security import check_password_hash
from recommender import recommend, get_movies_by_genre, get_movie_details_by_title, get_random_movies

app = Flask(__name__)

app.config['SECRET_KEY'] = 'movieproject123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def home():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_email'] = user.email
            session['username'] = user.username
            return redirect('/dashboard')

        return render_template('login.html', error="Invalid Email or Password")

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if email is already registered
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return render_template('signup.html', error="Email address is already registered.")

        # Check if username is already taken
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            return render_template('signup.html', error="Username is already taken.")

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        session['user_email'] = email
        session['username'] = username

        return redirect('/dashboard')

    return render_template('signup.html')

@app.route('/recommend', methods=['GET', 'POST'])
def recommendation():

    if request.method == 'POST':
        movie = request.form['movie']
        return redirect(f'/recommend?movie={movie}')

    movie = request.args.get('movie')
    if not movie:
        return redirect('/dashboard')

    try:
        results = recommend(movie)

        return render_template(
            'result.html',
            searched_movie=results['searched_movie'],
            movies=results['recommendations']
        )

    except Exception as e:
        return str(e)

@app.route('/dashboard')
def dashboard():
    suggested = get_random_movies(4)
    return render_template('dashboard.html', suggested_movies=suggested)
@app.route('/favorite/<movie>')
def favorite(movie):

    user_email = session.get('user_email', 'guest')
    
    # Check if already favorited to avoid duplicates
    existing = Favorite.query.filter_by(user_email=user_email, movie_name=movie).first()
    if not existing:
        fav = Favorite(
            user_email=user_email,
            movie_name=movie
        )
        db.session.add(fav)
        db.session.commit()

    return redirect(request.referrer or '/dashboard')

@app.route('/remove_favorite/<movie>')
def remove_favorite(movie):
    user_email = session.get('user_email', 'guest')
    fav = Favorite.query.filter_by(user_email=user_email, movie_name=movie).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return redirect(request.referrer or '/dashboard')

@app.route('/favorites')
def favorites():

    user_email = session.get('user_email', 'guest')
    fav_entries = Favorite.query.filter_by(user_email=user_email).all()

    # Load details for each favorite movie in parallel to avoid slow page load
    titles = [fav.movie_name for fav in fav_entries]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(len(titles), 10) if titles else 1) as executor:
        fav_movies = list(executor.map(get_movie_details_by_title, titles))

    return render_template(
        'favorites.html',
        favorites=fav_movies
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/genres')
def genres():
    return render_template('genres.html')

@app.route('/genres/<genre_name>')
def genre_movies(genre_name):
    movies = get_movies_by_genre(genre_name)
    return render_template('genre_movies.html', genre=genre_name, movies=movies)

@app.route('/update_list/<status>/<movie>')
def update_list(status, movie):
    user_email = session.get('user_email', 'guest')
    if status in ['watchlist', 'dropped', 'best', 'worst']:
        entry = UserMovie.query.filter_by(user_email=user_email, movie_name=movie).first()
        if entry:
            entry.status = status
        else:
            entry = UserMovie(user_email=user_email, movie_name=movie, status=status)
            db.session.add(entry)
        db.session.commit()
    return redirect(request.referrer or '/dashboard')

@app.route('/remove_from_list/<movie>')
def remove_from_list(movie):
    user_email = session.get('user_email', 'guest')
    entry = UserMovie.query.filter_by(user_email=user_email, movie_name=movie).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(request.referrer or '/dashboard')

@app.route('/profile')
def profile():
    user_email = session.get('user_email', 'guest')
    username = session.get('username', 'Guest')
    
    entries = UserMovie.query.filter_by(user_email=user_email).all()
    
    watchlist = []
    dropped = []
    best = []
    worst = []
    
    # Load details for all entries in parallel
    titles = [entry.movie_name for entry in entries]
    if titles:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(titles), 15)) as executor:
            details_list = list(executor.map(get_movie_details_by_title, titles))
            
        # Distribute details to lists based on database status
        for entry, details in zip(entries, details_list):
            if entry.status == 'watchlist':
                watchlist.append(details)
            elif entry.status == 'dropped':
                dropped.append(details)
            elif entry.status == 'best':
                best.append(details)
            elif entry.status == 'worst':
                worst.append(details)
            
    return render_template(
        'profile.html',
        username=username,
        email=user_email,
        watchlist=watchlist,
        dropped=dropped,
        best=best,
        worst=worst
    )

if __name__ == "__main__":
    app.run(debug=True)