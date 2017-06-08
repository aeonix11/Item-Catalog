from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog_database.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Google login
# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # abra = "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    print "fucking name %s" % data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response
# End Google signin
# JSON
# JSON APIs to view Categories and Item Information


@app.route('/<int:category_id>/item/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/category/JSON')
def categoryJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])

# Routes

# Show all categories and latest items arraged by entry starting with most recent


@app.route('/')
@app.route('/home/')
def showHome():
    category = session.query(Category).order_by(asc(Category.name))
    category_len = session.query(Category).count()
    if category_len == 0:
        flash("There are no categories to display")
    latest_items = session.query(Item).join(Category, Item.category_id == Category.id).order_by(Item.date.desc()).limit(10)
    latest_item_len = session.query(Item).count()
    category_name = [None] * latest_item_len
    if latest_item_len == 0:
        flash("There are no items to display")

    if 'username' not in login_session:
        return render_template('publicHome.html', categories=category, latest_items=latest_items, category_name=category_name)
    else:
        return render_template('home.html', categories=category, latest_items=latest_items, category_name=category_name)

# Show a Category item list


@app.route('/category/<string:category_name>/')
@app.route('/category/<string:category_name>/items/')
def showItems(category_name):
    # Category list
    category = session.query(Category).order_by(asc(Category.name))
    category_len = session.query(Category).count()
    if category_len == 0:
        flash("There are no categories to display")

    # Selected Category
    selected_category_name = session.query(Category).filter_by(name=category_name).one()
    number = 2
    print category_name
    # creator = getUserInfo(category_name.user_id)

    category_id = selected_category_name.id
    # Selected Category Items
    items = session.query(Item).filter_by(category_id=category_id).all()
    item_count = session.query(Item).filter_by(category_id=category_id).count()
    if item_count == 0:
        flash("There is no items to display!")

    if 'username' not in login_session:
        return render_template('publicCategoryItems.html', item_count=item_count, items=items, categories=category, selected_category_name=selected_category_name)
    else:
        return render_template('categoryItems.html', item_count=item_count, items=items, categories=category, selected_category_name=selected_category_name)


# Item Description
@app.route('/category/<int:item_id>/')
@app.route('/category/<int:item_id>/description/')
def showItemDesc(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    category_name = session.query(Category).filter_by(id=item.category_id).one()
    return render_template('itemDescription.html', item=item, category_name=category_name.name)

# Create a new category


@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showHome'))
    else:
        return render_template('newCategory.html')


# Create a new item
@app.route('/newItem', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    category_list = session.query(Category).all()
    if request.method == 'POST':

        user_id = login_session['user_id']
        # Validation
        if request.form['title']:
            title = request.form['title']
        else:
            flash("Please enter a title")
            return redirect(url_for('newItem'))

        if request.form['description']:
            description = request.form['description']
        else:
            flash("Please enter a Description")
            return redirect(url_for('newItem'))

        if request.form['category_name']:
            category_name = request.form['category_name']
            category = session.query(Category).filter_by(name=category_name).one()
            category_id = category.id

        newItem = Item(title=title, description=description, category_id=category_id, user_id=user_id)
        session.add(newItem)
        session.commit()
        flash('New %s Item Successfully Created' % (newItem.title))
        return redirect(url_for('showHome'))
    else:
        return render_template('newItem.html', categories=category_list)

# Edit a item


@app.route('/category/<string:category_name>/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id, category_name):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != editedItem.user_id:
        flash("You cannot edit what you did not create.")
        return redirect(url_for('showItemDesc', item_id=editedItem.id))

    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
        else:
            flash("Please enter a title")
            return redirect(url_for('editItem', item_title=item_title, category_name=category_name))

        if request.form['description']:
            editedItem.description = request.form['description']
        else:
            flash("Please enter a Description")
            return redirect(url_for('editItem', item_title=item_title, category_name=category_name))
        if request.form['category_name']:
            cat_name = request.form['category_name']
            category_validation = session.query(Category).all()
            cat_found = 0
            for cat in category_validation:
                if cat.name == cat_name:
                    cat_found = 1
            if cat_found == 1:
                category = session.query(Category).filter_by(name=cat_name).one()
                category_id = category.id
                editedItem.category_id = category_id
            else:
                flash("Category name does not exist")
                return redirect(url_for('editItem', item_id=item_id, category_name=category_name))
            session.add(editedItem)
            session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showItemDesc', item_id=editedItem.id))
    else:
        return render_template('editItem.html',  item=editedItem, category_name=category_name)

# Select a category to delete


@app.route('/Category/select/delete', methods=['GET', 'POST'])
def selectCategory():
    category = session.query(Category).order_by(asc(Category.name))
    category_len = session.query(Category).count()
    if category_len == 0:
        flash("There are no categories to display")

    return render_template('selectCategory.html', categories=category, category_len=category_len)


# Select a item to delete
@app.route('/Item/select/delete', methods=['GET', 'POST'])
def selectItem():
    items_len = session.query(Item).count()
    if items_len == 0:
        flash("There are no items to display")
    items = session.query(Item).join(Category, Item.category_id == Category.id).order_by(Item.date.desc())

    return render_template('selectItem.html', items=items, items_len=items_len)


# Delete a item
@app.route('/Item/delete/<int:item_id>', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(id=item_id).one()

    if login_session['user_id'] != itemToDelete.user_id:
        flash("You cannot delete what you did not create.")
        return redirect(url_for('selectItem'))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showHome'))
    else:
        return render_template('deleteItem.html', item=itemToDelete)

# Delete a Category


@app.route('/Category/delete/<int:category_id>', methods=['GET', 'POST'])
def deleteCategory(category_id):
    categoryToDelete = session.query(
        Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if categoryToDelete.user_id != login_session['user_id']:
        flash("You cannot delete what you did not create.")
        return redirect(url_for('selectCategory'))
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('selectCategory'))
    else:
        return render_template('deleteCategory.html', category=categoryToDelete)

# Disconnect


@app.route('/disconnect')
def disconnect():
    if 'username' in login_session:

        del login_session['username']
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']
        flash("You have successfully been logged out.")
        return redirect(url_for('showHome'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showHome'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
