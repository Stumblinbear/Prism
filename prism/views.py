import os

import flask
import flask_login
from flask_menu import current_menu
import jinja2

import prism
import prism.settings
import prism.helpers


flask_app = prism.flask_app()

@flask_app.route("/static/plugin/<plugin_id>/<path:static_file>")
def plugin_static(plugin_id, static_file):
	""" Allows plugins to load files from their own static directories """
	plugin_id = 'prism_' + plugin_id

	plugin = prism.get_plugin(plugin_id)
	if plugin is None:
		return 'Unknown plugin: %s' % plugin_id

	if plugin.is_core:
		static_dir = os.path.join(prism.settings.CORE_PLUGINS_PATH, plugin_id)
	else:
		static_dir = os.path.join(prism.settings.PLUGINS_PATH, plugin_id)

	static_dir = os.path.join(static_dir, 'static')
	return flask.send_from_directory(static_dir, static_file)

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
