"""
Created to meet these requirements:
- Store and access movies in a database
- Display them on a dynamic front-end website using the Flask framework.
"""

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

MOVIE_DB_API_KEY = "28fe4b77bf20d67763a3ef5810fa663a"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

class MyForm(FlaskForm):
    rating = StringField(label='Rating')
    review = StringField(label='Review')
    submit = SubmitField(label='Submit')

class OtherForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Submit")

# CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    def __repr__(self):
        return f'<Movie: {self.title} Place: #{self.ranking}>'   
    

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    """Display the homepage with movies ordered by rating."""
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)

@app.route("/edit-review", methods=["GET", "POST"])
def edit_review():
    """Edit the rating and review of a movie."""
    form = MyForm()
    if form.validate_on_submit():
        # Change database stuff and go back
        id = request.args.get('id')
        movie = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
        movie.review = form.review.data
        movie.rating = form.rating.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form)

@app.route("/delete", methods=["GET", "POST"])
def delete_review():
    """Delete a movie from the database."""
    id = request.args.get('id')
    movie = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add-review", methods=["GET", "POST"])
def add_movie():
    """Add a new movie by searching TMDb."""
    form = OtherForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        movies_list = [movie for movie in response.json()['results']]
        return render_template("select.html", movies=movies_list)
    return render_template("add.html", form=form)

@app.route("/find", methods=["GET", "POST"])
def find_movie():
    """Fetch movie details from TMDb and add to the database."""
    movie_api_id = request.args.get('id')
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        print(data)
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("edit_review", id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
