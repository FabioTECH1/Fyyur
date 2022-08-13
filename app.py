#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from ast import keyword
from distutils.log import error
from email.policy import default
import json
from posixpath import split
from sre_parse import State
import sys
from time import strftime
from dateutil import parser
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import desc
from forms import *
from flask_migrate import Migrate

# SQLALCHEMY_TRACK_MODIFICATIONS = False
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)

app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venues', lazy=False) 

    def __repr__(self):
        return f'<Venue {self.id} {self.name} {self.city} {self.state} {self.address} {self.phone} {self.image_link} {self.facebook_link} {self.seeking_talent} {self.seeking_description}>'


class Artist(db.Model): 
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artists', lazy=False) 

    def __repr__(self):
        return f'<Artist {self.id} {self.name} {self.city} {self.state} {self.phone} {self.genres} {self.image_link} {self.facebook_link} {self.seeking_venue} {self.seeking_description}>'

class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)  
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)


    def __repr__(self):
        return f'<Show {self.id}, artist {self.artist_id}, venue {self.venue_id}, start_time {self.start_time} >'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  data = []
  venues = Venue.query.group_by(Venue.city,Venue.state,Venue.id).with_entities(Venue.city,Venue.state).order_by(Venue.id.desc()).limit(10)
  for venue in venues:
    venue_info = []
    filtered_venue = Venue.query.filter_by(state=venue.state,city=venue.city).all()

    for f_venue in filtered_venue:
      venue_info.append({
        'id': f_venue.id,
        'name':f_venue.name,
      })
    data.append({
      'city':venue.city,
      'state':venue.state,
      'venues':venue_info,
    })
  artists = Artist.query.order_by(Artist.id.desc()).limit(10)
  return render_template('pages/home.html', areas=data, artists=artists)


#  Venues
#  ----------------------------------------------------------------

# view venues
@app.route('/venues')
def venues():
  form = SearchForm()

  data = []
  venues = Venue.query.group_by(Venue.city,Venue.state).with_entities(Venue.city,Venue.state).all()
  for venue in venues:
    venue_info = []
    filtered_venue = Venue.query.filter_by(state=venue.state,city=venue.city).all()

    for f_venue in filtered_venue:
      num_upcoming_shows = Show.query.filter(Show.venue_id==f_venue.id, Show.start_time > datetime.now()).all()
      venue_info.append({
        'id': f_venue.id,
        'name':f_venue.name,
        'num_upcoming_shows':len(num_upcoming_shows)
      })
    data.append({
      'city':venue.city,
      'state':venue.state,
      'venues':venue_info,
    })

  return render_template('pages/venues.html', areas=data, form=form)

# search for venues 
@app.route('/venues/search', methods=['POST'])
def search_venues():
  form = SearchForm()
  
  search_term = request.form.get('search_term', '')
  city = request.form.get('city')
  state = request.form.get('state')

  if city and state:
    venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%'), Venue.city.ilike('%'+city+'%'), Venue.state==state).all()
  elif city:
    venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%'), Venue.city.ilike('%'+city+'%')).all()
  elif state:
    venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%'), Venue.state==state).all()
  else:
    venues = Venue.query.filter(Venue.name.ilike('%'+search_term+'%')).all()
  response={
    "count": len(venues),
    "data": venues
  }
  # return str(len(venues))
  return render_template('pages/search_venues.html', results=response, search_term=search_term, state=state, city=city, form=form)

# view venue info 
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    shows_past = Show.query.filter(Show.venue_id==venue.id, Show.start_time < datetime.now()).all()
    past_shows = []
    upcoming_shows = []
    for show_past in shows_past:
      artist = Artist.query.get(show_past.artist_id)
      past_shows.append({
        'artist_id': show_past.artist_id,
        'artist_name':artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(show_past.start_time)
      })
    shows_coming = Show.query.filter(Show.venue_id==venue.id, Show.start_time > datetime.now()).all()
    for show_coming in shows_coming:
      artist = Artist.query.get(show_coming.artist_id)
      upcoming_shows.append({
        'artist_id': show_coming.artist_id,
        'artist_name':artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(show_coming.start_time)
      })
    
    data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres.split(','),
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website_link,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      'upcoming_shows': upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }
  except:
    error = True
  finally:
    if error:
      return render_template('errors/404.html'), 404
    else:
      return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

# create venue view 
@app.route('/venues/create', methods=['GET'])
def create_venue_form():

  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

# create venue  
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  form = VenueForm(request.form)
  try:      
    venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, 
    address=form.address.data, genres=','.join(form.genres.data), image_link=form.image_link.data, 
    facebook_link=form.facebook_link.data, website_link=form.website_link.data, 
    seeking_talent=form.seeking_talent.data, seeking_description=form.seeking_description.data)

    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + form.name.data + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()
    return redirect(url_for('index'))

  
# delete venue 
@app.route('/venues/<venue_id>/delete', methods=['post'])
def delete_venue(venue_id):

  try:
    Show.query.filter_by(venue_id=venue_id).delete()
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' deleted successfully.')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')
  finally:
    db.session.close()
    return redirect(url_for('index'))

    

#  Artists
#  ----------------------------------------------------------------
# artists view 
@app.route('/artists')
def artists():
  form = SearchForm()
  data = Artist.query.all() 

  return render_template('pages/artists.html', artists=data, form=form)

# search artist
@app.route('/artists/search', methods=['POST'])
def search_artists():

  form = SearchForm()

  search_term = request.form.get('search_term', '')
  city = request.form.get('city')
  state = request.form.get('state')

  if city and state:
    artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%'), Artist.city.ilike('%'+city+'%'), Artist.state==state).all()
  elif city:
    artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%'), Artist.city.ilike('%'+city+'%')).all()
  elif state:
    artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%'), Artist.state==state).all()
  else:
    artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
  response={
    "count": len(artists),
    "data": artists
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term, state=state, city=city, form=form)

# show artist info 
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  error = False
  try:
    artist = Artist.query.get(artist_id)
    shows_past = Show.query.filter(Show.artist_id==artist.id, Show.start_time < datetime.now()).all()
    past_shows = []
    upcoming_shows = []
    for show_past in shows_past:
      venue = Venue.query.get(show_past.venue_id)
      past_shows.append({
        'venue_id': show_past.venue_id,
        'venue_name':venue.name,
        "venue_image_link": venue.image_link,
        "start_time": str(show_past.start_time)
      })
    shows_coming = Show.query.filter(Show.artist_id==artist.id, Show.start_time > datetime.now()).all()
    for show_coming in shows_coming:
      venue = Venue.query.get(show_past.venue_id)
      upcoming_shows.append({
        'venue_id': show_coming.venue_id,
        'venue_name':venue.name,
        "venue_image_link": venue.image_link,
        "start_time": str(show_coming.start_time)
      })
    
    data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres.split(','),
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website_link,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      'upcoming_shows': upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }
  except:
    error = True
  finally:
    if error:
      return render_template('errors/404.html'), 404
    else:
      return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
# update artist view 
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data=artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)

# update artist info 
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  try:
    form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)

    artist.name = form.name.data
    artist.genres = ','.join(form.genres.data)
    artist.city = form.city.data
    artist.state= form.state.data
    artist.phone = form.phone.data
    artist.website_link = form.website_link.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    artist.image_link = form.image_link.data
    db.session.commit()
    flash('Artist ' + form.name.data + ' updated successfully.')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
  finally:
    db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

# update venue view
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data=venue.name
  form.genres.data = venue.genres
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.address.data = venue.address
  form.website_link.data = venue.website_link
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link

  return render_template('forms/edit_venue.html', form=form, venue=venue)

# update venue info 
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  try:
    form = VenueForm(request.form)
    venue = Venue.query.get(venue_id)

    venue.name = form.name.data
    venue.genres = ','.join(form.genres.data)
    venue.city = form.city.data
    venue.state= form.state.data
    venue.phone = form.phone.data
    venue.address = form.address.data
    venue.website_link = form.website_link.data
    venue.facebook_link = form.facebook_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    venue.image_link = form.image_link.data
    db.session.commit()
    flash('Venue ' + form.name.data + ' updated successfully.')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
  finally:
    db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

# create artist view 
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

# create artist 
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  form = ArtistForm(request.form)
  try:      
    artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, 
    genres=','.join(form.genres.data), image_link=form.image_link.data, facebook_link=form.facebook_link.data, 
    website_link=form.website_link.data, seeking_venue=form.seeking_venue.data, seeking_description=form.seeking_description.data)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + form.name.data + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  finally:
    db.session.close()
    return redirect(url_for('index'))

# delete artist 
@app.route('/artists/<artist_id>/delete', methods=['post'])
def delete_artist(artist_id):

  try:
    Show.query.filter_by(artist_id=artist_id).delete()
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' deleted successfully.')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be deleted.')
  finally:
    db.session.close()
    return redirect(url_for('index'))



#  Shows
#  ----------------------------------------------------------------

# show shows 
@app.route('/shows')
def shows():

  data = []
  shows = Show.query.all()
  for show in shows:
    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)
    data.append({
      'id':show.id,
      'venue_id':show.venue_id,
      'venue_name':venue.name,
      'artist_id':show.artist_id,
      'artist_name':artist.name,
      'artist_image_link':artist.image_link,
      'start_time':str(show.start_time)
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

# create show
@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  form = ShowForm(request.form)
  try:
    show = Show(venue_id=form.venue_id.data, artist_id=form.artist_id.data, start_time=form.start_time.data)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
    return redirect(url_for('index'))


# delete show 
@app.route('/show/<id>/delete', methods=['post'])
def delete_show(id):

  try:
    show = Show.query.get(id)
    db.session.delete(show)
    print('abc')
    db.session.commit()
    flash('Show deleted successfully.')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be deleted.')
  finally:
    db.session.close()
    return redirect(url_for('shows'))


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

