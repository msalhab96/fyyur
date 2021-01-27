#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
import config
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from models import *

app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
db.create_all()
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  latest_venues = Venue.query.order_by(Venue.id.desc()).limit(10)
  latest_artist = Artist.query.order_by(Artist.id.desc()).limit(10)
  return render_template('pages/home.html',
                         latest_venues= latest_venues,
                         latest_artist= latest_artist)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  all_cities = [item.city for item in db.session.query(Venue.city.distinct().label("city"))]
  data = [] 
  for city in all_cities:
    temp = [] 
    for venue in Venue.query.filter_by(city=city):
      state = venue.state
      id = venue.id
      name = venue.name
      num_upcoming_shows = [1 for item in Show.query.filter_by(venue_id=id).all() if item.time > datetime.now()]
      temp.append({"id": id, "name": name, "num_upcoming_shows": sum(num_upcoming_shows)})
    data.append({"city": city, "state": state, "venues": temp})
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  term = request.form.get('search_term', '')
  all_matches = Venue.query.filter(Venue.name.ilike("%" + term + "%")).all()
  response = {"count": len(all_matches), "data":[]}
  for item in all_matches:
    response['data'].append({"id": item.id, "name": item.name, "num_upcoming_shows": Show.query.filter_by(venue_id=item.id).count()})
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  targeted_venue = Venue.query.filter(Venue.id==venue_id).first()
  shows_in_ven = Show.query.filter(Show.venue_id==targeted_venue.id).all()
  artists_in_venue = Artist.query.join(Show, Artist.id==Show.artist_id).all()
  past_shows = [{"artist_id": item.artist_id,
                 "artist_name": Artist.query.filter_by(id=item.artist_id).first().name,
                 "artist_image_link": Artist.query.filter_by(id=item.artist_id).first().image_link,
                 "start_time": str(item.time)}
                for item in shows_in_ven if item.time < datetime.now()]

  upcoming_shows = [{"artist_id": item.artist_id,
                     "artist_name": Artist.query.filter_by(id=item.artist_id).first().name,
                     "artist_image_link": Artist.query.filter_by(id=item.artist_id).first().image_link,
                     "start_time": str(item.time)} for item in shows_in_ven if item.time > datetime.now()]
  data = {
    "id": targeted_venue.id,
    "name": targeted_venue.name,
    "genres": [item.genres for item in artists_in_venue],
    "address": targeted_venue.address,
    "city": targeted_venue.city,
    "state": targeted_venue.state,
    "phone": targeted_venue.phone,
    "website": targeted_venue.website,
    "facebook_link": targeted_venue.facebook_link,
    "seeking_talent": targeted_venue.seeking_talent,
    "seeking_description": targeted_venue.seeking_description,
    "image_link": targeted_venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  name = request.form.get("name", "")
  city = request.form.get("city", "")
  state = request.form.get("state", "")
  address = request.form.get("address", "")
  phone = request.form.get("phone", "")
  genres = request.form.get("genres", "")
  facebook_link = request.form.get("facebook_link", "")
  venue = Venue(
            name =  name,
            city =  city,
            state = state,
            address= address,
            phone = phone,
            facebook_link = facebook_link,
            )
  try:
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('Venue ' + request.form['name'] + ' could not be listed.')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for("venues"))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = [{"id": item.id, "name": item.name} for item in Artist.query.all()]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  term = request.form.get('search_term', '')
  all_matches = Artist.query.filter(Artist.name.ilike("%" + term + "%")).all()
  response = {"count": len(all_matches), "data":[]}
  for item in all_matches:
    response['data'].append({"id": item.id, "name": item.name, "num_upcoming_shows": Show.query.filter_by(artist_id=item.id).count()})
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  targeted_artist = Artist.query.filter_by(id=artist_id).first()
  targeted_shows = Show.query.filter_by(artist_id=artist_id).all()

  past_shows = [{"venue_id": item.venue_id,
                "venue_name": Venue.query.filter_by(id=item.venue_id).first().name,
                "venue_image_link": Venue.query.filter_by(id=item.venue_id).first().image_link,
                "start_time": str(item.time)}
                for item in targeted_shows if item.time < datetime.now()]

  upcoming_show = [{"venue_id": item.venue_id,
                "venue_name": Venue.query.filter_by(id=item.venue_id).first().name,
                "venue_image_link": Venue.query.filter_by(id=item.venue_id).first().image_link,
                "start_time": str(item.time)}
                for item in targeted_shows if item.time > datetime.now()]

  data = {
    "id": artist_id,
    "name": targeted_artist.name,
    "genres": targeted_artist.genres,
    "city": targeted_artist.city,
    "state": targeted_artist.state,
    "phone": targeted_artist.phone,
    "website": targeted_artist.website,
    "facebook_link": targeted_artist.facebook_link,
    "seeking_venue": targeted_artist.seeking_venue,
    "seeking_description": targeted_artist.seeking_description,
    "image_link": targeted_artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_show,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_show),
  }
  try:
    data['genres'] = data['genres'].split(',')
  except:
    data['genres'] = []
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  targeted_artist = Artist.query.filter_by(id=artist_id).first()
  artist={
    "id": artist_id,
    "name": targeted_artist.name,
    "genres": targeted_artist.genres,
    "city": targeted_artist.city,
    "state": targeted_artist.state,
    "phone": targeted_artist.phone,
    "website": targeted_artist.website,
    "facebook_link": targeted_artist.facebook_link,
    "seeking_venue": targeted_artist.seeking_venue,
    "seeking_description": targeted_artist.seeking_description,
    "image_link": targeted_artist.image_link,
  }
  try:
    artist['genres'] = artist['genres'].split(',')
  except:
    pass
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  targeted_artist = Artist.query.filter_by(id=artist_id).first()
  targeted_artist.name = request.form.get("name", targeted_artist.name)
  targeted_artist.genres = request.form.get("genres", targeted_artist.genres)
  targeted_artist.city = request.form.get("city", targeted_artist.city)
  targeted_artist.state = request.form.get("state", targeted_artist.state)
  targeted_artist.phone = request.form.get("phone", targeted_artist.phone)
  targeted_artist.facebook_link = request.form.get("facebook_link", targeted_artist.facebook_link)
  db.session.add(targeted_artist)
  db.session.commit()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  targeted_venue = Venue.query.filter_by(id=venue_id).first()
  venue={
    "id": venue_id,
    "name": targeted_venue.name,
    "genres": targeted_venue.genres,
    "address": targeted_venue.address,
    "city": targeted_venue.city,
    "state": targeted_venue.state,
    "phone": targeted_venue.phone,
    "website": targeted_venue.website,
    "facebook_link": targeted_venue.facebook_link,
    "seeking_talent": targeted_venue.seeking_venue,
    "seeking_description": targeted_venue.seeking_description,
    "image_link": targeted_venue.image_link,
  }
  try:
    venue['genres'] = venue['genres'].split(',')
  except:
    pass
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  targeted_venue = Venue.query.filter_by(id=venue_id).first()
  targeted_venue.name = request.form.get("name", targeted_venue.name)
  targeted_venue.genres = request.form.get("genres", targeted_venue.genres)
  targeted_venue.city = request.form.get("city", targeted_venue.city)
  targeted_venue.state = request.form.get("state", targeted_venue.state)
  targeted_venue.phone = request.form.get("phone", targeted_venue.phone)
  targeted_venue.facebook_link = request.form.get("facebook_link", targeted_venue.facebook_link)
  db.session.add(targeted_venue)
  db.session.commit()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  name = request.form.get("name", "")
  city = request.form.get("city", "")
  state = request.form.get("state", "")
  address = request.form.get("address", "")
  phone = request.form.get("phone", "")
  genres = request.form.get("genres", "")
  facebook_link = request.form.get("facebook_link", "")
  artist = Artist(
            name =  name,
            city =  city,
            state = state,
            genres = genres,
            phone = phone,
            facebook_link = facebook_link,
            )
  try:
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  all_shows = Show.query.all()
  data = [{"venue_id": item.id, 
           "venue_name": Venue.query.filter_by(id=item.venue_id).first().name,
           "artist_id": item.artist_id,
           "artist_name": Artist.query.filter_by(id=item.artist_id).first().name,
           "artist_image_link": Artist.query.filter_by(id=item.artist_id).first().image_link,
           "start_time": str(item.time)
          } for item in all_shows]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  artist_id = request.form.get("artist_id", "")
  venue_id = request.form.get("venue_id", "")
  time = request.form.get("start_time", "")
  try:
    show = Show(artist_id=artist_id, venue_id=venue_id, time=time)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    flash('An error occurred. Show could not be listed.')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
