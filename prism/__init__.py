# If you know of a better way to handle this, be my guest.
import builtins
import base64
import inspect
import json
import os
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

				if 'library' in plugin_info['dependencies']:
					for depend_name in plugin_info['dependencies']['library']:
						installed = True
						if not installed:
							plugin_info['_is_satisfied'] = False
						plugin_info['_dependencies'].append(('library', depend_name, installed))

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

		has_menus = False

		# Go through each of the module's views and add them to flask
		for view_class in plugin._module_views:
			view = view_class()

			blueprint_name = plugin._endpoint

			if view.endpoint != '/':
				blueprint_name += view.endpoint.replace('/', '.')

			# Create the blueprint in flask
			view._blueprint = Blueprint(blueprint_name,
										plugin.plugin_id,
										template_folder='templates')

			if hasattr(view, 'menu'):
				has_menus = True
				with flask_app().app_context():
					item = current_menu.submenu(blueprint_name)
					item.register(blueprint_name + '.index',
									view.menu['title'],
									view.menu['order'],
									icon=view.menu['icon'])

			for func_name in dir(view):
				# Ignore any non-user-defined methods
				if func_name.startswith('_'):
					continue

				# Get the method's attributes
				func = getattr(view, func_name)

				# We don't want variables. Only methods.
				if not hasattr(func, '__call__'):
					continue

				# If they have their own functions that shouldn't be endpoints
				if hasattr(func, 'ignore') and func.ignore:
					continue

				endpoint_id = func_name
				view_func_wrapper = self.func_wrapper(plugin.plugin_id, func)

				fallback_endpoint = self.get_http_endpoint(func)
				fallback_http_methods = self.get_http_methods(func)
				fallback_defaults = self.get_defaults(func)

				func_routes = list()
				if not hasattr(func, 'routes'):
					func_routes.append({
											'endpoint': fallback_endpoint,
											'http_methods': fallback_http_methods,
											'defaults': fallback_defaults
										})
				else:
					func_routes = func.routes

				if hasattr(func, 'menu'):
					has_menus = True
					with flask_app().app_context():
						item = current_menu.submenu(blueprint_name + '.' + endpoint_id)
						item.register(blueprint_name + '.' + endpoint_id,
										func.menu['title'],
										func.menu['order'],
										icon=func.menu['icon'])

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

					view._blueprint.add_url_rule(route['endpoint'],
													endpoint=endpoint_id,
													methods=route['http_methods'],
													view_func=view_func_wrapper,
													defaults=route['defaults'])

			flask_app().register_blueprint(view._blueprint, url_prefix='/' +
																blueprint_name.replace('.', '/'))

		if has_menus:
			with flask_app().app_context():
				item = current_menu.submenu(plugin._endpoint)
				item.register(plugin._endpoint + '.index',
								plugin.name_display,
								plugin.order,
								icon=plugin.menu_icon)

		paaf()

	def func_wrapper(self, plugin_id, func):
		""" Wraps the route return function. This allows us
		to do fun things with the return value :D """
		def func_wrapper(*args, **kwargs):
			flask.g.current_plugin = plugin_id

			if flask.request.method != 'GET':
				obj = func(flask.request, *args, **kwargs)
			else:
				obj = func(*args, **kwargs)

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
						return flask.redirect(flask.url_for('core.error', error_json=error_json))
			elif isinstance(obj, str):
				if obj.endswith('.html'):
					return flask.render_template(obj)
				elif get_url_for(obj) is not None:
					return flask.redirect(get_url_for(obj))
			elif isinstance(obj, dict):
				return json.dumps(obj)
			return obj
		func_wrapper.__name__ = func.__name__
		return func_wrapper

	def get_defaults(self, func):
		""" Returns the default values for the route """
		defaults = {}
		if hasattr(func, 'defaults'):
			defaults = func.defaults
		elif func.__defaults__ is not None:
			defaults = self.get_default_args(func)
		return defaults

	def get_default_args(self, func):
		""" Returns a dictionary of arg_name: default_values
		for the input function """
		args, varargs, keywords, defaults = inspect.getargspec(func)
		return dict(zip(args[-len(defaults):], defaults))

	def get_http_methods(self, func):
		""" Returns the HTTP methods for the route """
		http_methods = ['GET']
		# If the http methods have been specified in the @route decorator
		if hasattr(func, 'http_methods'):
			http_methods = func.http_methods
		# If the function is called an http method
		elif func.__name__ in ['get', 'post', 'put', 'delete']:
			http_methods = [func.__name__.upper()]
		return http_methods

	def get_http_endpoint(self, func):
		""" Returns the URL endpoint that the route uses for access """
		endpoint_http = '/' + func.__name__
		# If the function is named index
		if endpoint_http == '/index':
			endpoint_http = '/'
		# If an endpoint has been specified in the @route decorator
		elif hasattr(func, 'endpoint'):
			endpoint_http = func.endpoint
		elif func.__name__ in ['get', 'post', 'put', 'delete']:
			endpoint_http = '/'
		return endpoint_http

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

def is_package_installed(id):
	""" Returns true of the linux system has a
	binary installed under the name "id" """
	output = os_command('rpm -qa | grep %s' % id,
						'dpkg -list | grep %s' % id,
						'pkg_info | grep %s' % id)
	return (len(output) > 0)

def os_command(redhat, debian, bsd):
	""" Runs a command based on the OS currently in use """
	os = get_general_os()
	if os == 'redhat':
		return subprocess.Popen(redhat, shell=True, stdout=PIPE).stdout.read()
	elif os == 'debian':
		return subprocess.Popen(debian, shell=True, stdout=PIPE).stdout.read()
	else:
		return subprocess.Popen(bsd, shell=True, stdout=PIPE).stdout.read()

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
