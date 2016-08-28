import os

import prism
import settings


# Dependency: (binary/library, name)
# 	After load: (binary/library, name, is satisfied)
class BasePlugin(object):
	def __init__(self, **kwargs):
		self.display_name = None
		self.icon = None
		self.order = 999

		self._config = None
		self._module = None

		for k in kwargs:
			setattr(self, k, kwargs[k])

	@property
	def config(self):
		if self._config is None:
			self._config = PluginConfig(settings.CONFIG_FOLDER_PLUGINS, '%s.json' % self.plugin_id)
		return self._config

	@property
	def plugin_id(self):
		return self._info['_id']

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

	# Called when the plugin is enabled.
	def init(self, prism_state):
		pass

class PluginConfig(object):
	def __init__(self, folder, file):
		self._path = os.path.join(folder, file)

		self.reload()

	def reload(self):
		self.__dict__.update(settings.load_config(self._path))

	def save(self):
		config = dict([(k, v) for k, v in self.__dict__.items() if not k.startswith('_')])
		settings.save_config(self._path, config)

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value
		self.save()

	def __delitem__(self, key):
		del self.__dict__[key]

	def __contains__(self, key):
		return key in self.__dict__

	def __len__(self):
		return len(self.__dict__)

	def __repr__(self):
		return repr(self.__dict__)

	def __call__(self, key, default=None):
		if key in self:
			return self[key]
		self[key] = default
		return default
