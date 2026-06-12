import pandas as pd
import ast
import requests
import threading
from concurrent.futures import ThreadPoolExecutor

API_KEY = "8265bd1679663a7ea12ac168da84d2e8"

# Thread-safe in-memory cache for poster URLs to prevent redundant network calls
poster_cache = {}
cache_lock = threading.Lock()

def convert(text):
    if not isinstance(text, str):
        return []
    try:
        L = []
        for i in ast.literal_eval(text):
            L.append(i['name'])
        return L
    except Exception:
        return []

def fetch_director(text):
    if not isinstance(text, str):
        return []
    try:
        L = []
        for i in ast.literal_eval(text):
            if i['job'] == 'Director':
                L.append(i['name'])
        return L
    except Exception:
        return []

def fetch_poster(movie_id, title=None):
    # Convert movie_id to string for consistent cache key
    cache_key = str(movie_id) if movie_id is not None else title
    
    # Check cache first
    with cache_lock:
        if cache_key in poster_cache:
            return poster_cache[cache_key]
            
    # Try fetching by TMDB ID first (direct lookup is faster and more reliable)
    if movie_id is not None:
        try:
            url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
            response = requests.get(url, timeout=6)
            if response.status_code == 200:
                data = response.json()
                poster_path = data.get('poster_path')
                if poster_path:
                    path = f"https://image.tmdb.org/t/p/w500{poster_path}"
                    with cache_lock:
                        poster_cache[cache_key] = path
                    return path
            elif response.status_code == 404:
                # Movie permanently not found, cache fallback
                fallback = "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop"
                with cache_lock:
                    poster_cache[cache_key] = fallback
                return fallback
        except requests.exceptions.RequestException:
            # Temporary network error/timeout: do not cache fallback to allow retrying later
            pass
        except Exception:
            pass

    # Fallback: search by title
    if title:
        try:
            url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={title}"
            response = requests.get(url, timeout=6)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    poster_path = data['results'][0].get('poster_path')
                    if poster_path:
                        path = f"https://image.tmdb.org/t/p/w500{poster_path}"
                        with cache_lock:
                            poster_cache[cache_key] = path
                        return path
            elif response.status_code == 404:
                fallback = "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop"
                with cache_lock:
                    poster_cache[cache_key] = fallback
                return fallback
        except Exception:
            pass
        
    return "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop"

def get_movie_details(row):
    title = row['display_title']
    overview = row['display_overview']
    genres = row['display_genres']
    
    # Format genres beautifully as a list or a joined string
    genres_list = genres if isinstance(genres, list) else []
    genres_str = ", ".join(genres_list) if genres_list else "General"
    
    # Format rating
    rating = row['display_rating']
    rating_formatted = round(float(rating), 1) if pd.notna(rating) else 0.0
    
    # Get movie ID for direct TMDB lookup
    movie_id = row['movie_id'] if 'movie_id' in row else None
    if movie_id is None and 'id' in row:
        movie_id = row['id']
        
    poster = fetch_poster(movie_id, title)
    
    return {
        'title': title,
        'overview': overview if pd.notna(overview) else "No overview available.",
        'genres': genres_str,
        'rating': rating_formatted,
        'poster': poster
    }

# Load datasets
movies = pd.read_csv("dataset/tmdb_5000_movies.csv")
credits = pd.read_csv("dataset/tmdb_5000_credits.csv")

movies = movies.merge(credits, on="title")
movies.dropna(subset=['overview', 'title'], inplace=True)

# Preserve clean display data before splitting tags
movies['display_title'] = movies['title']
movies['display_overview'] = movies['overview']
movies['display_genres'] = movies['genres'].apply(convert)
movies['display_rating'] = movies['vote_average']

# Run tag vector preprocessing
movies['genres'] = movies['genres'].apply(convert)
movies['keywords'] = movies['keywords'].apply(convert)
movies['cast'] = movies['cast'].apply(convert)
movies['crew'] = movies['crew'].apply(fetch_director)
movies['overview'] = movies['overview'].apply(lambda x: x.split())

movies['tags'] = (
    movies['overview'] +
    movies['genres'] +
    movies['keywords'] +
    movies['cast'] +
    movies['crew']
)

# Extract new dataframe with metadata columns preserved
new_df = movies[['movie_id', 'title', 'tags', 'display_title', 'display_overview', 'display_genres', 'display_rating']]
new_df['tags'] = new_df['tags'].apply(lambda x: " ".join(x))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

cv = TfidfVectorizer(
    max_features=5000,
    stop_words='english'
)

vectors = cv.fit_transform(new_df['tags']).toarray()
similarity = cosine_similarity(vectors)

def recommend(movie):
    movie = movie.strip()
    
    # Case-insensitive title match
    matches = new_df[new_df['title'].str.lower() == movie.lower()]
    if matches.empty:
        raise Exception(f"Movie '{movie}' not found in database.")
        
    movie_index = matches.index[0]
    
    # Get details for the searched movie itself
    searched_movie_details = get_movie_details(new_df.iloc[movie_index])
    
    # Get details for recommendations
    distances = similarity[movie_index]
    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]
    
    # Fetch details for recommendations in parallel
    rows = [new_df.iloc[i[0]] for i in movies_list]
    with ThreadPoolExecutor(max_workers=5) as executor:
        recommendations = list(executor.map(get_movie_details, rows))
        
    return {
        'searched_movie': searched_movie_details,
        'recommendations': recommendations
    }

# Smoke test
if __name__ == "__main__":
    print(recommend("Avatar"))
    print("Movies Loaded:", len(new_df))

def get_movies_by_genre(genre_name, limit=12):
    matches = new_df[new_df['display_genres'].apply(
        lambda genres: any(g.lower() == genre_name.lower() for g in genres) if isinstance(genres, list) else False
    )]
    
    # Sort descending by display_rating
    sorted_matches = matches.sort_values(by='display_rating', ascending=False)
    
    # Fetch details in parallel to avoid slow page rendering
    rows = [row for idx, row in sorted_matches.head(limit).iterrows()]
    with ThreadPoolExecutor(max_workers=min(len(rows), 10) if rows else 1) as executor:
        results = list(executor.map(get_movie_details, rows))
        
    return results

def get_movie_details_by_title(title):
    matches = new_df[new_df['title'].str.lower() == title.lower()]
    if not matches.empty:
        return get_movie_details(matches.iloc[0])
    return {
        'title': title,
        'overview': 'No overview available.',
        'genres': 'General',
        'rating': 0.0,
        'poster': 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop'
    }

def get_random_movies(limit=4):
    try:
        random_rows = new_df.sample(n=limit)
        rows = [row for idx, row in random_rows.iterrows()]
        with ThreadPoolExecutor(max_workers=limit) as executor:
            results = list(executor.map(get_movie_details, rows))
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        return []