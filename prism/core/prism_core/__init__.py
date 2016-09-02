from prism.api.plugin import BasePlugin

from .views import *


class CorePlugin(BasePlugin):
	def init(self, prism_state):
		self.settings.add('terminal', True)
