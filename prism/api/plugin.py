import os

import prism

# Dependency: (binary/library, name)
# 	 After load: (binary/library, name, is satisfied)
class BasePlugin(object):
	def __init__(self, **kwargs):
		self._config = None
		self._locale = None
		self._module = None

		self._settings = None

		for k in kwargs:
			setattr(self, k, kwargs[k])

	@property
	def config(self):
		if self._config is None:
			self._config = prism.config.JSONConfig(self, 'config.json')
		return self._config

	@property
	def settings(self):
		if self._settings is None:
			self._settings = Settings(self)
		return self._settings

	@property
	def locale(self):
		if self._locale is None:
			self._locale = prism.config.LocaleConfig(self)
		return self._locale

	@property
	def plugin_id(self):
		return self._info['_id'].split('_', 1)[1]

	@property
	def version(self):
		return self._info['version']

	@property
	def name(self):
		return self._info['name']

	@property
	def description(self):
		return self._info['description']

	@property
	def dependencies(self):
		return self._info['_dependencies']

	@property
	def is_core(self):
		return self._info['_is_core']

	@property
	def is_satisfied(self):
		return self._info['_is_satisfied']

	@property
	def is_enabled(self):
		return self._info['_is_enabled']

	@property
	def plugin_icon(self):
		if 'icon' not in self._info:
			return 'circle-o'
		return self._info['icon']

	@property
	def menu_icon(self):
		if self.icon:
			return icon
		if 'icon' not in self._info:
			return 'circle-o'
		return self._info['icon']

	@property
	def data_folder(self):
		return os.path.join(prism.settings.CONFIG_FOLDER_PLUGINS, self._info['_id'])

	@property
	def plugin_folder(self):
		return os.path.join(prism.settings.PLUGINS_PATH if not self.is_core else prism.settings.CORE_PLUGINS_PATH,
								self._info['_id'])

	# Called when the plugin is enabled.
	def init(self, prism_state):
		pass

class Settings(object):
	""" Used by plugins to allow user settings """
	def __init__(self, plugin):
		self.options = {}

		plugin.config['settings'] = {}
		self.plugin_config = plugin.config

	def add(self, key, default, options={}):
		if 'type' not in options:
			if isinstance(default, bool):
				options['type'] = 'bool'
		self.options[key] = {'value': default, 'default': default, 'options': options}
		return self

	def __getitem__(self, key):
		if key not in self.plugin_config['settings']:
			return None
		return self.plugin_config['settings'][key]

	def __setitem__(self, key, value):
		self.options[key]['value'] = value
		self.plugin_config['settings'][key] = value
		self.plugin_config.save()

	def __delitem__(self, key):
		del self.plugin_config['settings'][key]

	def __contains__(self, key):
		return key in self.plugin_config['settings']

	def __len__(self):
		return len(self.plugin_config['settings'])

	def __repr__(self):
		return repr(self.options)
