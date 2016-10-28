import os

import flask
import flask_login
from flask_menu import current_menu
import jinja2

import prism
import prism.login
import prism.settings
import prism.helpers

flask_app = prism.flask_app()

@prism.helpers.repeat(0, 60 * 60)
def version_check():
	""" Checks for Prism version updates every hour """
	prism.settings.ping_version()

@flask_app.context_processor
def inject_things():
	""" Adds the site title, the logged in user, and the version
	to each site for use by the base template """

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

	return dict(title=title, me=prism.login.user(), version=prism.__version__, versioning=prism.settings.PRISM_VERSIONING)

@flask_app.route("/site-map")
def site_map():
	links = []
	for rule in flask_app.url_map.iter_rules():
		# Filter out rules we can't navigate to in a browser
		# and rules that require parameters
		defaults = rule.defaults if rule.defaults is not None else ()
		arguments = rule.arguments if rule.arguments is not None else ()

		if "GET" in rule.methods and len(defaults) >= len(arguments):
			url = flask.url_for(rule.endpoint, **(rule.defaults or {}))
			links.append(url + ': ' + rule.endpoint)

	return '<pre>' + str('\n'.join(links)) + '</pre>'

@flask_app.route("/static/plugin/<plugin_id>/<path:static_file>")
def plugin_static(plugin_id, static_file):
	""" Allows plugins to load files from their own static directories """
	plugin = prism.get_plugin(plugin_id)
	if plugin is None:
		return 'Unknown plugin: %s' % plugin_id
	return flask.send_from_directory(plugin.static_folder, static_file)

@flask_app.errorhandler(403)
def permission_denied(e):
	return flask.render_template('other/403.html'), 403

@flask_app.errorhandler(404)
def page_not_found(e):
	return flask.render_template('other/404.html'), 404

@flask_app.errorhandler(500)
def internal_server_error(e):
	return flask.render_template('other/500.html'), 500
