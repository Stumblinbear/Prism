import flask
from flask import Blueprint, request, redirect, url_for, render_template

import flask_login
from wtforms import Form, StringField, PasswordField, validators

import prism


flask_app = prism.flask_app()

class User(flask_login.UserMixin):
	def __init__(self, data):
		self.id = data['id']

	def is_anonymous(self):
		return False

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

class LoginForm(Form):
	username = StringField('Username', validators=[validators.Required()])
	password = PasswordField('Password', validators=[validators.Required()])

login_manager = flask_login.LoginManager()
login_manager.init_app(flask_app)

@flask_app.route("/", methods=['GET', 'POST'])
@prism.public_endpoint
def login():
	if prism.get().is_logged_in:
		return redirect(url_for('dashboard.home'))

	form = LoginForm(request.form)
	if request.method == 'POST' and form.validate():
		if prism.get().attempt_login(form.username.data, form.password.data):
			user = User({'id': form.username.data})

			flask_login.login_user(user)

			return redirect(url_for('dashboard.home'))
		flask.flash('Sorry, that username/password combination was incorrect.')
	return render_template('other/login.html', title='Login', form=form)

@flask_app.route('/logout')
def logout():
	return prism.get().do_logout()

# Loads the user's data from the database into our user object
@login_manager.user_loader
def load_user(username):
	user = User({'id': username})
	return user

# When an unauthorized user attempts to go to a user-only page, send them back to the login page
@login_manager.unauthorized_handler
def unauthorized_handler():
	return redirect(url_for('login.login'))
