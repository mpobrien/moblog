from blog import app
from flask import Flask
from flask import render_template, request, jsonify, g, redirect, url_for, session, abort, flash
import re, os, sys, json
from markdown import Markdown
from gfm import gfm
from forms import NewPostForm, EditPostForm, LoginForm
from pymongo.objectid import ObjectId
from functools import wraps

from pymongo import Connection
from datetime import datetime
from flaskext.oauth import OAuth

db = Connection().blog

oauth = OAuth()

twitter = oauth.remote_app('twitter',
    # unless absolute urls are used to make requests, this will be added
    # before all URLs.  This is also true for request_token_url and others.
    base_url='http://api.twitter.com/1/',
    # where flask should look for new request tokens
    request_token_url='https://api.twitter.com/oauth/request_token',
    # where flask should exchange the token with the remote application
    access_token_url='https://api.twitter.com/oauth/access_token',
    # twitter knows two authorizatiom URLs.  /authorize and /authenticate.
    # they mostly work the same, but for sign on /authenticate is
    # expected because this will give the user a slightly different
    # user interface on the twitter side.
    authorize_url='http://api.twitter.com/oauth/authenticate',
    # the consumer keys from the twitter application registry.
    consumer_key='kZCO5WpquMV91pogSohU2A',
    consumer_secret='433lGvyWDpkziQwCGNIkFi38v7JQN0skxkkruGa7MA'
)


def admins_only(f):#{{{
  @wraps(f)
  def decorated_function(*args, **kwargs):
    print g.user, app.admins
    if g.user is None or g.user['name'] not in app.admins:
      abort(404)
    return f(*args, **kwargs)
  return decorated_function#}}}

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        try:
            oid = ObjectId(session['user_id'])
        except:
            return
        g.user = db.users.find_one({"_id":oid})

@twitter.tokengetter
def get_twitter_token():
    """This is used by the API to look for the auth token and secret
    it should use for API calls.  During the authorization handshake
    a temporary set of token and secret is used, but afterwards this
    function has to return the token and secret.  If you don't want
    to store this in the database, consider putting it into the
    session instead.
    """
    user = g.user
    if user is not None:
        return user.oauth_token, user.oauth_secret



@app.template_filter()
def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    now = datetime.utcnow()
    diff = now - dt

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:

        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default


@app.route('/login')
def login():
    """Calling into authorize will cause the OpenID auth machinery to kick
    in.  When all worked out as expected, the remote application will
    redirect back to the callback URL provided.
    """
    return twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You were signed out')
    return redirect(request.referrer or url_for('home'))

@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    """Called after authorization.  After this function finished handling,
    the OAuth information is removed from the session again.  When this
    happened, the tokengetter from above is used to retrieve the oauth
    token and secret.

    Because the remote application could have re-authorized the application
    it is necessary to update the values in the database.

    If the application redirected back after denying, the response passed
    to the function will be `None`.  Otherwise a dictionary with the values
    the application submitted.  Note that Twitter itself does not really
    redirect back unless the user clicks on the application name.
    """
    next_url = request.args.get('next') or url_for('home')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    if resp['screen_name'] not in app.admins: # a non-admin twitter user tried to log in.
        return redirect(url_for('home'))

    user = db.users.find_one({"name":resp['screen_name']})

    # user never signed on
    if user is None:
        uid = db.users.insert({"name":resp['screen_name'],
                               "oauth_token":resp['oauth_token'],
                               "oauth_token_secret":resp['oauth_token_secret']},
                               safe=True)
    else:
        uid = user['_id']

    session['user_id'] = str(uid)
    flash('You were signed in')
    return redirect(next_url)

@app.route("/")
def home():
  posts = db.posts.find().sort("created_at", -1)
  return render_template("posts.html", posts=posts)

@app.route("/edit/<post_id>", methods=["GET", "POST"])
@admins_only
def edit(post_id):
    try:
        oid = ObjectId(post_id)
    except:
        return redirect(url_for("newpost"))
    post = db.posts.find_one({"_id":oid})
    if request.method == 'GET':
        form = EditPostForm()
        form.post_id.data = post_id
        form.title.data = post['title']
        form.content.data = post['body']
        return render_template("write.html", form=form, post_id=post_id)
    else:
        form = NewPostForm(request.form)
        if form.validate():
            title = form.title.data
            body = form.content.data
            md = Markdown()
            html = md.convert(gfm(body))
            db.posts.update({"_id":oid}, {"$set" :{"title":title, "body":body, "html":html}})
            return redirect(url_for("home"))
        else:
            return render_template("write.html", form=form, post_id=post_id)

@admins_only
@app.route("/write", methods=["GET", "POST"])
def newpost():
    if request.method == 'GET':
        return render_template("write.html", form=NewPostForm(), mode="new")
    else:
        form = NewPostForm(request.form)
        if form.validate():
            title = form.title.data
            body = form.content.data
            md = Markdown()
            html = md.convert(gfm(body))
            db.posts.insert({"title":title, "body":body, "html":html, "created_at":datetime.now()})
            return redirect(url_for("home"))
        else:
            return render_template("write.html", form=form, mode="new")
