import prism, settings
flask_app = prism.get().app()

from flask import request, redirect, url_for, render_template, g
from flask_login import current_user

import helpers

@flask_app.template_filter()
def convert_bytes(s):
	return helpers.convert_bytes(s, True)

flask_app.jinja_env.globals["next_color"] = helpers.next_color

import os, jinja2
def include_static(name):
	directory = flask_app.static_folder
	desired_file = os.path.join(directory, name)
	with open(desired_file) as f:
		return jinja2.Markup(f.read())
flask_app.jinja_env.globals["include_static"] = include_static

def has_plugin(id):
	mngr = prism.get_plugin_manager()
	return id in mngr.get_plugins() and mngr.get_plugin(id).active
flask_app.jinja_env.globals["has_plugin"] = has_plugin

import time
@flask_app.template_filter()
def ctime(s):
	return time.ctime(s)

from datetime import datetime

@flask_app.template_filter()
def timesince(dt, past_="ago", future_="from now", default="just now"):
	if isinstance(dt, int) or isinstance(dt, float):
		dt = datetime.strptime(ctime(dt), '%a %b %d %H:%M:%S %Y')
	
	now = datetime.utcnow()
	if now > dt:
		diff = now - dt
		dt_is_past = True
	else:
		diff = dt - now
		dt_is_past = False
	
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
		if period >= 1:
			return "%d %s %s" % (period, singular if period == 1 else plural, past_ if dt_is_past else future_)

	return default

@flask_app.context_processor
def inject_things():
	from flask_menu import current_menu
	
	title = None
	
	checked_menu = current_menu.active_item
	if checked_menu != None:
		while(checked_menu.has_active_child()):
			for child in checked_menu.children:
				if child.active:
					checked_menu = child
					break
		title = checked_menu.text
	
	if title == 'Menu item not initialised':
		title = None
	
	return dict(title=title)

@flask_app.before_request
def before_request():
	g.user = current_user

@flask_app.before_request
def check_valid_login():
	login_valid = prism.get().logged_in()
	
	if (request.endpoint and 
		not request.endpoint.startswith('static') and 
		not login_valid and 
		not getattr(flask_app.view_functions[request.endpoint], 'is_public', False)):
		return redirect(url_for('login'))

@flask_app.errorhandler(404)
def page_not_found(e):
	return render_template('other/404.html'), 404

@flask_app.errorhandler(500)
def internal_server_error(e):
	return render_template('other/500.html'), 500