#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import render_template, request, flash, redirect, url_for
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import Shows, Venue, Artist, db, app


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
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues(): 
  # shows all venues ordered by unique location
  venues = Venue.query.all()
  areas = []
  for area in Venue.query.distinct(Venue.city, Venue.state):
    all_venues = []
    for venue in venues:
      if venue.city == area.city and venue.state == area.state:
        all_venues.append({
          "id": venue.id,
          "name": venue.name,
        })
    areas.append({
      "city": area.city,
      "state": area.state,
      "venues": all_venues
    })

  return render_template('pages/venues.html', areas=areas);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # carries out a case insensitive search for any partial match in all venues
  query = request.form['search_term']
  actual_query = query.lower()
  venues=Venue.query.filter(Venue.name.ilike("%" + actual_query + "%"))
  response={
    "count": venues.count(),
    "data":venues.all()
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
     
  venue = Venue.query.get(venue_id)
  past_shows = []
  upcoming_shows = []

  all_past_shows = db.session.query(Shows).join(Venue).filter(Shows.venue_id==venue_id).filter(Shows.start_time<datetime.now()).all()
  for show in all_past_shows:
    artist = db.session.query(Artist).join(Shows).filter(Artist.id==show.artist_id).one()
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": str(show.start_time)
    })

  all_upcoming_shows = db.session.query(Shows).join(Venue).filter(Shows.venue_id==venue_id).filter(Shows.start_time>datetime.now()).all()
  for show in all_upcoming_shows:
    artist = db.session.query(Artist).join(Shows).filter(Artist.id==show.artist_id).one()
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": str(show.start_time)
    })

  data = {
    'id': venue.id,
    'name': venue.name,
    'city': venue.city,
    'state': venue.state,
    'address': venue.address,
    'phone': venue.phone,
    'genres': venue.genres,
    'image_link': venue.image_link,
    'facebook_link': venue.facebook_link,
    'website_link': venue.website_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(all_upcoming_shows),
    "past_shows": past_shows,
    "past_shows_count": len(all_past_shows),
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
  form = VenueForm()
  try:
      venue = Venue(name=form.name.data, 
      city=form.city.data, 
      state=form.state.data, 
      address=form.address.data, 
      phone=form.phone.data, 
      image_link=form.image_link.data, 
      facebook_link=form.facebook_link.data,
      website_link=form.website_link.data,
      seeking_talent=form.seeking_talent.data,
      seeking_description=form.seeking_description.data,
      genres=form.genres.data
      ) 
      exists=Venue.query.filter(Venue.name.ilike(venue.name)).count()
      if exists == 0:
        db.session.add(venue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + venue.name + ' was successfully listed!')
      else:
        raise Exception

  except:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
      db.session.rollback()

  finally:
      db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully deleted.')
  except:
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')
    db.session.rollback()
  finally:
    db.session.close()

  return None

#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # carries out a case insensitive search for any partial match in all artists
  query = request.form['search_term']
  actual_query = query.lower()
  artists=Artist.query.filter(Artist.name.ilike("%" + actual_query + "%"))
  response={
    "count": artists.count(),
    "data":artists.all()
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = Artist.query.get(artist_id)
  past_shows = []
  upcoming_shows = []
  past_shows_count = 0
  upcoming_shows_count = 0

  all_past_shows = db.session.query(Shows).join(Venue).filter(Shows.artist_id==artist_id).filter(Shows.start_time<datetime.now()).all()
  for show in all_past_shows:
    venue = db.session.query(Venue).join(Shows).filter(Venue.id==show.venue_id).one()
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": str(show.start_time)
    })

  all_upcoming_shows = db.session.query(Shows).join(Venue).filter(Shows.artist_id==artist_id).filter(Shows.start_time>datetime.now()).all()
  for show in all_upcoming_shows:
    venue = db.session.query(Venue).join(Shows).filter(Venue.id==show.venue_id).one()
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": str(show.start_time)
    })

  data = {
    'id': artist.id,
    'name': artist.name,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'genres': artist.genres,
    'image_link': artist.image_link,
    'facebook_link': artist.facebook_link,
    'website_link': artist.website_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(all_upcoming_shows),
    "past_shows": past_shows,
    "past_shows_count": len(all_past_shows),
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    try:
      form.populate_obj(artist)
      db.session.commit()

      # on successful db insert, flash success
      flash('Artist ' + artist.name + ' was successfully updated!')
    except Exception as e:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist could not be updated.')
      db.session.rollback()
      print(e)
    finally:
      db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))
      

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  try:
      form.populate_obj(venue)
      db.session.commit()

      # on successful db insert, flash success
      flash('Venue ' + venue.name + ' was successfully updated!')
  except:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + venue.name + ' could not be updated.')
      db.session.rollback()
  finally:
      db.session.close()
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
  form = ArtistForm() 
  try:
      artist = Artist(name=form.name.data, 
      city=form.city.data, 
      state=form.state.data,  
      phone=form.phone.data, 
      image_link=form.image_link.data, 
      facebook_link=form.facebook_link.data,
      website_link=form.website_link.data,
      seeking_venue=form.seeking_venue.data,
      seeking_description=form.seeking_description.data,
      genres=form.genres.data
      ) 
      # validates no duplicate artist can be created
      exists=Artist.query.filter(Artist.name.ilike(artist.name)).count()
      if exists == 0:
        db.session.add(artist)
        db.session.commit()

        # on successful db insert, flash success
        flash('Artist ' + artist.name + ' was successfully listed!')
      else:
        raise Exception

  except Exception as e:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist could not be listed.')
      db.session.rollback()
      print(e)

  finally:
      db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows

  upcoming_shows = []
  all_shows = Shows.query.all()

  for show in all_shows:
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)

    if show.start_time > datetime.now():
      upcoming_shows.append({
        "venue_id": venue.id,
        "venue_name": venue.name,
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(show.start_time)
      })

  return render_template('pages/shows.html', shows=upcoming_shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form = ShowForm()
  try:
    new_show = Shows(
      artist_id=form.artist_id.data,
      venue_id=form.venue_id.data,
      start_time=form.start_time.data
    )
    db.session.add(new_show)
    db.session.commit()
    
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except Exception as e:
    db.session.rollback()
    flash('Show was unable to be listed.')
    print(e)
  finally:
    db.session.close()
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
