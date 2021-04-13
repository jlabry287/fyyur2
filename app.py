#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request, Response,
    flash, redirect,
    url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import db, Venue, Artist, Show
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    # date = dateutil.parser.parse(value)
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value

    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
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
    all_locations = Venue.query.with_entities(
        Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    areas = []
    venue_data = []
    print(all_locations)
    for location in all_locations:
        matching_venues = Venue.query.filter_by(
            state=location.state).filter_by(city=location.city).all()
        area = {
            "city": location.city,
            "state": location.state,
            "venues": []
        }
        for venue in matching_venues:
            area["venues"].append({
                "id": venue.id,
                "name": venue.name,
                "upcoming_shows_count": len(db.session.query(Show)
                                            .filter(Show.start_time > datetime
                                            .now()).all())
            })
            areas.append(area)
    return render_template('pages/venues.html', areas=areas)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    results = db.session.query(Venue).filter(
        Venue.name.ilike(f'%{search_term}%')).all()
    data = []

    for result in results:
        data.append({
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": len(db.session.query(Show)
                                      .filter(Show.venue_id == result.id)
                                      .filter(Show.start_time > datetime
                                              .now()).all())
        })

    response = {
        "count": len(results),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    if not venue:
        return redirect(url_for('index'))
    else:
        now = datetime.now()
        get_upcoming_shows = db.session.query(Show).join(Artist).filter(
            Show.venue_id == venue_id).filter(Show.start_time > now).all()
        upcoming_shows = []
        for show in get_upcoming_shows:
            upcoming_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": show.start_time
            })
        get_past_shows = db.session.query(Show).join(Artist).filter(
            Show.venue_id == venue_id).filter(Show.start_time < now).all()
        past_shows = []
        for show in get_past_shows:
            past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.Artist.name,
                "artist_image_link": show.Artist.image_link,
                "start_time": show.start_time
            })

        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website_link": venue.website_link,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": len(upcoming_shows),
            "past_shows": past_shows,
            "past_shows_count": len(past_shows)
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
    error = False
    try:
        name = form.name.data
        city = form.city.data
        state = form.state.data
        address = form.address.data
        phone = form.phone.data
        genres = form.genres.data
        seeking_talent = form.seeking_talent.data
        seeking_description = form.seeking_description.data
        image_link = form.image_link.data
        website_link = form.website_link.data
        facebook_link = form.facebook_link.data

        venue = Venue(name=name, city=city, state=state, address=address,
                      phone=phone, genres=genres, image_link=image_link,
                      facebook_link=facebook_link, website_link=website_link,
                      seeking_talent=seeking_talent,
                      seeking_description=seeking_description)

        db.session.add(venue)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(e)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be created.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(e)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue could not be deleted.')
    else:
        flash('Venue was successfully deleted!')
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = db.session.query(Artist).all()

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    results = db.session.query(Artist).filter(
        Artist.name.ilike(f'%{search_term}%')).all()
    data = []

    for result in results:
        data.append({
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": len(db.session.query(Show)
                                      .filter(Show.artist_id == result.id)
                                      .filter(Show.start_time > datetime.now())
                                      .all())
        })

    response = {
        "count": len(results),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)

    if not artist:
        return redirect(url_for('index'))
    else:
        now = datetime.now()
        get_upcoming_shows = db.session.query(Show).join(Venue).filter(
            Show.artist_id == artist_id).filter(Show.start_time > now).all()
        upcoming_shows = []
        for show in get_upcoming_shows:
            upcoming_shows.append({
                "venue_id": show.venue_id,
                "venue_name": show.Venue.name,
                "venue_image_link": show.Venue.image_link,
                "start_time": show.start_time
            })
        get_past_shows = db.session.query(Show).join(Venue).filter(
            Show.artist_id == artist_id).filter(Show.start_time < now).all()
        past_shows = []
        for show in get_past_shows:
            past_shows.append({
                "venue_id": show.venue_id,
                "venue_name": show.Venue.name,
                "venue_image_link": show.Venue.image_link,
                "start_time": show.start_time
            })
        data = {
            "id": artist.id,
            "name": artist.name,
            "genres": artist.genres,
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website_link": artist.website_link,
            "facebook_link": artist.facebook_link,
            "seeking_talent": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": len(upcoming_shows),
            "past_shows": past_shows,
            "past_shows_count": len(past_shows)
        }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_load = Artist.query.get(artist_id)

    form.name.data = artist_load.name
    form.city.data = artist_load.city
    form.state.data = artist_load.state
    form.phone.data = artist_load.phone
    form.genres.data = artist_load.genres
    form.facebook_link.data = artist_load.facebook_link
    form.image_link.data = artist_load.image_link
    form.website_link.data = artist_load.website_link
    form.seeking_venue.data = artist_load.seeking_venue
    form.seeking_description.data = artist_load.seeking_description

    return render_template('forms/edit_artist.html', form=form,
                           artist=artist_load)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    error = False

    try:
        artist = Artist.query.get(artist_id)
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        artist.image_link = form.image_link.data
        artist.website_link = form.website_link.data
        artist.facebook_link = form.facebook_link.data

        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(e)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be updated.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue_load = Venue.query.get(venue_id)

    form.name.data = venue_load.name
    form.city.data = venue_load.city
    form.state.data = venue_load.state
    form.address.data = venue_load.address
    form.phone.data = venue_load.phone
    form.image_link.data = venue_load.image_link
    form.genres.data = venue_load.genres
    form.facebook_link.data = venue_load.facebook_link
    form.website_link.data = venue_load.website_link
    form.seeking_talent.data = venue_load.seeking_talent
    form.seeking_description.data = venue_load.seeking_description

    return render_template('forms/edit_venue.html', form=form,
                           venue=venue_load)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    error = False

    try:
        venue = Venue.query.get(venue_id)
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.image_link = form.image_link.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.website_link = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(e)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be updated.')
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
    form = ArtistForm()
    error = False

    try:
        name = form.name.data
        city = form.city.data
        state = form.state.data
        phone = form.phone.data
        genres = form.genres.data
        seeking_venue = form.seeking_venue.data
        seeking_description = form.seeking_description.data
        image_link = form.image_link.data
        website_link = form.website_link.data
        facebook_link = form.facebook_link.data

        artist = Artist(name=name, city=city, state=state, phone=phone,
                        genres=genres, image_link=image_link,
                        facebook_link=facebook_link, website_link=website_link,
                        seeking_venue=seeking_venue,
                        seeking_description=seeking_description)

        db.session.add(artist)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        print(e)
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be created.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    get_shows = db.session.query(Show).join(Artist).join(Venue).all()

    for show in get_shows:
        data.append({
            "artist_id": show.Artist.id,
            "artist_name": show.Artist.name,
            "artist_image_link": show.Artist.image_link,
            "venue_id": show.Venue.id,
            "venue_name": show.Venue.name,
            "start_time": show.start_time
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()
    error = False

    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    try:
        create_show = Show(artist_id=artist_id,
                           venue_id=venue_id, start_time=start_time)
        db.session.add(create_show)
        db.session.commit()
    except Exception as e:
        error = True
        print(e)
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
