## SI 364 - Winter 2018
## HW 3
#pip install psycopg2 
#pip3 install flask_script
####################
## Import statements
####################
import os
import urllib
import re
import datetime
import json
import urllib.request, urllib.parse, urllib.error
from urllib.request import Request, urlopen
import ssl
import requests
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms import validators
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.dialects.postgresql import JSON
from flask import flash
from migrate.versioning import api
#from flask_script import Manager
#from flask_migrate import Migrate, MigrateCommand

from flask_script import Manager, Shell # New

############################
# Application configurations
############################
app = Flask(__name__)
#app.debug = True
#app.use_reloader = True

app.config['SECRET_KEY'] = 'hard to guess string from si364'
## TODO 364: Create a database in postgresql in the code line below, and fill in your app's database URI. It should be of the format: postgresql://localhost/YOUR_DATABASE_NAME

## Your final Postgres database should be your uniqname, plus HW3, e.g. "jczettaHW3" or "maupandeHW3"

basedir = os.path.abspath(os.path.dirname(__file__))  # In case we need to reference the base directory of the application

#app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost:5432/hcyenhw3"
#https://blog.theodo.fr/2017/03/developping-a-flask-web-app-with-a-postresql-database-making-all-the-possible-errors/
#also add this line in pg_hba.conf file
# host  all  postgres  127.0.0.1/32  md5


app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/hcyenHW3"

#app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hcyenhw3"
##SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository') 
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

##################
### App setup ####
##################

#https://realpython.com/blog/python/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/
manager = Manager(app) # In order to use manager
#need to use PostgreSQL's psql to issue this command to create the database first -- create database hcyenHW3;
db = SQLAlchemy(app) # For database use

db.init_app(app)
#########################
#########################
######### Everything above this line is important/useful setup,
## not problem-solving.##
#########################
#########################

#########################
##### Set up Models #####
#########################
#from app import views, models

#from models import Result


## TODO 364: Set up the following Model classes, as described, with the respective fields (data types).

## The following relationships should exist between them:
# Tweet:User - Many:One

# - Tweet
## -- id (Integer, Primary Key)
## -- text (String, up to 280 chars)
## -- user_id (Integer, ID of user posted -- ForeignKey)

## Should have a __repr__ method that returns strings of a format like:
#### {Tweet text...} (ID: {tweet id})
#https://pyformat.info
#https://www.digitalocean.com/community/tutorials/how-to-use-string-formatters-in-python-3
class Tweet(db.Model):
	__tablename__ = 'tweets'
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.String(280))
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	def __repr__(self):
		#return "{Tweet text %r} % (ID: {tweet id})".format(self.text, self.id)
		return "Tweet text:{text}(ID:{id})".format(self.text, self.id)


# - User
## -- id (Integer, Primary Key)
## -- username (String, up to 64 chars, Unique=True)
## -- display_name (String, up to 124 chars)
## ---- Line to indicate relationship between Tweet and User tables (the 1 user: many tweets relationship)

## Should have a __repr__ method that returns strings of a format like:
#### {username} | ID: {id}
class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	display_name = db.Column(db.String(124))
	tweets = db.relationship('Tweet', backref='User', lazy='dynamic')

	def __repr__(self):
		return "{username} | ID: {id}".format(self.username, self.id)
		#return '<User %r>' % (self.username)


#migrate = Migrate(app, db)
#manager = Manager(app)
#manager.add_command('db', MigrateCommand)
########################
##### Set up Forms #####
########################

# TODO 364: Fill in the rest of the below Form class so that someone running this web app will be able to fill in information about tweets they wish existed to save in the database:

## -- text: tweet text (Required, should not be more than 280 characters)
## -- username: the twitter username who should post it (Required, should not be more than 64 characters)
## -- display_name: the display name of the twitter user with that username (Required, + set up custom validation for this -- see below)

#http://wtforms.simplecodes.com/docs/0.6/validators.html
def validate_username(form, field):
	if (field.data).startswith("@"):
		raise ValidationError("User Name could not start with @")

def validate_display_name(form, field):
	if not " " in (field.data):
		raise ValidationError("Display name MUST be at least 2 words")

class TweetForm(FlaskForm):
	text = StringField("Enter the text of the tweet (no more than 280 chars):", [validators.required(), validators.length(max=280)])
	username = StringField('Enter the username of the twitter user (no "@"!):', [validators.required(), validators.length(max=64), validate_username ])
	display_name = StringField("Enter the display name for the twitter user (must be at least 2 words):", [validators.required(), validate_display_name])
	submit = SubmitField("Submit")

	
# HINT: Check out index.html where the form will be rendered to decide what field names to use in the form class definition

# TODO 364: Set up custom validation for this form such that:
# - the twitter username may NOT start with an "@" symbol (the template will put that in where it should appear)
# - the display name MUST be at least 2 words (this is a useful technique to practice, even though this is not true of everyone's actual full name!)

# TODO 364: Make sure to check out the sample application linked in the readme to check if yours is like it!
#http://sample364hw3.herokuapp.com/

###################################
##### Routes & view functions #####
###################################

## Error handling routes - PROVIDED
@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500

#############
## Main route
#############

## TODO 364: Fill in the index route as described.

# A template index.html has been created and provided to render what this route needs to show -- YOU just need to fill in this view function so it will work.
# Some code already exists at the end of this view function -- but there's a bunch to be filled in.
## HINT: Check out the index.html template to make sure you're sending it the data it needs.
## We have provided comment scaffolding. Translate those comments into code properly and you'll be all set!

# NOTE: The index route should:
# - Show the Tweet form.
# - If you enter a tweet with identical text and username to an existing tweet, it should redirect you to the list of all the tweets and a message that you've already saved a tweet like that.
# - If the Tweet form is entered and validates properly, the data from the form should be saved properly to the database, and the user should see the form again with a message flashed: "Tweet successfully saved!"
# Try it out in the sample app to check against yours!

#https://books.google.com/books?id=NdZOCwAAQBAJ&pg=PA53&lpg=PA53&dq=wtforms+custom+validators&source=bl&ots=nx6R5ZLYGN&sig=6YQ00RZLqa2gpSYwdpwo730Dm44&hl=en&sa=X&ved=0ahUKEwjq6_uxjJDZAhUEca0KHSyMDYE4ChDoAQg5MAM#v=onepage&q=wtforms%20custom%20validators&f=false

@app.route('/', methods=['GET', 'POST'])
def index():
	# Initialize the form
	form = TweetForm()
	# Get the number of Tweets
	num_tweets = Tweet.query.count()
	# If the form was posted to this route,
	## Get the data from the form
	if form.validate_on_submit():
		if request.method == 'POST':
			if not request.form['text'] or not request.form['username'] or not request.form['display_name']:
				flash('Please enter all the fields', 'error')
			else:
				#user = User.query.filter_by(username=request.form['username']).first()
				#tweet=Tweet.query.filter_by(text=request.form['text'], user_id=User.id).first()
				user = User.query.filter_by(username=form.username.data).first()
				

				if user is None:
					#https://stackoverflow.com/questions/30032078/typeerror-init-takes-1-positional-argument-but-3-were-given
					user = User(username=form.username.data, display_name=form.display_name.data)
					db.session.add(user)
					db.session.commit()

					tweet = Tweet(text=form.text.data, user_id=user.id)
					db.session.add(tweet)
					db.session.commit()
					flash('This tweet is successfully added')
				else:
					#user = User(username=form.username.data, display_name=form.display_name.data)
					tweet=Tweet.query.filter_by(text=form.text.data, user_id=user.id).first()

					if not tweet is None:
						flash('That tweet already exists from that user!')
						return redirect(url_for('see_all_tweets'))
					else:
						tweet = Tweet(text=form.text.data, user_id=user.id)
						db.session.add(tweet)
						db.session.commit()
						flash('This tweet is successfully added')
					#http://flask-sqlalchemy.pocoo.org/2.3/queries/

					#u = User.query.filter_by(username=request.form['username']).first()
				
					#tweet=Tweet.query.filter_by(text=request.form['text'], user_id=user.id).first()
		 
					#tweet = Tweet(request.form['text'], author=user)
					#tweet = tweets(request.form['text'], author=user) #p = Post(body='my first post!', author=u)
				
					'''
					tweet = Tweet(text=form.text.data, user_id=user.id)
					db.session.add(tweet)
					db.session.commit()
					flash('This tweet is successfully added')
					'''			
				#return redirect('templates\index.html')
				#return render_template('index.html', form = form, num_tweets= num_tweets, username='', text='',display_name='')
				# if you use render_template, the text fields' values won't be cleared out.
				return redirect(url_for('index'))
			## Find out if there's already a user with the entered username
			## If there is, save it in a variable: user
			## Or if there is not, then create one and add it to the database

			## If there already exists a tweet in the database with this text and this user id (the id of that user variable above...) ## Then flash a message about the tweet already existing
			## And redirect to the list of all tweets

			## Assuming we got past that redirect,
			## Create a new tweet object with the text and user id
			## And add it to the database
			## Flash a message about a tweet being successfully added
			## Redirect to the index page

			# PROVIDED: If the form did NOT validate / was not submitted
	else:
		errors = [v for v in form.errors.values()]
		if len(errors) > 0:
			flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
		return render_template('index.html', form = form, num_tweets= num_tweets) # TODO 364: Add more arguments to the render_template invocation to send data to index.html

@app.route('/all_tweets')
def see_all_tweets():
	#pass # Replace with code
	# TODO 364: Fill in this view function so that it can successfully render the template all_tweets.html, which is provided.
	# HINT: Careful about what type the templating in all_tweets.html is expecting! It's a list of... not lists, but...
	# HINT #2: You'll have to make a query for the tweet and, based on that, another query for the username that goes with it...
	#https://stackoverflow.com/questions/1958219/convert-sqlalchemy-row-object-to-python-dict
	alltweets = Tweet.query.all()
	all_tweets = [(t.text, User.query.filter_by(id=t.user_id).first().username) for t in alltweets]
	#dict={}
	#tup()
	#below works too
	'''
	all_tweets=[]
	#tup=();
	for tw in alltweets:
		user = User.query.filter_by(id = tw.user_id).first()
		username=user.username
		#dict[tw.text] = username
		#all_tweets.append(dict)
		tup=(tw.text, username)
		#https://stackoverflow.com/questions/31175223/append-a-tuple-to-a-list-whats-the-difference-between-two-ways
		#all_tweets.append(tup((tw.text, username)))
		all_tweets.append(tup)
		#print(all_tweets)
	'''
	return render_template('all_tweets.html', all_tweets=all_tweets)

@app.route('/all_users')
def see_all_users():
	#pass # Replace with code
	# TODO 364: Fill in this view function so it can successfully render the template all_users.html, which is provided.
	allusers = User.query.all()
	return render_template('all_users.html', users=allusers)
# TODO 364
# Create another route (no scaffolding provided) at /longest_tweet with a view function get_longest_tweet (see details below for what it should do)
@app.route('/longest_tweet')
def get_longest_tweet():
	alltweets = Tweet.query.all()
	num_tweets = Tweet.query.count()
	print(num_tweets)
	twlist=[]
	#https://stackoverflow.com/questions/873327/pythons-most-efficient-way-to-choose-longest-string-in-list
	count=0
	for tw in alltweets:
		#str=(tw.text).replace(" ", "")

		if (len(tw.text) - (tw.text).count(' ')) >= count:  #cannot be > and has to be >= so it will include the tweet with the same length
			count = (len(tw.text) - (tw.text).count(' '))
			str=(tw.text)
			twlist.append(str)

		#twlist.append(str)
	#https://stackoverflow.com/questions/4659524/how-to-sort-by-length-of-string-followed-by-alphabetical-order
	#for i in sorted(twlist, key=len, reverse=True):
	#	print(i)

	twlist.sort() # sorts normally by alphabetical order
	twlist.sort(key=len, reverse=True) # sorts by descending length
	#twlist.sort(key=lambda item: (-len(item), item))
	print(twlist)
	longest_tweet=twlist[0]
	print(longest_tweet)
	t = Tweet.query.filter_by(text=longest_tweet).first()
	print(type(t))
	user = User.query.filter_by(id= t.user_id).first()
	username = user.username
	display_name = user.display_name
	
	return render_template('longest_tweet.html', all_tweets=alltweets, longest_tweet=longest_tweet, username=username, display_name=display_name )
# TODO 364
# Create a template to accompany it called longest_tweet.html that extends from base.html.

# NOTE:
# This view function should compute and render a template (as shown in the sample application) that shows the text of the tweet currently saved in the database which has the most NON-WHITESPACE characters in it, and the username AND display name of the user that it belongs to.
# NOTE: This is different (or could be different) from the tweet with the most characters including whitespace!
# Any ties should be broken alphabetically (alphabetically by text of the tweet). HINT: Check out the chapter in the Python reference textbook on stable sorting.
# Check out /longest_tweet in the sample application for an example.

# HINT 2: The chapters in the Python reference textbook on:
## - Dictionary accumulation, the max value pattern
## - Sorting
# may be useful for this problem!


if __name__ == '__main__':
	db.create_all() # Will create any defined models when you run the application
	manager.run()
	app.run(use_reloader=True,debug=True) # The usual
