from passlib.hash import sha256_crypt
import flask
from flask import Blueprint, request, redirect, url_for, render_template

import flask_login
from wtforms import Form, StringField, PasswordField, validators

import prism


flask_app = prism.flask_app()
db = prism.get().database

login_manager = flask_login.LoginManager()
login_manager.init_app(flask_app)

class User(db.Model):
	__tablename__ = 'user'

	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String, unique=True)
	password = db.Column(db.String)
	name = db.Column(db.String)
	info = db.Column(db.String)
	permissions = db.Column(db.String)

	def __init__(self, username, password, name, info, permissions):
		self.username = username
		self.password = password
		self.name = name
		self.info = info
		self.permissions = permissions

	def get_id(self):
		return self.user_id

	def has_permission(self, permission):
		if '.' in permission:
			# Temp fix for top level nav
			permission_tmp = permission.split('.', 1)
			if permission_tmp[0] == permission_tmp[1]:
				return True
		return self.permissions == '*' or permission in self.permissions.split(',')

	def add_permission(self, permission):
		if self.permissions != '*':
			permissions = self.permissions.split(',')
			if permission not in permissions:
				permissions.append(permission)
			self.permissions = permissions

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def update(self, username, password, name, info, permissions=''):
		if username:
			self.username = username
		if password:
			self.password = sha256_crypt.encrypt(password)
		if info:
			self.info = info
		if name:
			self.name = name
		self.permissions = permissions
		db.session.commit()

	def __repr__(self):
		return '<User %r>' % self.username

class LoginForm(Form):
	username = StringField('Username', validators=[validators.Required()])
	password = PasswordField('Password', validators=[validators.Required()])

def create_user(username, password, name, info='', permissions=[]):
	if not username or not password or not name:
		flask.flash('Unable to create new user.', 'error')
		return
	if prism.login.User.query.filter_by(username=username).first() is not None:
		flask.flash('A user with that username already exists.', 'error')
		return
	db.session.add(User(username, sha256_crypt.encrypt(password), name, info, ','.join(permissions)))
	db.session.commit()

def user():
	""" Returns the user object if they're logged in, otherwise None """
	from flask import g
	if hasattr(g, 'user'):
		return g.user
	return None

def is_logged_in():
	""" Returns true if the user is logged in """
	from flask import g
	if hasattr(g, 'user'):
		return g.user is not None and g.user.is_authenticated
	return False

@flask_app.route("/", methods=['GET', 'POST'])
@prism.public_endpoint
def login():
	if is_logged_in():
		return redirect(url_for('dashboard.DashboardView'))

	form = LoginForm(request.form)
	if request.method == 'POST' and form.validate():
		user = User.query.filter_by(username=form.username.data).first()
		if user:
			if sha256_crypt.verify(form.password.data, user.password):
				flask_login.login_user(user, remember=True)
				return redirect(url_for('dashboard.DashboardView'))
		flask.flash('Sorry, that username/password combination was incorrect.')
	return render_template('other/login.html', title='Login', form=form)

@flask_app.before_request
def revalidate_login():
	flask.g.current_plugin = None
	flask.g.user = flask_login.current_user

	if (flask.request.endpoint and
		not flask.request.endpoint.startswith('static') and
		not getattr(flask_app.view_functions[flask.request.endpoint] if flask.request.endpoint in flask_app.view_functions else None, 'is_public', False) and
		not is_logged_in()):
		return flask.redirect(flask.url_for('login'))

@flask_app.route('/logout')
def logout():
	flask_login.logout_user()
	return flask.redirect(flask.url_for('login'))

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

@login_manager.unauthorized_handler
def unauthorized_handler():
	""" When an unauthorized user attempts to go to a user-only page,
	send them back to the login page """
	return redirect(url_for('login.login'))
