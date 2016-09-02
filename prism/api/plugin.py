import os

import prism

# Dependency: (binary/library, name)
# 	After load: (binary/library, name, is satisfied)
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
			self._settings = prism.config.Settings(self)
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
	def name_display(self):
		if self.display_name:
			return self.display_name
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
