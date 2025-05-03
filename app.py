from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import unittest
from abc import ABC, abstractmethod
from datetime import date


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies_shows.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

TMDB_API_KEY = 'c7df9686ce2ff29bf93eebe314fde971'

def tmdb_url(path, **params):
    base = "https://api.themoviedb.org/3"
    params['api_key'] = TMDB_API_KEY
    query = '&'.join(f"{k}={v}" for k, v in params.items())
    return f"{base}{path}?{query}"


# ----------------- Models with Inheritance + Polymorphism -----------------

class MediaItem(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    release_year = db.Column(db.Integer, nullable=False)

    def display_info(self):
        return f"{self.title} ({self.release_year}) - {self.genre}"

class Movie(MediaItem):
    duration = db.Column(db.Integer, nullable=False)

    def display_info(self):
        return f"Movie: {super().display_info()} - {self.duration} min"

    def __repr__(self):
        return f'<Movie {self.title}>'

class TVShow(MediaItem):
    seasons = db.Column(db.Integer, nullable=False)
    episodes_per_season = db.Column(db.Integer, nullable=False)

    def display_info(self):
        return f"TV Show: {super().display_info()} - {self.seasons} seasons"

    def __repr__(self):
        return f'<TV Show {self.title}>'

    # ----------------- Factory Pattern -----------------

class MediaFactory:
    @staticmethod
    def create_media(media_type, **kwargs):
        if media_type == 'movie':
            return Movie(**kwargs)
        elif media_type == 'tvshow':
            return TVShow(**kwargs)
        else:
            raise ValueError("Unknown media type")

# ----------------- Strategy Pattern -----------------

class SearchStrategy(ABC):
    @abstractmethod
    def search(self, query):
        pass

class MovieSearchStrategy(SearchStrategy):
    def search(self, query):
        url = tmdb_url("/search/movie", query=query)
        response = requests.get(url)
        return response.json().get('results', [])

class TVShowSearchStrategy(SearchStrategy):
    def search(self, query):
        url = tmdb_url("/search/tv", query=query)
        response = requests.get(url)
        return response.json().get('results', [])

# ----------------- Create Tables -----------------
with app.app_context():
    db.create_all()

# ----------------- ROUTES -----------------
@app.route('/')
def home():
    return render_template('index.html')

# --------Add View Delete---------

def add_media(media_type):
    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        release_year = request.form['release_year']
        if media_type == 'movie':
            duration = request.form['duration']
            media_item = Movie(title=title, genre=genre, release_year=release_year, duration=duration)
        elif media_type == 'tvshow':
            seasons = request.form['seasons']
            episodes_per_season = request.form['episodes_per_season']
            media_item = TVShow(title=title, genre=genre, release_year=release_year,
                                seasons=seasons, episodes_per_season=episodes_per_season)
        db.session.add(media_item)
        db.session.commit()
        return redirect(url_for(f'{media_type}s'))

    return render_template(f'add_{media_type}.html')

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    return add_media('movie')

@app.route('/add_tvshow', methods=['GET', 'POST'])
def add_tvshow():
    return add_media('tvshow')

@app.route('/movies')
def movies():
    all_movies = Movie.query.all()
    return render_template('movies.html', movies=all_movies)

@app.route('/tvshows')
def tvshows():
    all_shows = TVShow.query.all()
    return render_template('tvshows.html', shows=all_shows)

def delete_media(media_type, media_id):
    model = Movie if media_type == 'movie' else TVShow
    media_item = model.query.get_or_404(media_id)

    db.session.delete(media_item)
    db.session.commit()
    return redirect(url_for(f'{media_type}s'))

@app.route('/delete/<media_type>/<int:media_id>')
def delete(media_type, media_id):
    return delete_media(media_type, media_id)

# --------Add To Watched---------

@app.route('/add_to_watched/<media_type>/<int:media_id>', methods=['POST'])
def add_to_watched(media_type, media_id):
    # Fetch movie or TV show details from TMDB API
    if media_type == 'movie':
        url = tmdb_url(f"/movie/{media_id}")
    elif media_type == 'tvshow':
        url = tmdb_url(f"/tv/{media_id}")
    else:
        return "Invalid media type", 400

    response = requests.get(url)
    data = response.json()

    # Extract common attributes
    title = data.get('title') if media_type == 'movie' else data.get('name')
    release_year = data.get('release_date', 'N/A')[:4] if media_type == 'movie' else data.get('first_air_date', 'N/A')[:4]

    # Check for duplicates
    if media_type == 'movie':
        existing_movie = Movie.query.filter_by(title=title, release_year=release_year).first()
        if existing_movie:
            return redirect(request.referrer or url_for('home'))  # Skip adding duplicate
        genre = ', '.join([genre['name'] for genre in data.get('genres', [])])
        duration = data.get('runtime', 0)
        movie = Movie(title=title, genre=genre, release_year=release_year, duration=duration)
        db.session.add(movie)
    elif media_type == 'tvshow':
        existing_tvshow = TVShow.query.filter_by(title=title, release_year=release_year).first()
        if existing_tvshow:
            return redirect(request.referrer or url_for('home'))  # Skip adding duplicate
        genre = ', '.join([genre['name'] for genre in data.get('genres', [])])
        seasons = data.get('number_of_seasons', 0)
        episodes_per_season = data.get('number_of_episodes', 0) // max(seasons, 1)
        tvshow = TVShow(title=title, genre=genre, release_year=release_year, seasons=seasons, episodes_per_season=episodes_per_season)
        db.session.add(tvshow)

    db.session.commit()
    return redirect(request.referrer or url_for('home'))

# ---------Discover Movies and TV Shows---------
@app.route('/discover')
def discover():
    page = request.args.get('page', 1, type=int)

    trending_movies_url = tmdb_url("/trending/movie/week", page=page)
    trending_movies_response = requests.get(trending_movies_url)
    trending_movies = trending_movies_response.json().get('results', [])

    trending_tvshows_url = tmdb_url("/trending/tv/week", page=page)
    trending_tvshows_response = requests.get(trending_tvshows_url)
    trending_tvshows = trending_tvshows_response.json().get('results', [])

    return render_template(
        'discover.html',
        trending_movies=trending_movies,
        trending_tvshows=trending_tvshows,
        current_page=page
    )


@app.route('/top_rated_movies')
def top_rated_movies():
    page = request.args.get('page', 1, type=int)

    top_rated_movies_url = tmdb_url("/movie/top_rated", page=page)
    response = requests.get(top_rated_movies_url)
    movies = response.json().get('results', [])

    return render_template(
        'top_rated_movies.html',
        movies=movies,
        current_page=page
    )

@app.route('/top_rated_tvshows')
def top_rated_tvshows():
    page = request.args.get('page', 1, type=int)

    top_rated_tvshows_url = tmdb_url("/tv/top_rated", page=page)
    response = requests.get(top_rated_tvshows_url)
    tvshows = response.json().get('results', [])

    return render_template(
        'top_rated_tvshows.html',
        tvshows=tvshows,
        current_page=page
    )





# ---------------------Search Bar-----------------------

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['search_query']
        search_type = request.form['search_type']
        return redirect(url_for('search', search_query=query, search_type=search_type))

    # Handle GET request with query parameters
    query = request.args.get('search_query', '')
    search_type = request.args.get('search_type', 'movie')

    if not query:
        return render_template('search_results.html', message="No search query provided.")

    if search_type == 'movie':
        url = tmdb_url("/search/movie", query=query)
    elif search_type == 'tvshow':
        url = tmdb_url("/search/tv", query=query)
    else:
        return render_template('search_results.html', message="Invalid search type.")

    response = requests.get(url)
    data = response.json()

    if data.get('results'):
        results = data['results']
        return render_template('search_results.html', results=results, search_type=search_type, search_query=query)
    else:
        return render_template('search_results.html', message="No results found.", search_type=search_type, search_query=query)

    # --------Movie Details---------

@app.route('/movie_details/<int:movie_id>')
def movie_details(movie_id):
    url = tmdb_url(f"/movie/{movie_id}")
    response = requests.get(url)
    data = response.json()
    if 'status_code' in data and data['status_code'] == 34:
        return render_template('404.html')
    title = data.get('title', 'N/A')
    overview = data.get('overview', 'No overview available.')
    release_date = data.get('release_date', 'N/A')
    runtime = data.get('runtime', 'N/A')
    vote_average = data.get('vote_average', 'N/A')
    genres = ', '.join([genre['name'] for genre in data.get('genres', [])])
    poster_path = data.get('poster_path', None)
    trailer_key = get_trailer_key(movie_id, TMDB_API_KEY)
    production_companies = ', '.join([company['name'] for company in data.get('production_companies', [])])
    cast = get_cast(movie_id, TMDB_API_KEY)
    similar_movies = get_similar_movies(movie_id, TMDB_API_KEY)
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    return render_template('movie_details.html',
                           title=title,
                           overview=overview,
                           release_date=release_date,
                           runtime=runtime,
                           vote_average=vote_average,
                           genres=genres,
                           poster_url=poster_url,
                           trailer_key=trailer_key,
                           production_companies=production_companies,
                           cast=cast,
                           similar_movies=similar_movies,
                           movie_id=movie_id)

def get_trailer_key(movie_id, TMDB_API_KEY):
    url = tmdb_url(f"/movie/{movie_id}/videos", language="en-US")
    response = requests.get(url)
    data = response.json()
    if data.get('results'):
        return data['results'][0].get('key')
    return None

def get_cast(movie_id, TMDB_API_KEY):
    url = tmdb_url(f"/movie/{movie_id}/credits", language="en-US")
    response = requests.get(url)
    data = response.json()
    cast = []
    for cast_member in data.get('cast', [])[:5]:
        actor_name = cast_member['name']
        actor_profile_path = cast_member.get('profile_path', None)
        actor_profile_url = f"https://image.tmdb.org/t/p/w500{actor_profile_path}" if actor_profile_path else None
        cast.append({
            'name': actor_name,
            'profile_url': actor_profile_url,
            'id': cast_member['id']
        })
    return cast

def get_similar_movies(movie_id, TMDB_API_KEY):
    url = tmdb_url(f"/movie/{movie_id}/similar", language="en-US")
    response = requests.get(url)
    data = response.json()
    return [{'title': movie['title'], 'id': movie['id'], 'poster': movie['poster_path']} for movie in data.get('results', [])][:5]

@app.route('/movie/<int:movie_id>/cast')
def full_cast(movie_id):
    url = tmdb_url(f"/movie/{movie_id}/credits")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        cast = data.get("cast", [])
        return render_template("full_cast.html", cast=cast, movie_id=movie_id)
    else:
        return "Failed to fetch cast details."

    # --------Actor Details---------

@app.route('/actor_details/<int:actor_id>')
def actor_details(actor_id):
    url = tmdb_url(f"/person/{actor_id}", language="en-US")
    response = requests.get(url)
    actor_data = response.json()
    if 'status_code' in actor_data and actor_data['status_code'] == 34:
        return render_template('404.html')
    name = actor_data.get('name', 'N/A')
    biography = actor_data.get('biography', 'No biography available.')
    birthday = actor_data.get('birthday', 'N/A')
    place_of_birth = actor_data.get('place_of_birth', 'N/A')
    profile_path = actor_data.get('profile_path', None)
    profile_url = f"https://image.tmdb.org/t/p/w500{profile_path}" if profile_path else None
    movie_credits = get_actor_movies(actor_id)
    return render_template('actor_details.html',
                           name=name,
                           biography=biography,
                           birthday=birthday,
                           place_of_birth=place_of_birth,
                           profile_url=profile_url,
                           movie_credits=movie_credits)

def get_actor_movies(actor_id):
    url = tmdb_url(f"/person/{actor_id}/movie_credits", language="en-US")
    response = requests.get(url)
    data = response.json()
    movie_credits = []
    for movie in data.get('cast', [])[:6]:
        movie_title = movie['title']
        movie_id = movie['id']
        movie_poster = movie.get('poster_path', None)
        movie_poster_url = f"https://image.tmdb.org/t/p/w500{movie_poster}" if movie_poster else None
        movie_credits.append({
            'title': movie_title,
            'id': movie_id,
            'poster_url': movie_poster_url
        })
    return movie_credits

# --------Tv Shows---------


@app.route('/tvshow_details/<int:tvshow_id>')
def tvshow_details(tvshow_id):
    url = tmdb_url(f"/tv/{tvshow_id}")
    response = requests.get(url)
    data = response.json()
    if 'status_code' in data and data['status_code'] == 34:
        return render_template('404.html')
    title = data.get('name', 'N/A')
    overview = data.get('overview', 'No overview available.')
    first_air_date = data.get('first_air_date', 'N/A')
    number_of_seasons = data.get('number_of_seasons', 'N/A')
    number_of_episodes = data.get('number_of_episodes', 'N/A')
    vote_average = data.get('vote_average', 'N/A')
    genres = ', '.join([genre['name'] for genre in data.get('genres', [])])
    poster_path = data.get('poster_path', None)
    cast = get_tvshow_cast(tvshow_id, TMDB_API_KEY)
    similar_shows = get_similar_tvshows(tvshow_id, TMDB_API_KEY)
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    return render_template('tvshow_details.html',
                           title=title,
                           overview=overview,
                           first_air_date=first_air_date,
                           number_of_seasons=number_of_seasons,
                           number_of_episodes=number_of_episodes,
                           vote_average=vote_average,
                           genres=genres,
                           poster_url=poster_url,
                           cast=cast,
                           similar_shows=similar_shows,
                           tvshow_id=tvshow_id)

def get_tvshow_cast(tvshow_id, TMDB_API_KEY):
    url = tmdb_url(f"/tv/{tvshow_id}/credits", language="en-US")
    response = requests.get(url)
    data = response.json()
    cast = []
    for cast_member in data.get('cast', [])[:5]:
        actor_name = cast_member['name']
        actor_profile_path = cast_member.get('profile_path', None)
        actor_profile_url = f"https://image.tmdb.org/t/p/w500{actor_profile_path}" if actor_profile_path else None
        cast.append({
            'name': actor_name,
            'profile_url': actor_profile_url,
            'id': cast_member['id']
        })
    return cast

def get_similar_tvshows(tvshow_id, TMDB_API_KEY):
    url = tmdb_url(f"/tv/{tvshow_id}/similar", language="en-US")
    response = requests.get(url)
    data = response.json()
    return [{'title': show['name'], 'id': show['id'], 'poster': show['poster_path']} for show in data.get('results', [])][:5]

@app.route('/tvshow/<int:tvshow_id>/cast')
def full_tvshow_cast(tvshow_id):
    url = tmdb_url(f"/tv/{tvshow_id}/credits", language="en-US")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        cast = data.get("cast", [])
        return render_template("full_cast.html", cast=cast, tvshow_id=tvshow_id, is_tvshow=True)
    else:
        return "Failed to fetch cast details."



# ----------------- Unit Tests -----------------

class TestMediaFactory(unittest.TestCase):
    def test_create_movie(self):
        movie = MediaFactory.create_media('movie', title='Inception', genre='Sci-Fi', release_year=2010, duration=148)
        self.assertIsInstance(movie, Movie)
        self.assertEqual(movie.title, 'Inception')

    def test_create_tvshow(self):
        show = MediaFactory.create_media('tvshow', title='Friends', genre='Comedy', release_year=1994, seasons=10, episodes_per_season=24)
        self.assertIsInstance(show, TVShow)
        self.assertEqual(show.title, 'Friends')

class TestSearchStrategy(unittest.TestCase):
    def test_movie_search_strategy(self):
        strategy = MovieSearchStrategy()
        results = strategy.search('Inception')
        self.assertIsInstance(results, list)

    def test_tvshow_search_strategy(self):
        strategy = TVShowSearchStrategy()
        results = strategy.search('Friends')
        self.assertIsInstance(results, list)

if __name__ == '__main__':
    unittest.main(argv=[''], exit=False)
    app.run(debug=True)