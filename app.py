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
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    genres = db.Column(db.ARRAY(db.String()))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String())
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='venues', lazy=True)

    def __repr__(self):
      return f'Venue <{self.id}, {self.name}>'


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='artists', lazy=True)

    def __repr__(self):
      return f'Artist <{self.id}, {self.name}>'

class Show(db.Model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
  start_time = db.Column(db.DateTime)

  def __repr__(self):
    return f'Show <{self.id}, {self.venue_id}, {self.artist_id}>'

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
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []

  cityState = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)

  for location in cityState:
    venues= db.session.query(Venue.id, Venue.name).filter(Venue.city == location[0]).filter(Venue.state == location[1])
    data.append({'city' : location[0],
                'state' : location[1],
                'venues' : venues})

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  term = request.form['search_term']
  search = "%{}%".format(term)
  venues = Venue.query.filter(Venue.name.ilike(search)).all()

  response = {}
  response['count'] = len(venues)
  data = []
  for venue in venues:
    data.append({'id' : venue.id,
                'name' : venue.name})
  response['data'] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.get(venue_id)
  shows = Show.query.filter(Show.venue_id == venue_id).all()
  past_shows = []
  upcoming_shows = []

  for show in shows:
    artist = Artist.query.filter(Artist.id == show.artist_id).one()
    show_data = {
      'artist_id' : artist.id,
      'artist_name' : artist.name,
      'artist_image_link' : artist.image_link,
      'start_time' : str(show.start_time)
    }

    if show.start_time < datetime.now():
      past_shows.append(show_data)
    else:
      upcoming_shows.append(show_data)
  
  data = {
    'id' : venue.id,
    'name' : venue.name,
    'genres' : venue.genres,
    'address' : venue.address,
    'city' : venue.city,
    'state' : venue.state,
    'phone' : venue.phone,
    'website' : venue.website,
    'facebook_link' : venue.facebook_link,
    'seeking_talent' : venue.seeking_talent,
    'seeking_description' : venue.seeking_description,
    'image_link' : venue.image_link,
    'past_shows' : past_shows,
    'upcoming_shows' : upcoming_shows,
    'past_shows_count' : len(past_shows),
    'upcoming_shows_count' : len(upcoming_shows)
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
  error = False
  try:
    venue = Venue(name=request.form['name'],
                    city=request.form['city'],
                    state=request.form['state'],
                    address=request.form['address'],
                    phone=request.form['phone'],
                    genres=request.form.getlist('genres'),
                    image_link=request.form['image_link'],
                    facebook_link=request.form['facebook_link'],
                    website=request.form['website'],
                    seeking_description=request.form['seeking_description'])
    if 'seeking_artist' in request.form:
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False

    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data=[]
  artists = Artist.query.all()
  for artist in artists:
    data.append({'id' : artist.id,
              'name' : artist.name})

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  term = request.form['search_term']
  search = "%{}%".format(term)
  artists = Artist.query.filter(Artist.name.ilike(search)).all()

  response = {}
  response['count'] = len(artists)
  data = []
  for artist in artists:
    data.append({'id' : artist.id,
                'name' : artist.name})
  response['data'] = data

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  artist = Artist.query.get(artist_id)
  shows = Show.query.filter(Show.artist_id == artist_id).all()
  past_shows = []
  upcoming_shows = []

  for show in shows:
    venue = Venue.query.filter(Venue.id == show.venue_id).one()
    show_data = {
      'venue_id' : venue.id,
      'venue_name' : venue.name,
      'venue_image_link' : venue.image_link,
      'start_time' : str(show.start_time)
    }

    if show.start_time < datetime.now():
      past_shows.append(show_data)
    else:
      upcoming_shows.append(show_data)
    
  data = {
    'id' : artist.id,
    'name' : artist.name,
    'genres' : artist.genres,
    'city' : artist.city,
    'state' : artist.state,
    'phone' : artist.phone,
    'website' : artist.website,
    'facebook_link' : artist.facebook_link,
    'seeking_venue' : artist.seeking_venue,
    'seeking_description' : artist.seeking_description,
    'image_link' : artist.image_link,
    'past_shows' : past_shows,
    'upcoming_shows' : upcoming_shows,
    'past_shows_count' : len(past_shows),
    'upcoming_shows_count' : len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  selectedArtist = Artist.query.get(artist_id)
  artist={
    "id": selectedArtist.id,
    "name": selectedArtist.name,
    "genres": selectedArtist.genres,
    "city": selectedArtist.city,
    "state": selectedArtist.state,
    "phone": selectedArtist.phone,
    "website": selectedArtist.website,
    "facebook_link": selectedArtist.facebook_link,
    "seeking_venue": selectedArtist.seeking_venue,
    "seeking_description": selectedArtist.seeking_description,
    "image_link": selectedArtist.image_link
  }

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    updated = {'name':request.form['name'],
                'city':request.form['city'],
                'state':request.form['state'],
                'phone':request.form['phone'],
                'genres':request.form.getlist('genres'),
                'image_link':request.form['image_link'],
                'facebook_link':request.form['facebook_link'],
                'website':request.form['website'],
                'seeking_description':request.form['seeking_description']}
    if 'seeking_venue' in request.form:
      updated['seeking_venue'] = True
    else:
      updated['seeking_venue'] = False
    print(updated)
    db.session.query(Artist).filter(Artist.id == artist_id).update(updated)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  selectedVenue = Venue.query.get(venue_id)
  venue={
    "id": selectedVenue.id,
    "name": selectedVenue.name,
    "genres": selectedVenue.genres,
    "address": selectedVenue.address,
    "city": selectedVenue.city,
    "state": selectedVenue.state,
    "phone": selectedVenue.phone,
    "website": selectedVenue.website,
    "facebook_link": selectedVenue.facebook_link,
    "seeking_talent": selectedVenue.seeking_talent,
    "seeking_description": selectedVenue.seeking_description,
    "image_link": selectedVenue.image_link
  }

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    updated = {'name':request.form['name'],
                'city':request.form['city'],
                'state':request.form['state'],
                'address':request.form['address'],
                'phone':request.form['phone'],
                'genres':request.form.getlist('genres'),
                'image_link':request.form['image_link'],
                'facebook_link':request.form['facebook_link'],
                'website':request.form['website'],
                'seeking_description':request.form['seeking_description']}
    if 'seeking_artist' in request.form:
      updated['seeking_talent'] = True
    else:
      updated['seeking_talent'] = False

    db.session.query(Venue).filter(Venue.id == venue_id).update(updated)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  try:
    artist = Artist(name=request.form['name'],
                    city=request.form['city'],
                    state=request.form['state'],
                    phone=request.form['phone'],
                    genres=request.form.getlist('genres'),
                    image_link=request.form['image_link'],
                    facebook_link=request.form['facebook_link'],
                    website=request.form['website'],
                    seeking_description=request.form['seeking_description'])
    if 'seeking_venue' in request.form:
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False

    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = []
  shows = Show.query.all()

  for show in shows:
    data.append({'venue_id' : show.venues.id,
                  'venue_name' : show.venues.name,
                  'artist_id' : show.artists.id,
                  'artist_name' : show.artists.name,
                  'artist_image_link' : show.artists.image_link,
                  'start_time' : str(show.start_time)})
                  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  try:
    show = Show(venue_id=request.form['venue_id'],
                artist_id=request.form['artist_id'],
                start_time=request.form['start_time'])

    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  
  if error:
    flash('An error occurred. Show could not be listed.')
  else:
    flash('Show was successfully listed!')

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
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
