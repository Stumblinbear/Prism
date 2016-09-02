import base64
import inspect
import json
import os
import pip
import platform
import re
import sys
import subprocess

import subprocess
from subprocess import PIPE

import flask
from flask import Blueprint
from flask_menu import current_menu

from prism.config import JSONConfig
import prism.settings
import prism.api.plugin


from prism.version import get_version
__version__ = get_version()

PRISM_STATE = None

def init(flask_app, config):
	global PRISM_STATE
	PRISM_STATE = Prism(flask_app, config)

	import prism.login
	import prism.views

def get():
	return PRISM_STATE

def flask_app():
	return PRISM_STATE.flask_app()

def plugin_manager():
	if PRISM_STATE._plugin_manager is None:
		PRISM_STATE._plugin_manager = PluginManager(PRISM_STATE.config)
		PRISM_STATE.plugin_manager.init()
	return PRISM_STATE.plugin_manager

def get_plugin(id):
	return PRISM_STATE.plugin_manager.get_plugin(id)

class Prism:
	def __init__(self, flask_app, config):
		self._flask_app = flask_app
		self.config = config

		self._plugin_manager = None

	def flask_app(self):
		""" Returns the flask application instance """
		return self._flask_app

	@property
	def plugin_manager(self):
		""" Returns the plugin manager instance """
		return self._plugin_manager

	@property
	# User functions
	def user(self):
		""" Returns the user object if they're logged in, otherwise None """
		from flask import g
		if hasattr(g, 'user'):
			return g.user
		return None

	@property
	def is_logged_in(self):
		""" Returns true if the user is logged in """
		from flask import g
		if hasattr(g, 'user'):
			return g.user is not None and g.user.is_authenticated
		return False

	# Returns true if login was successful
	def attempt_login(self, username, password):
		""" Attempt to log the user in if the username and password are correct """
		if self.config['username'] != username:
			return False
		if not crypt_verify(password, self.config['password']):
			return False
		return True

	# Log the user out
	def do_logout(self):
		""" Log the current user out """
		import flask_login
		flask_login.logout_user()

		from flask import g
		g.user = None

		return flask.redirect(flask.url_for('login'))

class PluginManager:
	def __init__(self, config):
		self.available_plugins = {}
		self.plugins = {}

		# Holds the list of enabled plugins
		self.enabled_plugins = config['enabled_plugins']

	def init(self):
		poof('Searching')
		self._search_plugins(settings.CORE_PLUGINS_PATH, True)
		self._search_plugins(settings.PLUGINS_PATH, False)
		paaf()

		self._sort_dependencies()

		poof('Loading')
		self._load_plugins()
		paaf()

	def get_sorted_plugins(self):
		plugins = list()

		for plugin_id, plugin in self.plugins.items():
			if plugin.is_core:
				plugins.insert(0, plugin)
			else:
				plugins.append(plugin)

		return plugins

	def get_plugin(self, id):
		""" Get a plugin, loaded or not """
		if id in self.plugins:
			return self.plugins[id]
		return None

	def is_enabled(self, id):
		""" Returns true if and only if all the plugin's dependencies are satisfied and
		it's set it enabled """
		return id in self.enabled_plugins

	def is_satisfied(self, id):
		""" Returns true if the plugin's dependencies are satisfied """
		return self.plugins[id].is_satisfied

	def get_classes(self, module, search_class):
		classes = list()
		for name, obj in inspect.getmembers(module):
			if inspect.isclass(obj):
				# Search for the plugin's base class
				if obj != search_class and issubclass(obj, search_class):
					classes.append((name, obj))
		return classes

	def _insert_dummy_plugin(self, plugin_info):
		dummy = prism.api.plugin.BasePlugin()
		dummy._info = plugin_info
		self.plugins[dummy.plugin_id] = dummy

	def _search_plugins(self, path, is_core):
		""" Searches for plugins in a specified folder """
		if is_core:
			output('Finding core plugins')
		else:
			output('Finding additional plugins')

		sys.path.append(path)

		for plugin_id in os.listdir(path):
			base_folder = os.path.join(path, plugin_id)
			if not os.path.isfile(base_folder):
				if not os.path.exists(os.path.join(base_folder, 'plugin.json')):
					output('Plugin does not have a plugin.json file. Offender: %s' % plugin_id)
					continue

				plugin_info = JSONConfig(base_folder, 'plugin.json', auto_save=False)
				plugin_info['_id'] = plugin_id
				plugin_info['_is_core'] = is_core
				plugin_info['_is_satisfied'] = True
				plugin_info['_is_enabled'] = False

				# Make the version readable
				version = None
				for i in plugin_info['version']:
					if isinstance(i, int):
						if version is None:
							version = str(i)
						else:
							version += '.' + str(i)
					else:
						version += '-' + i
				plugin_info['_version'] = plugin_info['version']
				plugin_info['version'] = version

				plugin_info['_dependencies'] = list()

				self.available_plugins[plugin_id] = plugin_info

	def _sort_dependencies(self):
		# These will always be initialized.
		poof('Sorting dependencies')
		installed_packages = pip.get_installed_distributions()
		installed_packages_list = sorted([i.key for i in installed_packages])
		for plugin_id, plugin_info in self.available_plugins.items():
			if not plugin_info['_is_core']:
				if 'dependencies' not in plugin_info:
					continue

				if 'binary' in plugin_info['dependencies']:
					for depend_name in plugin_info['dependencies']['binary']:
						installed = is_package_installed(depend_name)
						if not installed:
							plugin_info['_is_satisfied'] = False
						plugin_info['_dependencies'].append(('binary', depend_name, installed))

				if 'module' in plugin_info['dependencies']:
					for depend_name in plugin_info['dependencies']['module']:
						installed = (depend_name in installed_packages_list)
						if not installed:
							plugin_info['_is_satisfied'] = False
						plugin_info['_dependencies'].append(('module', depend_name, installed))

				if not plugin_info['_is_satisfied']:
					# Create a dummy plugin container
					self._insert_dummy_plugin(plugin_info)
					output('Dependency unsatisfied. Offender: %s' % plugin_id)
		paaf()

	def _load_plugins(self):
		""" Attempts to load every enabled plugin """
		plugins_loaded = list()

		core_plugins = list()
		plugins_additional = list()

		for plugin_id, plugin_info in self.available_plugins.items():
			if plugin_info['_is_core']:
				core_plugins.append(plugin_info)
			elif plugin_info['_is_satisfied']:
				plugins_additional.append(plugin_info)

		# These will always be initialized.
		output('Loading %s core plugin(s)' % len(core_plugins))
		for plugin_info in core_plugins:
			plugin = self._import_plugin(plugin_info)
			if not plugin:
				output('Error: Failed to load core plugin. Offender: %s' % plugin_id)
				continue

			plugins_loaded.append(plugin)
		paaf()

		poof('Loading %s additional plugin(s)' % len(plugins_additional))
		# Start plugins if they're set to be enabled.
		for plugin_info in plugins_additional:
			if not self.is_enabled(plugin_info['_id']):
				self._insert_dummy_plugin(plugin_info)
				continue

			plugin = self._import_plugin(plugin_info)
			if not plugin:
				output('Error: Failed to load additional plugin. Offender: %s' % plugin_id)
				continue

			plugins_loaded.append(plugin)
		paaf()

		poof('Initializing %s plugin(s)' % len(plugins_loaded))
		for plugin in plugins_loaded:
			plugin._info['_is_enabled'] = True
			self._init_plugin(plugin)
		paaf()

	def _import_plugin(self, plugin_info):
		module = __import__(plugin_info['_id'], globals(), locals())

		plugin = None
		module_views = list()

		for name, obj in self.get_classes(module, prism.api.plugin.BasePlugin):
			plugin = obj()
			plugin._module = module
			plugin._info = plugin_info

			plugin._endpoint = plugin.plugin_id
			if plugin._endpoint.startswith('prism_'):
				plugin._endpoint = plugin._endpoint.split('_', 1)[1]

			self.plugins[plugin.plugin_id] = plugin

		for name, obj in self.get_classes(module, api.view.BaseView):
			module_views.append(obj)

		if plugin is None:
			output('Error: Invalid plugin in plugins folder. Offender: %s' % plugin_id)
			return False

		plugin._module_views = module_views
		return plugin

	def _init_plugin(self, plugin):
		"""
		Initializes a plugin:
			1. Runs the plugin's init() function.
			2. Saves the config
			3. Loads the plugin's endpoints into flask
		"""
		poof('Starting %s v%s' % (plugin.name, plugin.version))
		plugin.init(PRISM_STATE)
		plugin.config.save()

		if len(plugin._module_views) > 0:
			blueprint_name = plugin._endpoint

			# Create the plugin blueprint in flask
			plugin._blueprint = Blueprint(blueprint_name,
											plugin.plugin_id,
											template_folder='templates')

			# Go through each of the module's views and add them to flask
			for view_class in plugin._module_views:
				view = view_class()

				endpoint_id = '%s' % view_class.__name__

				if view.menu is not None:
					with flask_app().app_context():
						# Generate the parent menu item
						if 'parent' in view.menu:
							if '.' not in view.menu['parent']['id']:
								parts = ('/' + blueprint_name + view.endpoint).split('/')
								flask_app().add_url_rule('/'.join(parts[:-1]),
																endpoint=blueprint_name + view.menu['parent']['id'])
								item = current_menu.submenu(view.menu['parent']['id'])
								item.register(blueprint_name + view.menu['parent']['id'],
												view.menu['parent']['text'],
												view.menu['parent']['order'],
												icon=view.menu['parent']['icon'])
							else:
								item = current_menu.submenu(view.menu['parent']['id'])
								item.register(blueprint_name + '.' + endpoint_id,
												view.menu['parent']['text'],
												view.menu['parent']['order'],
												icon=view.menu['parent']['icon'])
						item = current_menu.submenu(view.menu['id'])
						item.register(blueprint_name + '.' + endpoint_id,
										view.title,
										view.menu['order'],
										icon=view.menu['icon'])
					prism.output('Registered menu item for /%s: %s' % (blueprint_name + view.endpoint, view.menu['id']))

				# Find all methods in the view class
				for func_name in [method for method in dir(view) if callable(getattr(view, method))]:
					if func_name.startswith('_'):
						continue

					if func_name not in ['get', 'post', 'put', 'delete']:
						if not func_name.endswith(('_get', '_post', '_put', '_delete')):
							continue
						else:
							# Set the fallback http method to the extention of the function name
							parts = func_name.split('_')
							if parts[len(parts) - 1] in ('get', 'post', 'put', 'delete'):
								fallback_http_methods = [parts[len(parts) - 1].upper()]
					else:
						# Set the fallback http method to the function name
						fallback_http_methods = [func_name.upper()]

					if func_name == 'get':
						endpoint_id = '%s' % view_class.__name__
					else:
						endpoint_id = '%s:%s' % (view_class.__name__, func_name)

					# Get the method
					func = getattr(view, func_name)
					view_func_wrapper = self.func_wrapper(plugin.plugin_id, func)

					# If the http methods have been specified in the @subroute decorator
					if hasattr(func, 'http_methods'):
						fallback_http_methods = func.http_methods

					fallback_endpoint = '/'
					# If an endpoint has been specified in the @subroute decorator
					if hasattr(func, 'endpoint'):
						fallback_endpoint = func.endpoint

					# Prepare fallback defaults for the page
					if hasattr(func, 'defaults'):
						fallback_defaults = func.defaults
					elif func.__defaults__ is not None:
						args, varargs, keywords, defaults = inspect.getargspec(func)
						fallback_defaults = dict(zip(args[-len(defaults):], defaults))
					else:
						fallback_defaults = {}

					func_routes = list()
					if not hasattr(func, 'routes'):
						func_routes.append({
												'endpoint': fallback_endpoint,
												'http_methods': fallback_http_methods,
												'defaults': fallback_defaults
											})
					else:
						func_routes = func.routes

					# Add a route for the get function with no parameters
					if func_name == 'get':
						plugin._blueprint.add_url_rule(view.endpoint + fallback_endpoint,
														endpoint=endpoint_id,
														methods=fallback_http_methods,
														view_func=view_func_wrapper,
														defaults=fallback_defaults)

					for route in func_routes:
						if 'endpoint' not in route:
							route['endpoint'] = fallback_endpoint
						if 'http_methods' not in route:
							route['http_methods'] = fallback_http_methods
						if 'defaults' not in route:
							route['defaults'] = fallback_defaults.copy()

						# Defaults are odd. They cannot be attached to routes with the key in the url
						# For example: if <id> in in the url rule, it cann't be in defaults.
						pattern = re.compile(r'<(?:.+?(?=:):)?(.+?)>')
						if '<' in route['endpoint'] and len(route['defaults']) > 0:
							for id in re.findall(pattern, route['endpoint']):
								try:
									del route['defaults'][id]
								except:
									pass

						prism.output('Registered page /%s: %s %s' % (blueprint_name + view.endpoint + route['endpoint'], blueprint_name + '.' + endpoint_id, route['http_methods']))

						plugin._blueprint.add_url_rule(view.endpoint + route['endpoint'],
														endpoint=endpoint_id,
														methods=route['http_methods'],
														view_func=view_func_wrapper,
														defaults=route['defaults'])

			flask_app().register_blueprint(plugin._blueprint, url_prefix='/' +
																blueprint_name.replace('.', '/'))

		paaf()

	def func_wrapper(self, plugin_id, func):
		""" Wraps the route return function. This allows us
		to do fun things with the return value :D """
		def func_wrapper(*args, **kwargs):
			flask.g.current_plugin = plugin_id

			obj = func(flask.request, *args, **kwargs)

			# from flask import request, redirect, url_for, render_template
			if isinstance(obj, tuple):
				page_args = {}
				if len(obj) > 1:
					page_args = obj[1]

				if obj[0].endswith('.html'):
					return flask.render_template(obj[0], **page_args)
				elif get_url_for(obj[0]) is not None:
					return flask.redirect(get_url_for(obj[0], **page_args))
				elif len(obj) > 1:
					if obj[0] == 'redirect':
						return flask.redirect(flask.url_for(obj[1]))
					elif obj[0] == 'abort':
						flask.abort(obj[1])
					elif obj[0] == 'error':
						error_json = base64.b64encode(json.dumps(page_args).encode('utf-8'))
						return flask.redirect(flask.url_for('core.ErrorView', error_json=error_json))
			elif isinstance(obj, str):
				if obj.endswith('.html'):
					return flask.render_template(obj)
				elif get_url_for(obj) is not None:
					return flask.redirect(get_url_for(obj))
			elif isinstance(obj, dict):
				return flask.jsonify(obj)
			return repr(obj)
		func_wrapper.__name__ = func.__name__
		return func_wrapper

# Utility functions
def public_endpoint(function):
	""" Use as a decorator to allow a page to
	be accessed without being logged in """
	function.is_public = True
	return function

def get_url_for(url, **args):
	""" Checks if a url endpoint exists """
	try:
		return flask.url_for(url, **args)
	except:
		return None

def restart():
	""" Safely restart prism """
	import psutil
	import logging

	try:
		p = psutil.Process(os.getpid())
		for handler in p.get_open_files() + p.connections():
			os.close(handler.fd)
	except Exception as e:
		logging.error(e)

	python = sys.executable
	os.execl(python, python, *sys.argv)

def command(cmd):
	""" Runs a shell command and returns the output """
	return subprocess.call(cmd, shell=True)

poofs = 0
def poof(str=None):
	if str is not None:
		output('>%s' % str)
	global poofs
	poofs += 1
def paaf():
	global poofs
	poofs -= 1

def output(string):
	prefix = '::> '
	for i in range(0, poofs):
		prefix = prefix + '|'
	print('%s%s' % (prefix, string))

def get_input(string, default=None, allow_empty=True):
	""" Gets input from the user in the shell """
	if default:
		string = string + '[' + default + ']'

	while True:
		user_input = input('::| %s: ' % string)
		if user_input or allow_empty:
			break
	if not user_input:
		return (default, True)
	return (user_input, False)

def generate_random_string(length):
	""" Returns a string of random characters of size "length" """
	import random
	import string
	return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def is_package_installed(pkg):
	""" Returns true of the linux system has a
	binary installed under the name "pkg" """
	output = os_command('rpm -qa | grep %s' % pkg,
						'dpkg -l | grep %s' % pkg,
						'pkg_info | grep %s' % pkg)
	return (len(output) > 0)

def get_os_command(redhat, debian=None, bsd=None):
	if debian is None and bsd is None:
		return redhat

	os = get_general_os()
	if os == 'redhat':
		return redhat
	elif os == 'debian':
		return debian
	else:
		return bsd

def os_command(redhat, debian=None, bsd=None):
	""" Runs a command based on the OS currently in use """
	return subprocess.Popen(get_os_command(redhat, debian, bsd), shell=True, stdout=PIPE).stdout.read()

# Returns if the OS is a Debian, Red Hat, or BSD derivative
def get_general_os():
	""" Gets a simple name of the current linux operating system """
	if any(word in platform.platform() for word in ("redhat", "centos", "fedora")):
		return 'redhat'
	elif any(word in platform.platform() for word in ("freebsd", "openbsd")):
		return 'bsd'
	else:
		return 'debian'

# Wow. This is so perfect. /s
def is_crypted(string):
	return len(string) == 77

def crypt_string(string):
	""" Encrypt a string using SHA256 """
	from passlib.hash import sha256_crypt
	return sha256_crypt.encrypt(string)

def crypt_verify(string, hash):
	""" Verify that a string and an encryped hash are the same """
	from passlib.hash import sha256_crypt
	return sha256_crypt.verify(string, hash)
