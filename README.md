# AI Movie Recommendation System

## Project Overview

AI Movie Recommendation System is a web application that recommends movies based on user preferences using Machine Learning techniques.

The system analyzes movie information such as genres, cast, keywords, overview, and director details to find similar movies and provide personalized recommendations.

This project is developed using Python, Flask, SQLite, Scikit-Learn, and the TMDB 5000 Movies Dataset.

---

## Features

* User Registration and Login
* Secure Password Hashing
* Movie Recommendation Engine
* TF-IDF Vectorization
* Cosine Similarity Based Recommendations
* SQLite Database Integration
* Responsive Web Interface
* GitHub Version Control

---

## Technologies Used

### Frontend

* HTML5
* CSS3

### Backend

* Python
* Flask

### Database

* SQLite
* SQLAlchemy

### Machine Learning

* Scikit-Learn
* TF-IDF Vectorizer
* Cosine Similarity

### Dataset

* TMDB 5000 Movies Dataset

---

## Project Structure

```text
Movie-Recommendation-System/

├── app.py
├── models.py
├── recommender.py

├── templates/
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   └── result.html

├── static/
│   └── style.css

├── dataset/
│   ├── tmdb_5000_movies.csv
│   └── tmdb_5000_credits.csv

├── instance/
│   └── database.db

├── requirements.txt
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Vedmehta-22/Movie-Recommendation-System.git

cd Movie-Recommendation-System
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## Recommendation Algorithm

The recommendation engine follows these steps:

1. Load movie dataset.
2. Combine genres, keywords, cast, crew, and overview into tags.
3. Convert text data using TF-IDF Vectorizer.
4. Calculate similarity using Cosine Similarity.
5. Recommend the top similar movies.

---

## Dataset

The project uses the TMDB 5000 Movies Dataset.

The dataset contains:

* Movie Title
* Genres
* Cast Information
* Crew Information
* Keywords
* Overview
* Ratings

---

## Future Enhancements

* Movie Posters using TMDB API
* Favorite Movies Feature
* Search History
* Firebase Google Authentication
* Advanced Hybrid Recommendation System
* Dark Mode Interface

---

## Author

Ved Mehta
