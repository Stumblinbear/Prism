# If you know of a better way to handle this, be my guest.
import builtins
import inspect
import json
import os
import platform
import re
import sys
import subprocess

import subprocess
from subprocess import PIPE

from flask import Blueprint, request, render_template, url_for, redirect, abort
from flask_menu import current_menu

import api
import settings

PRISM_STATE = None

def init(flask_app, config):
	global PRISM_STATE
	PRISM_STATE = Prism(flask_app, config)

def get():
	return PRISM_STATE

def flask():
	return PRISM_STATE.flask()

def plugin_manager():
	if PRISM_STATE.plugin_manager == None:
		PRISM_STATE.plugin_manager = PluginManager(PRISM_STATE.config)
	return PRISM_STATE.plugin_manager

def get_plugin(id):
	return PRISM_STATE.plugin_manager.get_plugin(id)

class Prism:
	def __init__(self, flask_app, config):
		self.flask_app = flask_app
		self.config = config

		self.plugin_manager = None

	def flask(self):
		""" Returns the flask application instance """
		return self.flask_app

	#User functions
	def user(self):
		""" Returns the user object if they're logged in, otherwise None """
		from flask import g
		if hasattr(g, 'user'):
			return g.user
		return None

	def logged_in(self):
		""" Returns true if the user is logged in """
		from flask import g
		if hasattr(g, 'user'):
			return g.user is not None and g.user.is_authenticated
		return False

	# Returns true if login was successful
	def login(self, username, password):
		""" Attempt to log the user in if the username and password are correct """
		return self.config['username'] == username and crypt_verify(password, self.config['password'])

	# Log the user out
	def logout(self):
		""" Log the current user out """
		import flask_login
		flask_login.logout_user()

		from flask import g
		g.user = None

		return redirect(url_for('login'))

class PluginManager:
	def __init__(self, config):
		self.plugins = { }

		# Holds the list of core plugin ids
		self.core_plugins = list()
		# Holds the list of plugins with unsatisfied dependencies
		self.unsatisfied_plugins = list()
		# Holds the list of enabled plugins
		self.enabled_plugins = config['enabled_plugins']

		poof('Searching')
		self._search_plugins(settings.CORE_PLUGINS_PATH, True)
		self._search_plugins(settings.PLUGINS_PATH, False)
		paaf()

		poof('Loading')
		self._load_plugins()
		paaf()

	def get_plugin(self, id):
		""" Get a plugin, loaded or not """
		if id in self.plugins:
			return self.plugins[id]
		return None

	def is_satisfied(self, id):
		""" Returns true if the plugin's dependencies are satisfied """
		return id not in self.unsatisfied_plugins

	def is_enabled(self, id):
		""" Returns true if and only if all the plugin's dependencies are satisfied and
		it's set it enabled """
		return self.is_satisfied(id) and id in self.enabled_plugins

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
				module = __import__(plugin_id, globals(), locals())

				plugin = None
				module_views = list()

				for name, obj in inspect.getmembers(module):
					if inspect.isclass(obj):
						# Search for the plugin's base class
						if obj != api.BasePlugin and issubclass(obj, api.BasePlugin):
							plugin = obj()
							plugin.module = module
							plugin._is_core = False
							plugin._is_satisfied = True
							plugin._is_enabled = False

							if plugin_id != plugin.plugin_id:
								output('Error: Plugin ID <-> module ID mismatch. Offender: %s != %s' % (plugin.plugin_id, plugin_id))
								continue

							plugin._endpoint = plugin_id
							if plugin._endpoint.startswith('prism_'):
								plugin._endpoint = plugin._endpoint.split('_', 2)[1]

							self.plugins[plugin.plugin_id] = plugin

							if is_core:
								self.core_plugins.append(plugin.plugin_id)

						# Add any views to the view list for immediate parsing
						elif obj != api.view.BaseView and issubclass(obj, api.view.BaseView):
							module_views.append(obj)

				if plugin == None:
					output('Error: Invalid plugin in plugins folder. Offender: %s' % plugin_id)
					continue

				plugin._module_views = module_views


	def _load_plugins(self):
		""" Attempts to load every available plugin """
		plugins_additional = list()

		# These will always be initialized.
		output('Initializing %s core plugin(s)' % len(self.core_plugins))
		for plugin_id, plugin in self.plugins.items():
			if plugin_id in self.core_plugins:
				plugin._is_core = True
				plugin._is_enabled = True
				self._init_plugin(plugin)
			else:
				plugin._is_core = False
				plugins_additional.append(plugin_id)
		paaf()

		if len(plugins_additional) == 0:
			return

		poof('Initializing %s additional plugin(s)' % len(plugins_additional))
		poof('Settling dependencies')
		# Make sure application binaries and other dependencies are loaded
		for plugin_id in plugins_additional:
			plugin = self.get_plugin(plugin_id)

			new_dependencies = list()

			plugin._is_satisfied = True

			for depends in plugin.dependencies:
				# Check if packages in the linux system are installed
				if depends[0] == 'binary':
					installed = is_package_installed(package)
					if not installed:
						plugin._is_satisfied = False
					new_dependencies.append((depends[0], depends[1], installed))

				# Check if a python library is installed
				elif depends[0] == 'library':
					installed = True
					if not installed:
						plugin._is_satisfied = False
					new_dependencies.append((depends[0], depends[1], installed))
				else:
					output('Unknown dependency type: %s' % depends[0])

			if not plugin._is_satisfied:
				unsatisfied_plugins.append(plugin_id)
				output('Dependency unsatisfied. Offender: %s' % plugin_id)

			plugin.dependencies = new_dependencies
		paaf()

		# Start plugins if they're set to be enabled.
		for plugin_id in plugins_additional:
			if not self.is_enabled(plugin_id):
				continue
			self._init_plugin(self.get_plugin(plugin_id))
		paaf()

	def _init_plugin(self, plugin):
		"""
		Initializes a plugin:
		   1. Runs the plugin's init() function.
		   2. Saves the config
		   3. Loads the plugin's endpoints into flask
		"""
		plugin._is_enabled = True
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
			view._blueprint = Blueprint(blueprint_name, plugin.plugin_id, template_folder='templates')

			if hasattr(view, 'menu'):
				has_menus = True
				with flask().app_context():
					item = current_menu.submenu(blueprint_name)
					item.register(blueprint_name + '.index', view.menu['title'], view.menu['order'], icon=view.menu['icon'])

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
				view_func_wrapper = self.func_wrapper(func)

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
					with flask().app_context():
						item = current_menu.submenu(blueprint_name + '.' + endpoint_id)
						item.register(blueprint_name + '.' + endpoint_id, func.menu['title'], func.menu['order'], icon=func.menu['icon'])

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

					output('%s %s%s: %s' % (route['http_methods'], blueprint_name.replace('.', '/'), route['endpoint'], route['defaults']))

					view._blueprint.add_url_rule(route['endpoint'],
												endpoint=endpoint_id,
												methods=route['http_methods'],
												view_func=view_func_wrapper,
												defaults=route['defaults'])

			flask().register_blueprint(view._blueprint, url_prefix='/%s' % blueprint_name.replace('.', '/'))

		if has_menus:
			with flask().app_context():
				item = current_menu.submenu(plugin._endpoint)
				item.register(plugin._endpoint + '.index', plugin.name, plugin.order, icon=plugin.icon)

		paaf()

	def func_wrapper(self, func):
		""" Wraps the route return function. This allows us to do fun things with the return value :D """
		def func_wrapper(*args, **kwargs):
			if request.method != 'GET':
				obj = func(request, *args, **kwargs)
			else:
				obj = func(*args, **kwargs)

			# from flask import request, redirect, url_for, render_template
			if isinstance(obj, tuple):
				page_args = { }
				if len(obj) > 1:
					page_args = obj[1]

				if obj[0].endswith('.html'):
					return render_template(obj[0], **page_args)
				elif get_url_for(obj[0]) != None:
					print(get_url_for(obj[0], **page_args))
					return redirect(get_url_for(obj[0], **page_args))
				elif len(obj) > 1:
					if obj[0] == 'redirect':
						return redirect(url_for(obj[1]))
					elif obj[0] == 'abort':
						abort(obj[1])
			elif isinstance(obj, str):
				if obj.endswith('.html'):
					return render_template(obj)
				elif get_url_for(obj) != None:
					return redirect(get_url_for(obj))
			elif isinstance(obj, dict):
				return json.dumps(obj)
			return obj
		func_wrapper.__name__ = func.__name__
		return func_wrapper

	def get_defaults(self, func):
		""" Returns the default values for the route """
		defaults = { }
		if hasattr(func, 'defaults'):
			defaults = func.defaults
		elif func.__defaults__ != None:
			defaults = self.get_default_args(func)
		return defaults

	def get_default_args(self, func):
		""" Returns a dictionary of arg_name: default_values for the input function """
		args, varargs, keywords, defaults = inspect.getargspec(func)
		return dict(zip(args[-len(defaults):], defaults))

	def get_http_methods(self, func):
		""" Returns the HTTP methods for the route """
		http_methods = [ 'GET' ]
		# If the http methods have been specified in the @route decorator
		if hasattr(func, 'http_methods'):
			http_methods = func.http_methods
		# If the function is called an http method
		elif func.__name__ in [ 'get', 'post', 'put', 'delete' ]:
			http_methods = [ func.__name__.upper() ];
		return http_methods

	def get_http_endpoint(self, func):
		""" Returns the URL endpoint that the route uses for access """
		endpoint_http = '/%s' % func.__name__
		# If the function is named index
		if endpoint_http == '/index':
			endpoint_http = '/'
		# If an endpoint has been specified in the @route decorator
		elif hasattr(func, 'endpoint'):
			endpoint_http = func.endpoint
		elif func.__name__ in [ 'get', 'post', 'put', 'delete' ]:
			endpoint_http = '/'
		return endpoint_http

# Utility functions
def public_endpoint(function):
	""" Use as a decorator to allow a page to be accessed without being logged in """
	function.is_public = True
	return function

def get_url_for(url, **args):
	""" Checks if a url endpoint exists """
	try:
		return url_for(url, **args)
	except:
		return None

def restart():
	""" Safely restart prism """
	import psutil, logging

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
	import random, string
	return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def is_package_installed(id):
	""" Returns true of the linux system has a binary installed under the name "id" """
	output = os_command('rpm -qa | grep %s' % id, 'dpkg -list | grep %s' % id, 'pkg_info | grep %s' % id)
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
