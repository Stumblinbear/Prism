# If you know of a better way to handle this, be my guest.
import builtins, subprocess, inspect, os, sys, re, platform

import subprocess
from subprocess import PIPE

def restart():
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
	return subprocess.call(cmd, shell=True)

def init(flask_app, config):
	builtins.prism_state = Prism(flask_app, config)

def get():
	return builtins.prism_state

def get_plugin_manager():
	return builtins.prism_state.plugin_manager

def get_plugin(id):
	return builtins.prism_state.plugin_manager.get_plugin(id)

class Prism:
	def __init__(self, flask_app, config):
		self.flask_app = flask_app
		self.config = config
		
		self.plugin_manager = PrismPluginManager(config)
	
	# Returns the Flask application instance
	def app(self):
		return self.flask_app
	
	# Returns the Prism plugin manager
	def get_plugin_manager(self):
		return self.plugin_manager
	
	#User functions
	def get_user(self):
		from flask import g
		if hasattr(g, 'user'):
			return g.user
		return None
	
	def logged_in(self):
		from flask import g
		if hasattr(g, 'user'):
			return g.user is not None and g.user.is_authenticated
		return False
	
	# Returns true if login was successful
	def login(self, username, password):
		return self.config['username'] == username and crypt_verify(password, self.config['password'])
	
	# Log the user out
	def logout(self):
		import flask_login
		flask_login.logout_user()
		
		from flask import g, redirect, url_for
		g.user = None
		
		return redirect(url_for('login'))

class PrismPlugin:
	def __init__(self, id, active=True, info=None):
		self.id = id
		self.active = active
		self.info = info
		
	def init(self):
		if self.active:
			from flask import Blueprint
			self.blueprint = Blueprint(self.id, inspect.getmodule(inspect.stack()[1][0]).__name__, template_folder='templates')
	
	def bp(self):
		if not self.active or not self.blueprint:
			return None
		if not hasattr(self, 'blueprint'):
			raise Exception('%s has not been initialized.' % self.id)
		return self.blueprint
	
	def route(self, rule, text=None,
					nav_path=None,
					icon=None,
					order=99,
					hidden=False,
					ignore=False,
					**kwargs):
		if not self.active:
			return None
		
		if nav_path == None and text != None:
			nav_path = '.%s' % text.lower().replace(' ', '')
		
		def decorator(f):
			# Register with Flask
			self.bp().add_url_rule(rule, kwargs.pop("endpoint", f.__name__), f, **kwargs)
			
			if ignore:
				return f
			
			# Register with Flask Menu
			@self.blueprint.before_app_first_request
			def _register_menu_item():
				from flask_menu import current_menu
				item = current_menu.submenu(str(nav_path))
				item.register(
					self.bp().name + '.' + f.__name__,
					text,
					order,
					endpoint_arguments_constructor=None,
					dynamic_list_constructor=None,
					active_when=None,
					visible_when=None,
					expected_args=inspect.getargspec(f).args,
					icon=icon,
					hidden=hidden)
			
			return f
		return decorator

class PrismPluginManager:
	def __init__(self, config):
		self.plugins = []
		self.enabled = config['enabled']
	
	def get_plugin(self, id):
		for plugin in self.plugins:
			if plugin.id == id:
				return plugin
		return None
	
	def set_plugin(self, id, plugin):
		for i in range(0, len(self.plugins)):
			if self.plugins[i]['id'] == id:
				self.plugins[i] = plugin
		return None
	
	# Returns a list of all plugins
	def get_plugins(self):
		return self.plugins
	
	# Plugins can be structured in one of two ways.
	# 1:
	# plugin_<id>
	#    |----- __init__.py
	# 2:
	# plugin_<id>
	#    |----- plugin_<id>: Imported. Allows packaging libraries.
	#          |----- __init__.py
	def load_plugins(self, path):
		import json
		
		# Append the plugins directory
		sys.path.append(path)
		
		self.plugins = list()
		
		output('Searching')
		for plugin_id in os.listdir(path):
			base_folder = os.path.join(path, plugin_id)
			if not os.path.isfile(base_folder):
				# If folder is a prism plugin
				regexp_result = re.search("^prism_(.+?)$", plugin_id)
				if regexp_result:
					plugin_path = os.path.join(base_folder, plugin_id)
					plugin_add = None
					
					# Check if the .py file is in the base folder
					if os.path.exists(os.path.join(base_folder, '__init__.py')):
						plugin_add = { 'plugin_name': plugin_id, 'id': regexp_result.group(1), 'info': os.path.join(base_folder, 'plugin.json') }
						
					# If not, check if the base folder has a folder named
					# the same as the base folder
					elif os.path.exists(plugin_path) and os.path.exists(os.path.join(plugin_path, '__init__.py')):
						
						sys.path.append(base_folder)
						plugin_add = { 'plugin_name': plugin_id, 'id': regexp_result.group(1), 'info': os.path.join(plugin_path, 'plugin.json') }
						
					else:
						output('Invalid plugin. Offender: %s' % plugin_id)
					
					if plugin_add != None:
						plugin_add['info'] = json.loads(open(plugin_add['info']).read())
						plugin_add['info']['enabled'] = (plugin_add['id'] in self.enabled)
						self.plugins.append(plugin_add)
					
				else:
					output('Unknown folder in plugins directory. Offender: %s' % plugin_id)
		
		poof()
		output('Found %s' % len(self.plugins))
		paaf()
		
		output('Sorting')
		poof()
		plugins_sorted = []
		
		# Here's where I should sort plugins so required plugins show first and plugins with dependencies are in the correct order
		while self.plugins:
			remaining_plugins = []
			emitted = False
			
			for plugin in self.plugins:
				# Add required plugins. This should only be "dashboard" but whatever.
				if 'required' in plugin['info'] and plugin['info']['required']:
					plugin['info']['enabled'] = True
					plugins_sorted.insert(0, plugin)
					emitted = True
				elif not 'dependencies' in plugin['info']:
					plugins_sorted.append(plugin)
				else:
					settled = False
					
					depends = plugin['info']['dependencies']
					if 'plugin' in depends:
						depends_sorted = 0
						for depend in depends['plugin']:
							for p in plugins_sorted:
								if p['id'] == depend:
									depends_sorted += 1
						
						# If all dependencies have been sorted
						if len(depends['plugin']) == depends_sorted:
							settled = True
						else:
							settled = False
					else:
						settled = True
					
					# If dependencies are sorted, append it to the sorted list. If not, add it for further sorting.
					if settled:
						plugins_sorted.append(plugin)
						emitted = True
					else:
						remaining_plugins.append(plugin)
			
			if not emitted:
				for plugin in remaining_plugins:
					plugins_sorted.append(plugin)
				break
			
			self.plugins = remaining_plugins
		
		self.plugins = plugins_sorted
		paaf()
		
		
		loadable = 0
		
		output('Settling dependencies')
		poof()
		# Make sure application binaries and other dependencies are loaded
		for i in range(0, len(self.plugins)):
			satisfied = True
			
			# If any dependencies are set
			if 'dependencies' in self.plugins[i]['info']:
				depends = self.plugins[i]['info']['dependencies']
				
				self.plugins[i]['info']['dependencies'] = []
				
				# Check if packages in the linux system are installed
				if 'package' in depends:
					for package in depends['package']:
						settled = is_package_installed(package)
						if not settled:
							satisfied = False
						self.plugins[i]['info']['dependencies'].append(('package', package, settled))
				
				# Check if prism plugins are activated
				if 'plugin' in depends:
					for depend in depends['plugin']:
						settled = False
						for plugin in self.plugins:
							if plugin['id'] == depend:
								if plugin['info']['enabled'] and plugin['info']['dependencies_satisfied']:
									settled = True
								break
						
						if not settled:
							satisfied = False
						
						self.plugins[i]['info']['dependencies'].append(('plugin', depend, settled))
			
			self.plugins[i]['info']['dependencies_satisfied'] = satisfied
			loadable = loadable + 1
		paaf()
		
		poof()
		output('%s plugins ready for load' % loadable)
		paaf()
		
		output('Importing')
		
		poof()
		for i in range(0, len(self.plugins)):
			plugin = self.plugins[i]
			if not self.plugins[i]['info']['enabled'] or not plugin['info']['dependencies_satisfied']:
				self.plugins[i] = PrismPlugin(plugin['id'], info=plugin['info'], active=False)
				continue
			
			self.plugins[i] = PrismPlugin(plugin['id'], info=plugin['info'])
			
			output(plugin['id'])
			__import__(plugin['plugin_name'], globals(), locals())
		paaf()
	
	def register_blueprints(self, flask_app):
		poof()
		for plugin in self.plugins:
			if not plugin.active:
				continue
			output(plugin.id)
			flask_app.register_blueprint(plugin.bp())
		paaf()

# Utility functions
poofs = 0
def poof():
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
	import random, string
	return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def is_package_installed(id):
	output = os_command('rpm -qa | grep %s' % id, 'dpkg -list | grep %s' % id, 'pkg_info | grep %s' % id)
	return (len(output) > 0)

def os_command(redhat, debian, bsd):
	os = get_general_os()
	if os == 'redhat':
		return subprocess.Popen(redhat, shell=True, stdout=PIPE).stdout.read()
	elif os == 'debian':
		return subprocess.Popen(debian, shell=True, stdout=PIPE).stdout.read()
	else:
		return subprocess.Popen(bsd, shell=True, stdout=PIPE).stdout.read()

# Returns if the OS is a Debian, Red Hat, or BSD derivative
def get_general_os():
	if any(word in platform.platform() for word in ("redhat", "centos", "fedora")):
		return 'redhat'
	elif any(word in platform.platform() for word in ("freebsd", "openbsd")):
		return 'bsd'
	else:
		return 'debian'

# Wow. This is so perfect. /s
def is_crypted(string):
	return len(string) == 77

# Used for password encrypting and the like
def crypt_string(string):
	from passlib.hash import sha256_crypt
	return sha256_crypt.encrypt(string)

# Verify a string and hash
def crypt_verify(string, hash):
	from passlib.hash import sha256_crypt
	return sha256_crypt.verify(string, hash)