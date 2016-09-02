import flask
import flask_login
from flask_menu import current_menu

import prism
import prism.settings
import prism.helpers


flask_app = prism.flask_app()

def has_no_empty_params(rule):
	defaults = rule.defaults if rule.defaults is not None else ()
	arguments = rule.arguments if rule.arguments is not None else ()
	return len(defaults) >= len(arguments)

@flask_app.route("/site-map")
def site_map():
	links = []
	for rule in flask_app.url_map.iter_rules():
		# Filter out rules we can't navigate to in a browser
		# and rules that require parameters
		if "GET" in rule.methods and has_no_empty_params(rule):
			url = flask.url_for(rule.endpoint, **(rule.defaults or {}))
			links.append(url + ': ' + rule.endpoint)

	return '<pre>' + str('\n'.join(links)) + '</pre>'

@flask_app.context_processor
def inject_things():
	title = None

	checked_menu = current_menu.active_item
	if checked_menu is not None:
		while(checked_menu.has_active_child()):
			for child in checked_menu.children:
				if child.active:
					checked_menu = child
					break
		title = checked_menu.text

	if title == 'Menu item not initialised':
		title = None

	return dict(title=title, version=prism.__version__)

@flask_app.before_request
def before_request():
	flask.g.current_plugin = None
	flask.g.user = flask_login.current_user

	login_valid = prism.get().is_logged_in

	if (flask.request.endpoint and
		not flask.request.endpoint.startswith('static') and
		not login_valid and
		not getattr(flask_app.view_functions[flask.request.endpoint], 'is_public', False)):
		return flask.redirect(flask.url_for('login'))

@flask_app.errorhandler(404)
def page_not_found(e):
	return flask.render_template('other/404.html'), 404

@flask_app.errorhandler(500)
def internal_server_error(e):
	return flask.render_template('other/500.html'), 500
