import os

import settings

# Dependency: (binary/library, name)
# 	After load: (binary/library, name, is satisfied)
class BasePlugin(object):
	def __init__(self, plugin_id, name, version, **kwargs):
		self.plugin_id = plugin_id
		self.name = name
		self._version = version
		self.description = ''
		self.author = ''
		self.homepage = ''
		self.dependencies = [ ]

		self.icon = 'circle-o'
		self.order = 999

		self.config = PluginConfig(settings.CONFIG_FOLDER_PLUGINS, '%s.json' % plugin_id)

		for k in kwargs:
			setattr(self, k, kwargs[k])

		self.version = None
		for i in version:
			if isinstance(i, int):
				if self.version == None:
					self.version = str(i)
				else:
					self.version += '.' + str(i)
			else:
				self.version += '-' + i

	# Called when the plugin is enabled.
	def init(self, prism):
		pass

class PluginConfig(object):
	def __init__(self, folder, file):
		self._path = os.path.join(folder, file)

		self.reload()

	def reload(self):
		self.__dict__.update(settings.load_config(self._path))

	def save(self):
		config = dict([ (k, v) for k, v in self.__dict__.items() if not k.startswith('_') ])
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
